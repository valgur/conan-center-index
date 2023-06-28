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


class IgnitionMathConan(ConanFile):
    name = "ignition-math"
    description = " Math classes and functions for robot applications"
    license = "Apache-2.0"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://gazebosim.org/libs/math"
    topics = ("ignition", "math", "robotics", "gazebo")

    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
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
        if self.settings.compiler.cppstd:
            check_min_cppstd(self, self._minimum_cpp_standard)
        min_version = self._minimum_compilers_version.get(str(self.settings.compiler))
        if not min_version:
            self.output.warning(
                f"{self.name} recipe lacks information about the {self.settings.compiler} compiler support."
            )
        else:
            if Version(self.settings.compiler.version) < min_version:
                raise ConanInvalidConfiguration(
                    f"{self.name} requires c++17 support. The current compiler"
                    f" {self.settings.compiler} {self.settings.compiler.version} does not support it."
                )

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires("eigen/3.3.9")
        self.requires("doxygen/1.8.17")
        self.requires("swig/4.0.2")

    def validate(self):
        if self.settings.os == "Macos" and self.settings.arch == "armv8":
            raise ConanInvalidConfiguration("sorry, M1 builds are not currently supported, give up!")

    def build_requirements(self):
        if int(Version(self.version).minor) <= 8:
            self.build_requires("ignition-cmake/2.5.0")
        else:
            self.build_requires("ignition-cmake/2.10.0")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["BUILD_TESTING"] = False
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
            set(ignition-math{version.major}_VERSION_MAJOR {version.major})
            set(ignition-math{version.major}_VERSION_MINOR {version.minor})
            set(ignition-math{version.major}_VERSION_PATCH {version.patch})
            set(ignition-math{version.major}_VERSION_STRING "{version.major}.{version.minor}.{version.patch}")
            set(ignition-math{version.major}_INCLUDE_DIRS "${{CMAKE_CURRENT_LIST_DIR}}/../../include/ignition/math{version.major}")
        """)
        save(self, module_file, content)

    def package(self):
        copy(self, "LICENSE", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder)
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "share"))
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))
        self._create_cmake_module_variables(
            os.path.join(self.package_folder, self._module_file_rel_path), Version(self.version)
        )

        # Remove MS runtime files
        for dll_pattern_to_remove in ["concrt*.dll", "msvcp*.dll", "vcruntime*.dll"]:
            rm(self, dll_pattern_to_remove, os.path.join(self.package_folder, "bin"), recursive=True)

    @property
    def _module_file_rel_dir(self):
        return os.path.join("lib", "cmake")

    @property
    def _module_file_rel_path(self):
        return os.path.join(self._module_file_rel_dir, f"conan-official-{self.name}-variables.cmake")

    def package_info(self):
        version_major = Version(self.version).major
        lib_name = f"ignition-math{version_major}"

        self.cpp_info.set_property("cmake_file_name", lib_name)
        self.cpp_info.set_property("cmake_target_name", lib_name)

        # TODO: to remove in conan v2 once cmake_find_package_* generators removed
        self.cpp_info.names["cmake_find_package"] = lib_name
        self.cpp_info.names["cmake_find_package_multi"] = lib_name
        self.cpp_info.names["cmake_paths"] = lib_name

        self.cpp_info.components[lib_name].names["cmake_find_package"] = lib_name
        self.cpp_info.components[lib_name].names["cmake_find_package_multi"] = lib_name
        self.cpp_info.components[lib_name].names["cmake_paths"] = lib_name
        self.cpp_info.components[lib_name].libs = [lib_name]
        self.cpp_info.components[lib_name].includedirs.append(
            os.path.join("include", "ignition", "math" + version_major)
        )
        self.cpp_info.components[lib_name].requires = ["swig::swig", "eigen::eigen", "doxygen::doxygen"]

        self.cpp_info.components[lib_name].builddirs = [self._module_file_rel_dir]
        self.cpp_info.components[lib_name].build_modules["cmake_find_package"] = [self._module_file_rel_path]
        self.cpp_info.components[lib_name].build_modules["cmake_find_package_multi"] = [
            self._module_file_rel_path
        ]
        self.cpp_info.components[lib_name].build_modules["cmake_paths"] = [self._module_file_rel_path]

        self.cpp_info.components["eigen3"].names["cmake_find_package"] = "eigen3"
        self.cpp_info.components["eigen3"].names["cmake_find_package_multi"] = "eigen3"
        self.cpp_info.components["eigen3"].names["cmake_paths"] = "eigen3"
        self.cpp_info.components["eigen3"].includedirs.append(
            os.path.join("include", "ignition", "math" + version_major)
        )
        self.cpp_info.components["eigen3"].requires = ["eigen::eigen"]

        self.cpp_info.components["eigen3"].builddirs = [self._module_file_rel_dir]
        self.cpp_info.components["eigen3"].build_modules["cmake_find_package"] = [self._module_file_rel_path]
        self.cpp_info.components["eigen3"].build_modules["cmake_find_package_multi"] = [
            self._module_file_rel_path
        ]
        self.cpp_info.components["eigen3"].build_modules["cmake_paths"] = [self._module_file_rel_path]
