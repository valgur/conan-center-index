import os

from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *

required_conan_version = ">=2.1"


class LiblslConan(ConanFile):
    name = "liblsl"
    description = "Lab Streaming Layer is a C++ library for multi-modal " \
                  "time-synched data transmission over the local network"
    license = "MIT"
    topics = ("labstreaminglayer", "lsl", "network", "stream", "signal", "transmission")
    homepage = "https://github.com/sccn/liblsl"
    url = "https://github.com/conan-io/conan-center-index"

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

    def requirements(self):
        self.requires("boost/[^1.71.0]", libs=False)
        self.requires("pugixml/[^1.13]")

    def layout(self):
        cmake_layout(self, src_folder="src")

    def validate(self):
        check_min_cppstd(self, 14)

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        replace_in_file(self, "CMakeLists.txt", "set(CMAKE_POSITION_INDEPENDENT_CODE ON)", "")

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["LSL_BUILD_STATIC"] = not self.options.shared
        tc.variables["LSL_BUNDLED_BOOST"] = False
        tc.variables["LSL_BUNDLED_PUGIXML"] = False
        tc.variables["lslgitrevision"] = "v" + self.version
        tc.variables["lslgitbranch"] = "master"
        tc.generate()
        cd = CMakeDeps(self)
        cd.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        cmake = CMake(self)
        cmake.install()
        rm(self, "lslver*", os.path.join(self.package_folder, "bin"))
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))
        copy(self, "LICENSE", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "LSL")
        self.cpp_info.set_property("cmake_target_name", "LSL::lsl")
        self.cpp_info.requires = ["boost::headers", "pugixml::pugixml"]
        self.cpp_info.libs = ["lsl"]
        self.cpp_info.defines = ["LSLNOAUTOLINK"]
        if not self.options.shared:
            self.cpp_info.defines.append("LIBLSL_STATIC")
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs = ["pthread"]
        elif self.settings.os == "Windows":
            self.cpp_info.system_libs = ["iphlpapi", "winmm", "mswsock", "ws2_32"]
