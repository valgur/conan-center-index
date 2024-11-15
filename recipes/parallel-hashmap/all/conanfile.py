from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.files import copy, get
from conan.tools.layout import basic_layout
import os

required_conan_version = ">=1.50.0"


class ParallelHashmapConan(ConanFile):
    name = "parallel-hashmap"
    description = "A family of header-only, very fast and memory-friendly hashmap and btree containers."
    license = "Apache-2.0"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/greg7mdp/parallel-hashmap"
    topics = ("parallel", "hashmap", "btree", "header-only")
    package_type = "header-library"
    settings = "os", "arch", "compiler", "build_type"
    no_copy_source = True

    def layout(self):
        basic_layout(self, src_folder="src")

    def package_id(self):
        self.info.clear()

    def validate(self):
        check_min_cppstd(self, 11)

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def package(self):
        copy(self, "LICENSE", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        copy(self, "*.h", src=os.path.join(self.source_folder, "parallel_hashmap"),
                          dst=os.path.join(self.package_folder, "include", "parallel_hashmap"))
        copy(self, "phmap.natvis", src=self.source_folder, dst=os.path.join(self.source_folder, "res"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "phmap")
        self.cpp_info.set_property("cmake_target_name", "phmap")
        self.cpp_info.bindirs = []
        self.cpp_info.libdirs = []
