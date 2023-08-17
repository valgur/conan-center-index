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
from conan.tools.scm import Version
from conan.tools.system import package_manager
from conan.tools.cmake import (
    CMake,
    CMakeDeps,
    CMakeToolchain,
    cmake_layout,
)

required_conan_version = ">=1.53.0"


class AcadoConan(ConanFile):
    name = "acado"
    description = (
        "ACADO Toolkit is a software environment and algorithm collection for automatic control and dynamic optimization."
    )
    license = "LGPL-3.0"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/acado/acado"
    topics = ("control", "optimization", "mpc")

    package_type = "library"
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
        export_conandata_patches(self)
        copy(self, "CMakeLists.txt",
             src=self.recipe_folder,
             dst=self.export_sources_path / "tmp")
        copy(self, "CMakeLists.txt",
             src=os.path.join(self.recipe_folder, "acado"),
             dst=self.export_sources_path / "tmp" / "acado")

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires("qpoases/3.2.1", transitive_headers=True)

    def validate(self):
        if is_msvc(self) and self.options.shared:
            # https://github.com/acado/acado/blob/b4e28f3131f79cadfd1a001e9fff061f361d3a0f/CMakeLists.txt#L77-L80
            raise ConanInvalidConfiguration("Acado does not support shared builds on Windows.")
        if self.settings.compiler == "apple-clang":
            raise ConanInvalidConfiguration("apple-clang not supported")
        if self.settings.compiler == "clang" and self.settings.compiler.version == "9":
            raise ConanInvalidConfiguration("acado can not be built by Clang 9.")

        # acado requires libstdc++11 for shared builds
        # https://github.com/conan-io/conan-center-index/pull/3967#issuecomment-752985640
        if self.options.shared and self.settings.compiler == "clang" and self.settings.compiler.libcxx != "libstdc++11":
            raise ConanInvalidConfiguration("libstdc++11 required")
        if self.options.shared and self.settings.compiler == "gcc" and self.settings.compiler.libcxx != "libstdc++11":
            raise ConanInvalidConfiguration("libstdc++11 required")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        for d in ["qpoases", "qpoases3", "qpOASES-3.0beta", "qpOASES-3.2.0"]:
            rmdir(self, os.path.join(self.source_folder, "external_packages", d))
        # TODO: should also use Eigen3 from Conan
        # rmdir(self, os.path.join(self.source_folder, "external_packages", "eigen3"))
        # replace_in_file(
        #     self, os.path.join(self.source_folder, "acado/matrix_vector/matrix_vector_tools.hpp"), "external_packages/eigen3/", ""
        # )

        copy(self, "CMakeLists.txt",
             src=self.export_sources_path / "tmp",
             dst=os.path.join(self.source_folder))
        copy(self, "CMakeLists.txt",
             src=self.export_sources_path / "tmp" / "acado",
             dst=os.path.join(self.source_folder, "acado"))


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

        # ACADO logs 170,000 lines of warnings, so we disable them
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

    def package(self):
        copy(self, "LICENSE.txt", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()

        copy(self, "*",
             src=os.path.join(self.build_folder, "lib"),
             dst=os.path.join(self.package_folder, "lib"))

        rmdir(self, os.path.join(self.package_folder, "share"))
        rm(self, "*.pdb", self.package_folder, recursive=True)

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "ACADO")
        self.cpp_info.set_property("cmake_target_name", "ACADO::ACADO")

        if self.options.shared:
            self.cpp_info.libs = ["acado_toolkit_s", "acado_casadi"]
        else:
            self.cpp_info.libs = ["acado_toolkit", "acado_casadi"]

        self.cpp_info.builddirs.append(os.path.join("lib", "cmake"))

        self.cpp_info.includedirs.append(os.path.join("include", "acado"))

        acado_template_paths = os.path.join(self.package_folder, "include", "acado", "code_generation", "templates")
        self.conf_info.define("user.acado:template_paths", acado_template_paths)

        # TODO: to remove in conan v2
        self.output.info(f"Setting ACADO_TEMPLATE_PATHS environment variable: {acado_template_paths}")
        self.env_info.ACADO_TEMPLATE_PATHS = acado_template_paths
        self.cpp_info.names["cmake_find_package"] = "ACADO"
        self.cpp_info.names["cmake_find_package_multi"] = "ACADO"
