import os

from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.files import *
from conan.tools.layout import basic_layout

required_conan_version = ">=2.1"


class DynologConan(ConanFile):
    name = "dynolog"
    description = "Development header files of Dynolog - a telemetry daemon for performance monitoring and tracing."
    license = "MIT"
    homepage = "https://github.com/facebookincubator/dynolog"
    topics = ("performance-monitoring", "profiling", "cpu-metrics", "gpu-monitoring", "system-monitoring", "facebook", "header-only")
    package_type = "header-library"
    settings = "os", "arch", "compiler", "build_type"

    def layout(self):
        basic_layout(self, src_folder="src")

    def requirements(self):
        self.requires("glog/[>=0.6 <1]")

    def validate(self):
        check_min_cppstd(self, 17)

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        copy(self, "*.h",
             os.path.join(self.source_folder, "dynolog", "src"),
             os.path.join(self.package_folder, "include", "dynolog", "src"))

    def package_info(self):
        self.cpp_info.bindirs = []
        self.cpp_info.libdirs = []
