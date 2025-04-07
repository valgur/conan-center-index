from conan import ConanFile
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout
from conan.tools.files import copy, get, rmdir
import os

required_conan_version = ">=2.1"


class CerealConan(ConanFile):
    name = "cereal"
    description = "Serialization header-only library for C++11."
    license = "BSD-3-Clause"
    topics = ("header-only", "serialization", "cpp11")
    homepage = "https://github.com/USCiLab/cereal"
    url = "https://github.com/conan-io/conan-center-index"
    package_type = "header-library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "thread_safe": [True, False],
    }
    default_options = {
        "thread_safe": False,
    }

    def layout(self):
        cmake_layout(self, src_folder="src")

    def package_id(self):
        self.info.clear()

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["JUST_INSTALL_CEREAL"] = True
        tc.variables["CEREAL_INSTALL"] = True
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()

        # The "share" folder was being removed up to and including version 1.3.0.
        # The module files were moved to lib/cmake from 1.3.1 on, so now removing both
        # as to avoid breaking versions < 1.3.1
        rmdir(self, os.path.join(self.package_folder, "share"))
        rmdir(self, os.path.join(self.package_folder, "lib"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "cereal")
        self.cpp_info.set_property("cmake_target_name", "cereal::cereal")
        self.cpp_info.set_property("cmake_target_aliases", ["cereal"]) # target before 1.3.1
        self.cpp_info.bindirs = []
        self.cpp_info.libdirs = []
        if self.options.thread_safe:
            self.cpp_info.defines = ["CEREAL_THREAD_SAFE=1"]
            if self.settings.os in ["Linux", "FreeBSD"]:
                self.cpp_info.system_libs.append("pthread")
