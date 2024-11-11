from conan import ConanFile
from conan.tools.files import copy, get
from conan.tools.layout import basic_layout
import os

required_conan_version = ">=1.50.0"


class UtfCppConan(ConanFile):
    name = "utfcpp"
    description = "UTF-8 with C++ in a Portable Way"
    license = "BSL-1.0"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/nemtrif/utfcpp"
    topics = ("utf", "utf8", "unicode", "text", "header-only")
    package_type = "header-library"
    settings = "os", "arch", "compiler", "build_type"
    no_copy_source = True

    def layout(self):
        basic_layout(self, src_folder="src")

    def package_id(self):
        self.info.clear()

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def package(self):
        copy(self, "LICENSE", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        copy(self, "*.h", src=os.path.join(self.source_folder, "source"),
                          dst=os.path.join(self.package_folder, "include", "utf8cpp"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "utf8cpp")
        self.cpp_info.set_property("cmake_target_name", "utf8cpp")
        self.cpp_info.set_property("cmake_target_aliases", ["utf8::cpp"])
        self.cpp_info.includedirs.append(os.path.join("include", "utf8cpp"))
        self.cpp_info.bindirs = []
        self.cpp_info.libdirs = []
