# TODO: verify the Conan v2 migration

import os
import glob

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


class AcadoConan(ConanFile):
    name = "acado"
    description = "ACADO Toolkit is a software environment and algorithm collection for automatic control and dynamic optimization."
    license = "LGPL-3.0"
    topics = ("control", "optimization", "mpc")
    homepage = "https://github.com/acado/acado"
    url = "https://github.com/conan-io/conan-center-index"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "codegen_only": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "codegen_only": True,
    }

    def export_sources(self):
        copy(self, "cmake/qpoases.cmake", src=self.recipe_folder, dst=self.export_sources_folder)
        export_conandata_patches(self)

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        extracted_dir = glob.glob("acado-*/")[0]
        os.rename(extracted_dir, self.source_folder)

    def generate(self):
        tc = CMakeToolchain(self)

        tc.variables["CMAKE_CXX_STANDARD"] = 11

        tc.variables["ACADO_BUILD_SHARED"] = self.options.shared
        tc.variables["ACADO_BUILD_STATIC"] = not self.options.shared

        tc.variables["ACADO_WITH_EXAMPLES"] = False
        tc.variables["ACADO_WITH_TESTING"] = False
        tc.variables["ACADO_DEVELOPER"] = False
        tc.variables["ACADO_INTERNAL"] = False
        tc.variables["ACADO_BUILD_CGT_ONLY"] = self.options.codegen_only

        # ACADO logs 170.000 lines of warnings, so we disable them
        tc.variables["CMAKE_C_FLAGS"] = "-w"
        tc.variables["CMAKE_CXX_FLAGS"] = "-w"
        tc.generate()

        tc = CMakeDeps(self)
        tc.generate()

    def _patch_sources(self):
        apply_conandata_patches(self)

    def build(self):
        self._patch_sources()
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    @property
    def _qpoases_sources(self):
        return os.path.join("lib", "cmake", "qpoases")

    def package(self):
        copy(self, "LICENSE.txt", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()

        copy(self, "*", src="lib", dst=os.path.join(self.package_folder, "lib"))
        copy(self, "qpoases.cmake", src="cmake", dst=os.path.join(self.package_folder, "lib/cmake"))
        qpoases_sources_from = os.path.join(
            self.package_folder, "share", "acado", "external_packages", "qpoases"
        )
        copy(self, "*", src=qpoases_sources_from, dst=self._qpoases_sources)

        rmdir(self, os.path.join(self.package_folder, "share"))
        rm(self, "*.pdb", self.package_folder, recursive=True)

    def package_info(self):
        acado_template_paths = os.path.join(
            self.package_folder, "include", "acado", "code_generation", "templates"
        )
        self.output.info("Setting ACADO_TEMPLATE_PATHS environment variable: {}".format(acado_template_paths))
        self.env_info.ACADO_TEMPLATE_PATHS = acado_template_paths

        if self.options.shared:
            self.cpp_info.libs = ["acado_toolkit_s", "acado_casadi"]
        else:
            self.cpp_info.libs = ["acado_toolkit", "acado_casadi"]

        self.cpp_info.names["cmake_find_package"] = "ACADO"
        self.cpp_info.names["cmake_find_package_multi"] = "ACADO"

        self.cpp_info.builddirs.append(os.path.join("lib", "cmake"))
        self.cpp_info.build_modules.append(os.path.join("lib", "cmake", "qpoases.cmake"))

        self.cpp_info.includedirs.append(os.path.join("include", "acado"))
        self.cpp_info.includedirs.append(self._qpoases_sources)
        self.cpp_info.includedirs.append(os.path.join(self._qpoases_sources, "INCLUDE"))
        self.cpp_info.includedirs.append(os.path.join(self._qpoases_sources, "SRC"))

    def validate(self):
        if self.settings.compiler == "Visual Studio" and self.options.shared:
            # https://github.com/acado/acado/blob/b4e28f3131f79cadfd1a001e9fff061f361d3a0f/CMakeLists.txt#L77-L80
            raise ConanInvalidConfiguration("Acado does not support shared builds on Windows.")
        if self.settings.compiler == "apple-clang":
            raise ConanInvalidConfiguration("apple-clang not supported")
        if self.settings.compiler == "clang" and self.settings.compiler.version == "9":
            raise ConanInvalidConfiguration("acado can not be built by Clang 9.")

        # acado requires libstdc++11 for shared builds
        # https://github.com/conan-io/conan-center-index/pull/3967#issuecomment-752985640
        if (
            self.options.shared
            and self.settings.compiler == "clang"
            and self.settings.compiler.libcxx != "libstdc++11"
        ):
            raise ConanInvalidConfiguration("libstdc++11 required")
        if (
            self.options.shared
            and self.settings.compiler == "gcc"
            and self.settings.compiler.libcxx != "libstdc++11"
        ):
            raise ConanInvalidConfiguration("libstdc++11 required")
