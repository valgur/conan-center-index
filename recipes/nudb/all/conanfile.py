# TODO: verify the Conan v2 migration

import os

from conan import ConanFile
from conan.tools.files import copy, get

required_conan_version = ">=1.52.0"


class NudbConan(ConanFile):
    name = "nudb"
    description = "A fast key/value insert-only database for SSD drives in C++11"
    license = "BSL-1.0"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/CPPAlliance/NuDB"
    topics = ("header-only", "KVS", "insert-only")

    package_type = "header-library"
    settings = "os", "arch", "compiler", "build_type"
    no_copy_source = True
    no_copy_source = True

    def layout(self):
        pass

    def requirements(self):
        self.requires("boost/1.78.0")

    def package_id(self):
        self.info.clear()

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def package(self):
        copy(self, "LICENSE*", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder)
        copy(self, "*.hpp", dst=self.package_folder, src=os.path.join(self.source_folder, "include"))
        copy(self, "*.ipp", dst=self.package_folder, src=os.path.join(self.source_folder, "include"))

    def package_info(self):
        self.cpp_info.bindirs = []
        self.cpp_info.libdirs = []
        self.cpp_info.names["cmake_find_package"] = "NuDB"
        self.cpp_info.names["cmake_find_package_multi"] = "NuDB"
        self.cpp_info.components["core"].names["cmake_find_package"] = "nudb"
        self.cpp_info.components["core"].names["cmake_find_package_multi"] = "nudb"
        self.cpp_info.components["core"].requires = ["boost::thread", "boost::system"]
        self.cpp_info.set_property("cmake_target_name", "NuDB")
        self.cpp_info.set_property("cmake_target_module_name", "NuDB::nudb")
        self.cpp_info.set_property("cmake_find_module", "both")
