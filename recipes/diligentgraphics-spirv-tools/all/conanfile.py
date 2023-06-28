# TODO: verify the Conan v2 migration

import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import check_min_cppstd, stdcpp_library
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import (
    apply_conandata_patches,
    copy,
    export_conandata_patches,
    get,
    replace_in_file,
    rm,
    rmdir,
)

required_conan_version = ">=1.53.0"


class SpirvtoolsConan(ConanFile):
    name = "diligentgraphics-spirv-tools"
    description = "Diligent fork. Create and optimize SPIRV shaders"
    license = "Apache-2.0"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/DiligentGraphics/SPIRV-Tools/"
    topics = ("spirv", "spirv-v", "vulkan", "opengl", "opencl", "hlsl", "khronos", "diligent")

    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "build_executables": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "build_executables": True,
    }
    provides = "spirv-tools"
    deprecated = "spirv-tools"

    def export_sources(self):
        export_conandata_patches(self)

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")

    def layout(self):
        cmake_layout(self, src_folder="src")

    @property
    def _get_compatible_spirv_headers_version(self):
        return {
            "cci.20211008": "cci.20211006",
        }.get(str(self.version), False)

    def requirements(self):
        if not self._get_compatible_spirv_headers_version:
            raise ConanInvalidConfiguration("unknown diligentgraphics-spirv-headers version")
        self.requires("diligentgraphics-spirv-headers/{}".format(self._get_compatible_spirv_headers_version))

    def validate(self):
        if self.settings.compiler.get_safe("cppstd"):
            check_min_cppstd(self, 11)

    def _validate_dependency_graph(self):
        if (
            self.dependencies["diligentgraphics-spirv-headers"].ref.version
            != self._get_compatible_spirv_headers_version
        ):
            raise ConanInvalidConfiguration(
                "diligentgraphics-spirv-tools {0} requires diligentgraphics-spirv-headers {1}".format(
                    self.version, self._get_compatible_spirv_headers_version
                )
            )

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)

        # Required by the project's CMakeLists.txt
        tc.variables["SPIRV-Headers_SOURCE_DIR"] = self.dependencies[
            "diligentgraphics-spirv-headers"
        ].package_folder.replace("\\", "/")

        # There are some switch( ) statements that are causing errors
        # need to turn this off
        tc.variables["SPIRV_WERROR"] = False

        tc.variables["SKIP_SPIRV_TOOLS_INSTALL"] = False
        tc.variables["SPIRV_LOG_DEBUG"] = False
        tc.variables["SPIRV_SKIP_TESTS"] = True
        tc.variables["SPIRV_CHECK_CONTEXT"] = False
        tc.variables["SPIRV_BUILD_FUZZER"] = False
        tc.variables["SPIRV_SKIP_EXECUTABLES"] = not self.options.build_executables

        tc.generate()

        tc = CMakeDeps(self)
        tc.generate()

    def _patch_sources(self):
        apply_conandata_patches(self)
        # CMAKE_POSITION_INDEPENDENT_CODE was set ON for the entire
        # project in the lists file.
        replace_in_file(
            self,
            os.path.join(self.source_folder, "CMakeLists.txt"),
            "set(CMAKE_POSITION_INDEPENDENT_CODE ON)",
            "",
        )

    def build(self):
        self._validate_dependency_graph()
        self._patch_sources()
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(
            self,
            pattern="LICENSE*",
            dst=os.path.join(self.package_folder, "licenses"),
            src=self.source_folder,
        )
        cmake = CMake(self)
        cmake.install()

        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))
        rmdir(self, os.path.join(self.package_folder, "SPIRV-Tools"))
        rmdir(self, os.path.join(self.package_folder, "SPIRV-Tools-link"))
        rmdir(self, os.path.join(self.package_folder, "SPIRV-Tools-opt"))
        rmdir(self, os.path.join(self.package_folder, "SPIRV-Tools-reduce"))
        rmdir(self, os.path.join(self.package_folder, "SPIRV-Tools-lint"))

        if self.options.shared:
            for file_name in ["*SPIRV-Tools", "*SPIRV-Tools-opt", "*SPIRV-Tools-link", "*SPIRV-Tools-reduce"]:
                for ext in [".a", ".lib"]:
                    rm(self, file_name + ext, os.path.join(self.package_folder, "lib"), recursive=True)
        else:
            rm(self, "*SPIRV-Tools-shared.dll", os.path.join(self.package_folder, "bin"), recursive=True)
            rm(self, "*SPIRV-Tools-shared*", os.path.join(self.package_folder, "lib"), recursive=True)

        if self.options.shared:
            targets = {
                "SPIRV-Tools-shared": "diligentgraphics-spirv-tools::SPIRV-Tools",
            }
        else:
            targets = {
                "SPIRV-Tools": (
                    "diligentgraphics-spirv-tools::SPIRV-Tools"
                ),  # before 2020.5, kept for conveniency
                "SPIRV-Tools-static": "diligentgraphics-spirv-tools::SPIRV-Tools",
                "SPIRV-Tools-opt": "diligentgraphics-spirv-tools::SPIRV-Tools-opt",
                "SPIRV-Tools-link": "diligentgraphics-spirv-tools::SPIRV-Tools-link",
                "SPIRV-Tools-reduce": "diligentgraphics-spirv-tools::SPIRV-Tools-reduce",
            }
        self._create_cmake_module_alias_targets(
            os.path.join(self.package_folder, self._module_file_rel_path), targets
        )

    @property
    def _module_subfolder(self):
        return os.path.join("lib", "cmake")

    @property
    def _module_file_rel_path(self):
        return os.path.join(self._module_subfolder, "conan-official-{}-targets.cmake".format(self.name))

    def package_info(self):
        self.cpp_info.filenames["cmake_find_package"] = "SPIRV-Tools"
        self.cpp_info.filenames["cmake_find_package_multi"] = "SPIRV-Tools"
        self.cpp_info.names["pkg_config"] = "SPIRV-Tools-shared" if self.options.shared else "SPIRV-Tools"

        # SPIRV-Tools
        self.cpp_info.components["spirv-tools-core"].names["cmake_find_package"] = "SPIRV-Tools"
        self.cpp_info.components["spirv-tools-core"].names["cmake_find_package_multi"] = "SPIRV-Tools"
        self.cpp_info.components["spirv-tools-core"].builddirs.append(self._module_subfolder)
        self.cpp_info.components["spirv-tools-core"].build_modules["cmake_find_package"] = [
            self._module_file_rel_path
        ]
        self.cpp_info.components["spirv-tools-core"].build_modules["cmake_find_package_multi"] = [
            self._module_file_rel_path
        ]
        self.cpp_info.components["spirv-tools-core"].libs = [
            "SPIRV-Tools-shared" if self.options.shared else "SPIRV-Tools"
        ]
        self.cpp_info.components["spirv-tools-core"].requires = [
            "diligentgraphics-spirv-headers::diligentgraphics-spirv-headers"
        ]
        if self.options.shared:
            self.cpp_info.components["spirv-tools-core"].defines = ["SPIRV_TOOLS_SHAREDLIB"]
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.components["spirv-tools-core"].system_libs.extend(["m", "rt"])
        if not self.options.shared and stdcpp_library(self):
            self.cpp_info.components["spirv-tools-core"].system_libs.append(stdcpp_library(self))

        # FIXME: others components should have their own CMake config file
        if not self.options.shared:
            # SPIRV-Tools-opt
            self.cpp_info.components["spirv-tools-opt"].names["cmake_find_package"] = "SPIRV-Tools-opt"
            self.cpp_info.components["spirv-tools-opt"].names["cmake_find_package_multi"] = "SPIRV-Tools-opt"
            self.cpp_info.components["spirv-tools-opt"].builddirs.append(self._module_subfolder)
            self.cpp_info.components["spirv-tools-opt"].build_modules["cmake_find_package"] = [
                self._module_file_rel_path
            ]
            self.cpp_info.components["spirv-tools-opt"].build_modules["cmake_find_package_multi"] = [
                self._module_file_rel_path
            ]
            self.cpp_info.components["spirv-tools-opt"].libs = ["SPIRV-Tools-opt"]
            self.cpp_info.components["spirv-tools-opt"].requires = [
                "spirv-tools-core",
                "diligentgraphics-spirv-headers::diligentgraphics-spirv-headers",
            ]
            if self.settings.os in ["Linux", "FreeBSD"]:
                self.cpp_info.components["spirv-tools-opt"].system_libs.append("m")
            # SPIRV-Tools-link
            self.cpp_info.components["spirv-tools-link"].names["cmake_find_package"] = "SPIRV-Tools-link"
            self.cpp_info.components["spirv-tools-link"].names[
                "cmake_find_package_multi"
            ] = "SPIRV-Tools-link"
            self.cpp_info.components["spirv-tools-link"].builddirs.append(self._module_subfolder)
            self.cpp_info.components["spirv-tools-link"].build_modules["cmake_find_package"] = [
                self._module_file_rel_path
            ]
            self.cpp_info.components["spirv-tools-link"].build_modules["cmake_find_package_multi"] = [
                self._module_file_rel_path
            ]
            self.cpp_info.components["spirv-tools-link"].libs = ["SPIRV-Tools-link"]
            self.cpp_info.components["spirv-tools-link"].requires = ["spirv-tools-core", "spirv-tools-opt"]
            # SPIRV-Tools-reduce
            self.cpp_info.components["spirv-tools-reduce"].names["cmake_find_package"] = "SPIRV-Tools-reduce"
            self.cpp_info.components["spirv-tools-reduce"].names[
                "cmake_find_package_multi"
            ] = "SPIRV-Tools-reduce"
            self.cpp_info.components["spirv-tools-reduce"].builddirs.append(self._module_subfolder)
            self.cpp_info.components["spirv-tools-reduce"].build_modules["cmake_find_package"] = [
                self._module_file_rel_path
            ]
            self.cpp_info.components["spirv-tools-reduce"].build_modules["cmake_find_package_multi"] = [
                self._module_file_rel_path
            ]
            self.cpp_info.components["spirv-tools-reduce"].libs = ["SPIRV-Tools-reduce"]
            self.cpp_info.components["spirv-tools-reduce"].requires = ["spirv-tools-core", "spirv-tools-opt"]

        bin_path = os.path.join(self.package_folder, "bin")
        self.output.info(f"Appending PATH environment variable: {bin_path}")
        self.env_info.path.append(bin_path)
