import os

from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.files import *
from conan.tools.layout import basic_layout

required_conan_version = ">=2.1"


class GtsamGnssPackage(ConanFile):
    name = "gtsam_gnss"
    description = "Factor graph optimization library for GNSS positioning"
    license = "MIT"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/taroz/gtsam_gnss"
    topics = ("gps", "gnss", "fgo", "factor-graph", "robotics", "gtsam")
    package_type = "header-library"
    settings = "os", "arch", "compiler", "build_type"
    no_copy_source = True

    def layout(self):
        basic_layout(self, src_folder="src")

    def requirements(self):
        self.requires("gtsam/4.3-pre.20250201")

    def package_id(self):
        self.info.clear()

    def validate(self):
        check_min_cppstd(self, 17)

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        copy(self, "*.h",
             os.path.join(self.source_folder, "src"),
             os.path.join(self.package_folder, "include", "gtsam_gnss"),
             keep_path=True)

    def package_info(self):
        self.cpp_info.bindirs = []
        self.cpp_info.libdirs = []
