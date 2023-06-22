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
import os
import shutil
import textwrap
from conan.tools.cmake import (
    CMake,
    CMakeDeps,
    CMakeToolchain,
    cmake_layout,
)

required_conan_version = ">=1.43.0"


class CryptoPPPEMConan(ConanFile):
    name = "cryptopp-pem"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://www.cryptopp.com/wiki/PEM_Pack"
    license = "Unlicense"
    description = "The PEM Pack is a partial implementation of message encryption which allows you to read and write PEM encoded keys and parameters, including encrypted private keys."
    topics = ("cryptopp", "crypto", "cryptographic", "security", "PEM")

    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
    }

    generators = "cmake", "cmake_find_package"
    _cmake = None

    @property
    def _build_subfolder(self):
        return "build_subfolder"

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

    def source(self):
        suffix = "CRYPTOPP_{}".format(self.version.replace(".", "_"))

        # Get sources
        tools.get(
            **self.conan_data["sources"][self.version]["source"],
            strip_root=True,
            destination=self._source_subfolder
        )

        # Get CMakeLists
        tools.get(**self.conan_data["sources"][self.version]["cmake"])
        src_folder = os.path.join(self.source_folder, "cryptopp-cmake-" + suffix)
        dst_folder = os.path.join(self.source_folder, self._source_subfolder)
        shutil.move(os.path.join(src_folder, "CMakeLists.txt"), os.path.join(dst_folder, "CMakeLists.txt"))
        shutil.move(
            os.path.join(src_folder, "cryptopp-config.cmake"),
            os.path.join(dst_folder, "cryptopp-config.cmake"),
        )
        tools.rmdir(src_folder)

        # Get license
        tools.download(
            "https://unlicense.org/UNLICENSE",
            "UNLICENSE",
            sha256="7e12e5df4bae12cb21581ba157ced20e1986a0508dd10d0e8a4ab9a4cf94e85c",
        )

    def _patch_sources(self):
        if self.settings.os == "Android" and "ANDROID_NDK_HOME" in os.environ:
            shutil.copyfile(
                os.path.join(
                    tools.get_env("ANDROID_NDK_HOME"), "sources", "android", "cpufeatures", "cpu-features.h"
                ),
                os.path.join(self._source_subfolder, "cpu-features.h"),
            )
        for patch in self.conan_data.get("patches", {}).get(self.version, []):
            tools.patch(**patch)
        # Honor fPIC option
        tools.replace_in_file(
            os.path.join(self._source_subfolder, "CMakeLists.txt"),
            "SET(CMAKE_POSITION_INDEPENDENT_CODE 1)",
            "",
        )

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["BUILD_STATIC"] = not self.options.shared
        tc.variables["BUILD_SHARED"] = self.options.shared
        tc.variables["BUILD_TESTING"] = False
        tc.variables["BUILD_DOCUMENTATION"] = False
        tc.variables["USE_INTERMEDIATE_OBJECTS_TARGET"] = False
        tc.variables["DISABLE_ASM"] = True
        if self.settings.os == "Android":
            tc.variables["CRYPTOPP_NATIVE_ARCH"] = True
        if (
            self.settings.os == "Macos"
            and self.settings.arch == "armv8"
            and tools.Version(self.version) <= "8.4.0"
        ):
            tc.variables["CMAKE_CXX_FLAGS"] = "-march=armv8-a"
        self._cmake.configure(build_folder=self._build_subfolder)
        return self._cmake

    def requirements(self):
        self.requires("cryptopp/" + self.version)

    def build(self):
        self._patch_sources()
        cmake = self._configure_cmake()
        cmake.build()

    def package(self):
        self.copy(pattern="UNLICENSE", dst="licenses")
        cmake = self._configure_cmake()
        cmake.install()
        tools.rmdir(os.path.join(self.package_folder, "lib", "cmake"))
        # TODO: to remove in conan v2 once cmake_find_package* generators removed
        self._create_cmake_module_alias_targets(
            os.path.join(self.package_folder, self._module_file_rel_path),
            {
                "cryptopp-pem-shared": "cryptopp-pem::cryptopp-pem-shared",
                "cryptopp-pem-static": "cryptopp-pem::cryptopp-pem-static",
            },
        )

    @staticmethod
    def _create_cmake_module_alias_targets(module_file, targets):
        content = ""
        for alias, aliased in targets.items():
            content += textwrap.dedent(
                """\
                if(TARGET {aliased} AND NOT TARGET {alias})
                    add_library({alias} INTERFACE IMPORTED)
                    set_property(TARGET {alias} PROPERTY INTERFACE_LINK_LIBRARIES {aliased})
                endif()
            """.format(
                    alias=alias, aliased=aliased
                )
            )
        tools.save(module_file, content)

    @property
    def _module_file_rel_path(self):
        return os.path.join("lib", "cmake", "conan-official-{}-targets.cmake".format(self.name))

    def package_info(self):
        cmake_target = "cryptopp-pem-shared" if self.options.shared else "cryptopp-pem-static"
        self.cpp_info.set_property("cmake_file_name", "cryptopp-pem")
        self.cpp_info.set_property("cmake_target_name", cmake_target)
        self.cpp_info.set_property("pkg_config_name", "libcryptopp-pem")

        # TODO: back to global scope once cmake_find_package* generators removed
        self.cpp_info.components["libcryptopp-pem"].libs = tools.collect_libs(self)
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.components["libcryptopp-pem"].system_libs = ["pthread", "m"]
        elif self.settings.os == "SunOS":
            self.cpp_info.components["libcryptopp-pem"].system_libs = ["nsl", "socket"]
        elif self.settings.os == "Windows":
            self.cpp_info.components["libcryptopp-pem"].system_libs = ["ws2_32"]

        # TODO: to remove in conan v2 once cmake_find_package* & pkg_config generators removed
        self.cpp_info.names["pkg_config"] = "libcryptopp-pem"
        self.cpp_info.components["libcryptopp-pem"].names["cmake_find_package"] = cmake_target
        self.cpp_info.components["libcryptopp-pem"].names["cmake_find_package_multi"] = cmake_target
        self.cpp_info.components["libcryptopp-pem"].build_modules["cmake_find_package"] = [
            self._module_file_rel_path
        ]
        self.cpp_info.components["libcryptopp-pem"].build_modules["cmake_find_package_multi"] = [
            self._module_file_rel_path
        ]
        self.cpp_info.components["libcryptopp-pem"].set_property("cmake_target_name", cmake_target)
        self.cpp_info.components["libcryptopp-pem"].set_property("pkg_config_name", "libcryptopp-pem")

        self.cpp_info.components["libcryptopp-pem"].requires = ["cryptopp::cryptopp"]
