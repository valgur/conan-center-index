import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.cmake import CMakeToolchain, CMake, cmake_layout, CMakeDeps
from conan.tools.files import get, copy, rmdir, apply_conandata_patches, export_conandata_patches

required_conan_version = ">=2.1"


class opengvConan(ConanFile):
    name = "opengv"
    description = "A collection of computer vision methods for solving geometric vision problems"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/laurentkneip/opengv"
    license = "BSD-3-Clause"
    topics = ("computer", "vision", "geometric", "pose", "triangulation", "point-cloud")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "with_python_bindings": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "with_python_bindings": False,
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
        self.requires("eigen/3.4.0", transitive_headers=True)
        if self.options.with_python_bindings:
            self.requires("pybind11/2.10.1")

    def validate(self):
        # Disable windows builds since they error out.
        if self.settings.os == "Windows":
            raise ConanInvalidConfiguration("Windows builds are not supported by this recipe.")
        #FIXME this passes locally but fails on CCI with a clang internal error
        if self.settings.compiler == "clang" and self.settings.compiler.version == 12:
            raise ConanInvalidConfiguration("Clang 12 builds fail on Conan CI.")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        apply_conandata_patches(self)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["BUILD_TESTS"] = False
        tc.variables["BUILD_PYTHON"] = self.options.with_python_bindings
        tc.variables["BUILD_POSITION_INDEPENDENT_CODE"] = self.settings.os != "Windows" and self.options.get_safe("fPIC", True)
        tc.generate()

        cd = CMakeDeps(self)
        cd.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "License.txt", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder)
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "opengv")
        self.cpp_info.set_property("cmake_target_name", "opengv")
        self.cpp_info.libs = ["opengv"]
        if self.options.with_python_bindings:
            opengv_dist_packages = os.path.join(self.package_folder, "lib", "python3", "dist-packages")
            self.runenv_info.prepend_path("PYTHONPATH", opengv_dist_packages)
