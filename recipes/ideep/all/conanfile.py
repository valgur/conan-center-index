import os

from conan import ConanFile
from conan.tools.files import *
from conan.tools.layout import basic_layout
from conan.tools.scm import Version

required_conan_version = ">=2.1"


class PackageConan(ConanFile):
    name = "ideep"
    description = "Intel Optimization for Chainer*, a Chainer module providing numpy like API and DNN acceleration using MKL-DNN."
    license = "MIT"
    homepage = "https://github.com/intel/ideep"
    topics = ("intel", "onednn", "oneapi", "dnn", "deep-learning", "chainer")
    package_type = "header-library"
    settings = "os", "arch", "compiler", "build_type"
    no_copy_source = True

    def layout(self):
        basic_layout(self, src_folder="src")

    def requirements(self):
        v = Version(self.version)
        self.requires(f"onednn/[~{v.major}.{v.minor}]")

    def package_id(self):
        self.info.clear()

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        copy(self, "*", os.path.join(self.source_folder, "include"), os.path.join(self.package_folder, "include"))

    def package_info(self):
        self.cpp_info.bindirs = []
        self.cpp_info.libdirs = []
