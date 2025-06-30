import os

from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *

required_conan_version = ">=2.1"


class GnuradioVolkConan(ConanFile):
    name = "gnuradio-volk"
    description = "VOLK is the Vector-Optimized Library of Kernels."
    license = "LGPL-3.0-or-later"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://www.libvolk.org/"
    topics = ("simd", "kernel", "sdr", "dsp", "gnuradio")

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
    implements = ["auto_shared_fpic"]

    python_requires = "conan-utils/latest"

    @property
    def _utils(self):
        return self.python_requires["conan-utils"].module

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires("cpu_features/0.9.0")
        # TODO: add recipe for gstreamer-orc https://github.com/GStreamer/orc

    def validate(self):
        check_min_cppstd(self, 17)

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        # Disable apps
        save(self, "apps/CMakeLists.txt", "")

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["ENABLE_STATIC_LIBS"] = not self.options.shared
        tc.variables["ENABLE_TESTING"] = False
        tc.variables["ENABLE_MODTOOL"] = False  # Requires Python
        tc.variables["ENABLE_ORC"] = False  # Not available on CCI
        tc.cache_variables["CMAKE_POLICY_DEFAULT_CMP0148"] = "OLD" # FindPythonInterp support
        tc.cache_variables["CMAKE_POLICY_DEFAULT_CMP0077"] = "NEW" # tc.requires support
        tc.generate()

        deps = CMakeDeps(self)
        deps.generate()

        venv = self._utils.PythonVenv(self)
        venv.generate(system_site_packages=True)

    def build(self):
        self._utils.pip_install(self, ["mako"])
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "COPYING", self.source_folder, os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        if not self.options.shared:
            rm(self, "*.so*", os.path.join(self.package_folder, "lib"))
            rm(self, "*.dylib*", os.path.join(self.package_folder, "lib"))
            rm(self, "volk.dll.lib", os.path.join(self.package_folder, "lib"))
            rm(self, "volk.dll", os.path.join(self.package_folder, "bin"))
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))
        rm(self, "*.pdb", os.path.join(self.package_folder, "lib"))
        rm(self, "*.pdb", os.path.join(self.package_folder, "bin"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "Volk")
        self.cpp_info.set_property("cmake_target_name", "Volk::volk")
        self.cpp_info.set_property("pkg_config_name", "volk")
        self.cpp_info.libs = ["volk"]
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs.extend(["m", "pthread"])
