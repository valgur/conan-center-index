import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout
from conan.tools.files import *
from conan.tools.microsoft import is_msvc

required_conan_version = ">=2.4"


class Id3v2libConan(ConanFile):
    name = "id3v2lib"
    description = "id3v2lib is a library written in C to read and edit id3 tags from mp3 files."
    topics = ("conan", "id3", "tags", "mp3", "container", "media", "audio")
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/larsbs/id3v2lib"
    license = "BSD-2-Clause"
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

    def validate(self):
        # An issue has been opened to discuss supporting MSVC:
        # https://github.com/larsbs/id3v2lib/issues/48
        if is_msvc(self):
            raise ConanInvalidConfiguration("id3v2lib does not support Visual Studio.")

    def layout(self):
        cmake_layout(self, src_folder="src")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        cmake = CMake(self)
        cmake.install()
        copy(self, "LICENSE", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "id3v2lib")
        self.cpp_info.set_property("cmake_target_name", "id3v2lib::id3v2lib")
        self.cpp_info.set_property("pkg_config_name", "id3v2lib")
        self.cpp_info.libs = ["id3v2lib"]
