# TODO: verify the Conan v2 migration

import os

from conan import ConanFile, conan_version
from conan.errors import ConanInvalidConfiguration, ConanException
from conan.tools.android import android_abi
from conan.tools.apple import (
    XCRun,
    fix_apple_shared_install_name,
    is_apple_os,
    to_apple_arch,
)
from conan.tools.build import (
    build_jobs,
    can_run,
    check_min_cppstd,
    cross_building,
    default_cppstd,
    stdcpp_library,
    valid_min_cppstd,
)
from conan.tools.cmake import (
    CMake,
    CMakeDeps,
    CMakeToolchain,
    cmake_layout,
)
from conan.tools.env import (
    Environment,
    VirtualBuildEnv,
    VirtualRunEnv,
)
from conan.tools.files import (
    apply_conandata_patches,
    chdir,
    collect_libs,
    copy,
    download,
    export_conandata_patches,
    get,
    load,
    mkdir,
    patch,
    patches,
    rename,
    replace_in_file,
    rm,
    rmdir,
    save,
    symlinks,
    unzip,
)
from conan.tools.gnu import (
    Autotools,
    AutotoolsDeps,
    AutotoolsToolchain,
    PkgConfig,
    PkgConfigDeps,
)
from conan.tools.layout import basic_layout
from conan.tools.meson import MesonToolchain, Meson
from conan.tools.microsoft import (
    MSBuild,
    MSBuildDeps,
    MSBuildToolchain,
    NMakeDeps,
    NMakeToolchain,
    VCVars,
    check_min_vs,
    is_msvc,
    is_msvc_static_runtime,
    msvc_runtime_flag,
    unix_path,
    unix_path_package_info_legacy,
    vs_layout,
)
from conan.tools.microsoft.visual import vs_ide_version
from conan.tools.scm import Version
from conan.tools.system import package_manager
from conan.tools.cmake import (
    CMake,
    CMakeDeps,
    CMakeToolchain,
    cmake_layout,
)
import os

required_conan_version = ">=1.43.0"


class LibCheckConan(ConanFile):
    name = "libcheck"
    description = "A unit testing framework for C"
    topics = ("unit", "testing", "framework", "C")
    license = "LGPL-2.1-or-later"
    homepage = "https://github.com/libcheck/check"
    url = "https://github.com/conan-io/conan-center-index"

    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "with_subunit": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "with_subunit": True,
    }

    generators = "cmake", "cmake_find_package"
    _cmake = None

    @property
    def _build_subfolder(self):
        return "build_subfolder"

    @property
    def _is_msvc(self):
        return str(self.settings.compiler) in ["Visual Studio", "msvc"]

    def export_sources(self):
        self.copy("CMakeLists.txt")
        for patch in self.conan_data.get("patches", {}).get(self.version, []):
            self.copy(patch["patch_file"])

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            del self.options.fPIC
        del self.settings.compiler.libcxx
        del self.settings.compiler.cppstd

    def requirements(self):
        if self.options.with_subunit:
            self.requires("subunit/1.4.0")

    def source(self):
        tools.get(
            **self.conan_data["sources"][self.version], destination=self._source_subfolder, strip_root=True
        )

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["CHECK_ENABLE_TESTS"] = False
        tc.variables["ENABLE_MEMORY_LEAKING_TESTS"] = False
        tc.variables["CHECK_ENABLE_TIMEOUT_TESTS"] = False
        tc.variables["HAVE_SUBUNIT"] = self.options.with_subunit
        self._cmake.configure(build_folder=self._build_subfolder)
        return self._cmake

    def build(self):
        for patch in self.conan_data.get("patches", {}).get(self.version, []):
            tools.patch(**patch)
        cmake = self._configure_cmake()
        cmake.build()

    def package(self):
        self.copy("COPYING.LESSER", src=self._source_subfolder, dst="licenses")
        cmake = self._configure_cmake()
        cmake.install()

        tools.rmdir(os.path.join(self.package_folder, "lib", "cmake"))
        tools.rmdir(os.path.join(self.package_folder, "lib", "pkgconfig"))
        tools.rmdir(os.path.join(self.package_folder, "share"))

    def package_info(self):
        target = "checkShared" if self.options.shared else "check"
        self.cpp_info.set_property("cmake_file_name", "check")
        self.cpp_info.set_property("cmake_target_name", "Check::{}".format(target))
        self.cpp_info.set_property("pkg_config_name", "check")

        # TODO: back to global scope in conan v2 once cmake_find_package_* generators removed
        libsuffix = "Dynamic" if self._is_msvc and self.options.shared else ""
        self.cpp_info.components["liblibcheck"].libs = ["check{}".format(libsuffix)]
        if self.options.with_subunit:
            self.cpp_info.components["liblibcheck"].requires.append("subunit::libsubunit")
        if not self.options.shared:
            if self.settings.os in ["Linux", "FreeBSD"]:
                self.cpp_info.components["liblibcheck"].system_libs = ["m", "pthread", "rt"]

        bin_path = os.path.join(self.package_folder, "bin")
        self.output.info("Appending PATH environment variable: {}".format(bin_path))
        self.env_info.PATH.append(bin_path)

        # TODO: to remove in conan v2 once cmake_find_package_* generators removed
        self.cpp_info.filenames["cmake_find_package"] = "check"
        self.cpp_info.filenames["cmake_find_package_multi"] = "check"
        self.cpp_info.names["cmake_find_package"] = "Check"
        self.cpp_info.names["cmake_find_package_multi"] = "Check"
        self.cpp_info.names["pkg_config"] = "check"
        self.cpp_info.components["liblibcheck"].names["cmake_find_package"] = target
        self.cpp_info.components["liblibcheck"].names["cmake_find_package_multi"] = target
        self.cpp_info.components["liblibcheck"].set_property("cmake_target_name", "Check::{}".format(target))
        self.cpp_info.components["liblibcheck"].set_property("pkg_config_name", "check")
