from conan import ConanFile
from conan.tools.files import get, copy
from conan.tools.layout import basic_layout
from conan.tools.scm import Version
import os

required_conan_version = ">=2.1"

class MsgpackCXXConan(ConanFile):
    name = "msgpack-cxx"
    description = "The official C++ library for MessagePack"
    license = "BSL-1.0"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/msgpack/msgpack-c"
    topics = ("msgpack", "message-pack", "serialization", "header-only")
    package_type = "header-library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "use_boost": [True, False],
    }
    default_options = {
        "use_boost": True,
    }
    no_copy_source = True

    def config_options(self):
        # Boost was not optional until 4.1.0
        if Version(self.version) < "4.1.0":
            del self.options.use_boost

    def layout(self):
        basic_layout(self, src_folder="src")

    def requirements(self):
        # Boost was not optional until 4.1.0
        if self.options.get_safe("use_boost", True):
            self.requires("boost/1.86.0")

    def package_id(self):
        self.info.clear()

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def package(self):
        copy(self, "LICENSE_1_0.txt", self.source_folder, os.path.join(self.package_folder, "licenses"))
        copy(self, "*.h", os.path.join(self.source_folder, "include"), os.path.join(self.package_folder, "include"))
        copy(self, "*.hpp", os.path.join(self.source_folder, "include"), os.path.join(self.package_folder, "include"))

    def package_info(self):
        if Version(self.version) > "6.1.1":
            self.cpp_info.set_property("cmake_file_name", "msgpack-cxx")
        else:
            # The README is wrong, the correct name is msgpack-cxx,
            # but keep it for old published versions not to break the consumers
            self.cpp_info.set_property("cmake_file_name", "msgpack")

        if Version(self.version) >= "6.0.0":
            self.cpp_info.set_property("cmake_target_name", "msgpack-cxx")
        else:
            self.cpp_info.set_property("cmake_target_name", "msgpackc-cxx")

        self.cpp_info.libdirs = []
        self.cpp_info.bindirs = []

        if Version(self.version) >= "4.1.0" and not self.options.use_boost:
            self.cpp_info.defines.append("MSGPACK_NO_BOOST")
        else:
            self.cpp_info.requires.append("boost::headers")
