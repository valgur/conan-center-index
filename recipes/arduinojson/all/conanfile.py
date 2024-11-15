import os

from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.files import copy, get
from conan.tools.layout import basic_layout
from conan.tools.scm import Version

required_conan_version = ">=1.50.0"


class ArduinojsonConan(ConanFile):
    name = "arduinojson"
    description = "C++ JSON library for IoT. Simple and efficient."
    homepage = "https://github.com/bblanchon/ArduinoJson"
    topics = ("json", "msgpack", "message-pack", "arduino", "iot", "embedded", "esp8266")
    license = "MIT"
    url = "https://github.com/conan-io/conan-center-index"
    package_type = "header-library"
    settings = "os", "arch", "compiler", "build_type"
    no_copy_source = True

    @property
    def _min_cppstd(self):
        return "98" if Version(self.version) < "6.21.0" else "11"

    def layout(self):
        basic_layout(self, src_folder="src")

    def package_id(self):
        self.info.clear()

    def validate(self):
        check_min_cppstd(self, self._min_cppstd)

    def source(self):
        has_arduinojson_root = not ("6.18.2" <= Version(self.version) < "7.0")
        get(self, **self.conan_data["sources"][self.version], strip_root=has_arduinojson_root)

    def build(self):
        pass

    def package(self):
        copy(self, "*LICENSE*", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        copy(self, "*.h", src=os.path.join(self.source_folder, "src"), dst=os.path.join(self.package_folder, "include"))
        copy(self, "*.hpp", src=os.path.join(self.source_folder, "src"), dst=os.path.join(self.package_folder, "include"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "ArduinoJson")
        self.cpp_info.set_property("cmake_target_name", "ArduinoJson")
        self.cpp_info.bindirs = []
        self.cpp_info.libdirs = []
