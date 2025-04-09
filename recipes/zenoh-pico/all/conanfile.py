import os
import re
from pathlib import Path

from conan import ConanFile
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout
from conan.tools.files import *

required_conan_version = ">=2.4"


class ZenohPicoConan(ConanFile):
    name = "zenoh-pico"
    description = "Zenoh for pico devices: a pub/sub/query protocol unifying data in motion, data at rest and computations"
    license = "Apache-2.0 OR EPL-2.0"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/eclipse-zenoh/zenoh-pico"
    topics = ("networking", "pub-sub", "messaging", "robotics", "ros2", "iot", "edge-computing", "micro-controllers")
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
    languages = ["C"]

    def layout(self):
        cmake_layout(self, src_folder="src")

    def build_requirements(self):
        self.tool_requires("cmake/[^4]")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.cache_variables["BUILD_TESTING"] = False
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    @property
    def _defines_file(self):
        return Path(self.package_folder, "share", "conan", "zenohpico", "defines")

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()

        # Store the CMake defines for package_info()
        # https://github.com/eclipse-zenoh/zenoh-pico/blob/1.3.2/CMakeLists.txt#L166-L210
        content = Path(self.package_folder, "lib", "cmake", "zenohpico", "zenohpicoTargets.cmake").read_text()
        defines = re.search('INTERFACE_COMPILE_DEFINITIONS "(.+?)"', content)[1].split(";")
        save(self, self._defines_file, "\n".join(defines))

        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "zenohpico")
        self.cpp_info.set_property("cmake_target_name", "zenohpico::lib")
        zenohpico_shared = "shared" if self.options.shared else "static"
        self.cpp_info.set_property("cmake_target_aliases", [f"zenohpico::{zenohpico_shared}"])
        self.cpp_info.set_property("pkg_config_name", "zenohpico")

        lib = "zenohpico"
        if self.settings.build_type == "Debug":
            lib += "d"
        self.cpp_info.libs = [lib]
        if self.settings.os in ["Linux", "FreeBSD"]:
            # https://github.com/eclipse-zenoh/zenoh-pico/blob/1.3.2/CMakeLists.txt#L392-L398
            self.cpp_info.system_libs.extend(["pthread", "rt"])
        elif self.settings.os == "Windows":
            # https://github.com/eclipse-zenoh/zenoh-pico/blob/1.3.2/CMakeLists.txt#L400-L403
            self.cpp_info.system_libs.extend(["ws2_32", "iphlpapi"])

        self.cpp_info.defines.extend(filter(None, load(self, self._defines_file).split()))
