from conan import ConanFile
from conan.tools.files import copy, get
from conan.tools.layout import basic_layout
import os

required_conan_version = ">=2.1"


class CppZmqConan(ConanFile):
    name = "cppzmq"
    description = "C++ binding for 0MQ"
    homepage = "https://github.com/zeromq/cppzmq"
    license = "MIT"
    topics = ("zmq-cpp", "zmq", "cpp-bind")
    url = "https://github.com/conan-io/conan-center-index"
    package_type = "header-library"
    settings = "os", "arch", "compiler", "build_type"
    no_copy_source = True

    def layout(self):
        basic_layout(self, src_folder="src")

    def requirements(self):
        self.requires("zeromq/4.3.5")

    def package_id(self):
        self.info.clear()

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def build(self):
        pass

    def package(self):
        copy(self, "LICENSE", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        copy(self, "zmq*.hpp", src=self.source_folder, dst=os.path.join(self.package_folder, "include"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "cppzmq")
        # cppzmq has 2 weird official CMake imported targets:
        # - cppzmq if cppzmq depends on shared zeromq
        # - cppzmq-static if cppzmq depends on static zeromq
        self.cpp_info.set_property("cmake_target_name", "cppzmq")
        self.cpp_info.set_property("cmake_target_aliases", ["cppzmq-static"])
        self.cpp_info.bindirs = []
        self.cpp_info.libdirs = []
