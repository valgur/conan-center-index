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
from conan.tools.scm import Version
from conan.tools.system import package_manager
from conan.tools.cmake import (
    CMake,
    CMakeDeps,
    CMakeToolchain,
    cmake_layout,
)
import os


class Libfreenect2Conan(ConanFile):
    name = "libfreenect2"
    license = ("Apache-2.0", "GPL-2.0")
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/OpenKinect/libfreenect2"
    description = "Open source drivers for the Kinect for Windows v2 device."
    topics = ("usb", "camera", "kinect")
    settings = "os", "compiler", "build_type", "arch"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "with_opencl": [True, False],
        "with_opengl": [True, False],
        "with_vaapi": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "with_opencl": True,
        "with_opengl": True,
        "with_vaapi": True,
    }

    def export_sources(self):
        export_conandata_patches(self)

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC
        if self.settings.os != "Linux":
            self.options.rm_safe("with_vaapi")

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")

    def requirements(self):
        self.requires("libusb/1.0.24")
        self.requires("libjpeg-turbo/2.1.1")
        if self.options.with_opencl:
            self.requires("opencl-headers/2021.04.29")
            self.requires("opencl-icd-loader/2021.04.29")
        if self.options.with_opengl:
            self.requires("opengl/system")
            self.requires("glfw/3.3.4")
        if self.options.get_safe("with_vaapi"):
            self.requires("vaapi/system")

    def validate(self):
        if self.settings.compiler.get_safe("cppstd"):
            check_min_cppstd(self, 11)

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def _patch_sources(self):
        apply_conandata_patches(self)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["BUILD_EXAMPLES"] = False
        tc.variables["BUILD_OPENNI2_DRIVER"] = False
        tc.variables["ENABLE_CXX11"] = True
        tc.variables["ENABLE_OPENCL"] = self.options.with_opencl
        tc.variables["ENABLE_CUDA"] = False  # TODO: CUDA
        tc.variables["ENABLE_OPENGL"] = self.options.with_opengl
        tc.variables["ENABLE_VAAPI"] = self.options.get_safe("with_vaapi", False)
        tc.variables["ENABLE_TEGRAJPEG"] = False  # TODO: TegraJPEG
        tc.variables["ENABLE_PROFILING"] = False
        tc.generate()

        tc = CMakeDeps(self)
        tc.generate()

    def build(self):
        self._patch_sources()
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(
            self,
            "APACHE20",
            src=self.source_folder,
            dst=os.path.join(self.package_folder, "licenses"),
            keep_path=False,
        )
        copy(
            self,
            "GPL2",
            src=self.source_folder,
            dst=os.path.join(self.package_folder, "licenses"),
            keep_path=False,
        )
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))

    def package_info(self):
        self.cpp_info.names["cmake_find_package"] = "freenect2"
        self.cpp_info.names["cmake_find_package_multi"] = "freenect2"
        self.cpp_info.names["pkg_config"] = "freenect2"
        self.cpp_info.libs = collect_libs(self)
        if self.settings.os == "Linux":
            self.cpp_info.system_libs.extend(["m", "pthread", "dl"])
        elif self.settings.os == "Macos":
            self.cpp_info.frameworks.extend(["VideoToolbox", "CoreFoundation", "CoreMedia", "CoreVideo"])
