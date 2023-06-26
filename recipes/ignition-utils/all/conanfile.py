# TODO: verify the Conan v2 migration

import os
import textwrap

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import apply_conandata_patches, copy, export_conandata_patches, get, rm, rmdir, save
from conan.tools.scm import Version

required_conan_version = ">=1.53.0"


class IgnitionUitlsConan(ConanFile):
    name = "ignition-utils"
    description = "Provides general purpose classes and functions designed for robotic applications.."
    license = "Apache-2.0"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://gazebosim.org/libs/utils"
    topics = ("ignition", "robotics", "utils")

    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "ign_utils_vendor_cli11": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "ign_utils_vendor_cli11": True,
    }

    @property
    def _minimum_cpp_standard(self):
        return 17

    @property
    def _minimum_compilers_version(self):
        return {
            "Visual Studio": "16",
            "gcc": "7",
            "clang": "5",
            "apple-clang": "10",
        }

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

    def requirements(self):
        self.requires("doxygen/1.9.2")
        if self.options.ign_utils_vendor_cli11:
            self.requires("cli11/2.1.2")

    def validate(self):
        if self.settings.os == "Macos" and self.settings.arch == "armv8":
            raise ConanInvalidConfiguration("sorry, M1 builds are not currently supported, give up!")
        if self.settings.compiler.cppstd:
            check_min_cppstd(self, self._minimum_cpp_standard)
        min_version = self._minimum_compilers_version.get(str(self.settings.compiler))
        if not min_version:
            self.output.warn(
                f"{self.name} recipe lacks information about the {self.settings.compiler} compiler support."
            )
        else:
            if Version(self.settings.compiler.version) < min_version:
                raise ConanInvalidConfiguration(
                    f"{self.name} requires c++17 support. The current compiler"
                    f" {self.settings.compiler} {self.settings.compiler.version} does not support it."
                )

    def build_requirements(self):
        self.build_requires("ignition-cmake/2.10.0")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["BUILD_TESTING"] = False
        tc.variables["IGN_UTILS_VENDOR_CLI11"] = self.options.ign_utils_vendor_cli11
        tc.variables["CMAKE_FIND_DEBUG_MODE"] = True
        tc.generate()
        tc = CMakeDeps(self)
        tc.generate()

    def build(self):
        apply_conandata_patches(self)
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def _create_cmake_module_variables(self, module_file, version):
        content = textwrap.dedent(f"""\
            set(ignition-utils{version.major}_VERSION_MAJOR {version.major})
            set(ignition-utils{version.major}_VERSION_MINOR {version.minor})
            set(ignition-utils{version.major}_VERSION_PATCH {version.patch})
            set(ignition-utils{version.major}_VERSION_STRING "{version.major}.{version.minor}.{version.patch}")
        """)
        save(self, module_file, content)

    def package(self):
        copy(self, "LICENSE", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder)
        cli_header_src = os.path.join(self.source_folder, "cli", "include")
        if int(Version(self.version).minor) == 0:
            cli_header_src = os.path.join(cli_header_src, "ignition", "utils", "cli")
        else:
            cli_header_src = os.path.join(cli_header_src, "external-cli", "ignition", "utils", "cli")
        copy(
            self,
            "*.hpp",
            src=cli_header_src,
            dst=os.path.join(self.package_folder, "include/ignition/utils1/ignition/utils/cli"),
        )
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "share"))
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))

        # Remove MS runtime files
        for dll_pattern_to_remove in ["concrt*.dll", "msvcp*.dll", "vcruntime*.dll"]:
            rm(self, dll_pattern_to_remove, os.path.join(self.package_folder, "bin"), recursive=True)

        self._create_cmake_module_variables(
            os.path.join(self.package_folder, self._module_file_rel_path), Version(self.version)
        )

    @property
    def _module_file_rel_path(self):
        return os.path.join("lib", "cmake", f"conan-official-{self.name}-variables.cmake")

    def package_info(self):
        version_major = Version(self.version).major
        lib_name = f"ignition-utils{version_major}"
        build_dirs = os.path.join(self.package_folder, "lib", "cmake")
        include_dir = os.path.join("include", "ignition", "utils" + version_major)
        self.cpp_info.names["cmake_find_package"] = lib_name
        self.cpp_info.names["cmake_find_package_multi"] = lib_name
        self.cpp_info.names["cmake_paths"] = lib_name

        self.cpp_info.components[lib_name].names["cmake_find_package"] = lib_name
        self.cpp_info.components[lib_name].names["cmake_find_package_multi"] = lib_name
        self.cpp_info.components[lib_name].names["cmake_paths"] = lib_name
        self.cpp_info.components[lib_name].libs = [lib_name]
        self.cpp_info.components[lib_name].includedirs.append(include_dir)
        self.cpp_info.components[lib_name].requires = ["doxygen::doxygen"]
        if self.options.ign_utils_vendor_cli11:
            self.cpp_info.components[lib_name].requires.append("cli11::cli11")

        self.cpp_info.components[lib_name].builddirs.append(build_dirs)
        self.cpp_info.components[lib_name].build_modules["cmake_find_package"] = [self._module_file_rel_path]
        self.cpp_info.components[lib_name].build_modules["cmake_find_package_multi"] = [
            self._module_file_rel_path
        ]
        self.cpp_info.components[lib_name].build_modules["cmake_paths"] = [self._module_file_rel_path]

        self.cpp_info.components["cli"].names["cmake_find_package"] = "cli"
        self.cpp_info.components["cli"].names["cmake_find_package_multi"] = "cli"
        self.cpp_info.components["cli"].names["cmake_paths"] = "cli"
        self.cpp_info.components["cli"].includedirs.append(os.path.join(include_dir, "ignition", "utils"))
        if self.options.ign_utils_vendor_cli11:
            self.cpp_info.components["cli"].requires = ["cli11::cli11"]

        self.cpp_info.components["cli"].builddirs.append(build_dirs)
        self.cpp_info.components["cli"].build_modules["cmake_find_package"] = [self._module_file_rel_path]
        self.cpp_info.components["cli"].build_modules["cmake_find_package_multi"] = [
            self._module_file_rel_path
        ]
        self.cpp_info.components["cli"].build_modules["cmake_paths"] = [self._module_file_rel_path]
