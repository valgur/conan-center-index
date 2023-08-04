import os

from conan import ConanFile
from conan.tools.apple import is_apple_os
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import apply_conandata_patches, collect_libs, copy, export_conandata_patches, get, rmdir

required_conan_version = ">=1.53.0"


class Libfreenect2Conan(ConanFile):
    name = "libfreenect2"
    description = "Open source drivers for the Kinect for Windows v2 device."
    license = ("Apache-2.0", "GPL-2.0")
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/OpenKinect/libfreenect2"
    topics = ("usb", "camera", "kinect")

    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "with_opencl": [True, False],
        "with_opengl": [True, False],
        "with_vaapi": [True, False],
        "with_cuda": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "with_opencl": True,
        "with_opengl": True,
        "with_vaapi": True,
        "with_cuda": False,
    }

    def export_sources(self):
        export_conandata_patches(self)

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC
        if self.settings.os not in ["Linux", "FreeBSD"]:
            self.options.rm_safe("with_vaapi")

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires("libusb/1.0.26")
        self.requires("libjpeg-turbo/3.0.0")
        if self.options.with_opencl:
            self.requires("opencl-headers/2023.04.17")
            self.requires("opencl-icd-loader/2023.04.17")
        if self.options.with_opengl:
            self.requires("opengl/system")
            self.requires("glfw/3.3.8")
        if self.options.get_safe("with_vaapi"):
            self.requires("vaapi/system")

    def validate(self):
        if self.settings.compiler.get_safe("cppstd"):
            check_min_cppstd(self, 11)
        if self.options.with_cuda:
            self.output.warning("Conan package for CUDA is not available, this package will be used from system.")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["BUILD_EXAMPLES"] = False
        tc.variables["BUILD_OPENNI2_DRIVER"] = False
        tc.variables["ENABLE_CXX11"] = True
        tc.variables["ENABLE_OPENCL"] = self.options.with_opencl
        tc.variables["ENABLE_CUDA"] = self.options.with_cuda
        tc.variables["ENABLE_OPENGL"] = self.options.with_opengl
        tc.variables["ENABLE_VAAPI"] = self.options.get_safe("with_vaapi", False)
        tc.variables["ENABLE_TEGRAJPEG"] = False  # TODO: TegraJPEG
        tc.variables["ENABLE_PROFILING"] = False
        tc.generate()

        tc = CMakeDeps(self)
        tc.generate()

    def build(self):
        apply_conandata_patches(self)
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "APACHE20",
            src=self.source_folder,
            dst=os.path.join(self.package_folder, "licenses"),
            keep_path=False)
        copy(self, "GPL2",
            src=self.source_folder,
            dst=os.path.join(self.package_folder, "licenses"),
            keep_path=False)
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "freenect2")
        self.cpp_info.set_property("cmake_target_name", "freenect2::freenect2")
        self.cpp_info.set_property("pkg_config_name", "freenect2")
        self.cpp_info.libs = collect_libs(self)
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs.extend(["m", "pthread", "dl"])
        elif is_apple_os(self):
            self.cpp_info.frameworks.extend(["VideoToolbox", "CoreFoundation", "CoreMedia", "CoreVideo"])

        # TODO: to remove in conan v2 once cmake_find_package_* generators removed
        self.cpp_info.names["cmake_find_package"] = "freenect2"
        self.cpp_info.names["cmake_find_package_multi"] = "freenect2"
