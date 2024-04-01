import os

from conan import ConanFile
from conan.tools.files import copy, download

required_conan_version = ">=1.53.0"


class SuiteSparseConan(ConanFile):
    name = "suitesparse"
    description = "SuiteSparse: a suite of sparse matrix algorithms"
    license = "GPL-2.0-or-later AND GPL-3.0-only AND LGPL-2.1-or-later AND BSD-2-Clause AND BSD-3-Clause AND Apache-2.0"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://people.engr.tamu.edu/davis/suitesparse.html"
    topics = ("graph-algorithms", "mathematics", "sparse-matrix", "linear-algebra")

    package_type = "header-library"
    settings = "os", "arch", "compiler", "build_type"

    def package_id(self):
        self.info.clear()

    def requirements(self):
        self.requires("suitesparse-amd/3.3.2")
        self.requires("suitesparse-btf/2.3.2")
        self.requires("suitesparse-camd/3.3.2")
        self.requires("suitesparse-ccolamd/3.3.3")
        self.requires("suitesparse-cholmod/5.2.1")
        self.requires("suitesparse-colamd/3.3.3")
        self.requires("suitesparse-config/7.7.0")
        self.requires("suitesparse-cxsparse/4.4.0")
        self.requires("suitesparse-graphblas/9.1.0")
        self.requires("suitesparse-klu/2.3.3")
        self.requires("suitesparse-lagraph/1.1.3")
        self.requires("suitesparse-ldl/3.3.2")
        self.requires("suitesparse-mongoose/3.3.3")
        self.requires("suitesparse-paru/0.1.3")
        self.requires("suitesparse-rbio/4.3.2")
        self.requires("suitesparse-spex/3.1.0")
        self.requires("suitesparse-spqr/4.3.3")
        self.requires("suitesparse-umfpack/6.3.3")

    def source(self):
        download(self, **self.conan_data["sources"][self.version]["license"], filename="LICENSE.txt")

    def package(self):
        copy(self, "LICENSE.txt", self.source_folder, os.path.join(self.package_folder, "licenses"))

    def package_info(self):
        # Unofficial targets
        self.cpp_info.set_property("cmake_file_name", "SuiteSparse")
        self.cpp_info.set_property("cmake_target_name", "SuiteSparse::SuiteSparse")
        self.cpp_info.set_property("pkg_config_name", "SuiteSparse")

        self.cpp_info.bindirs = []
        self.cpp_info.libdirs = []
        self.cpp_info.includedirs = []
        self.cpp_info.frameworkdirs = []
