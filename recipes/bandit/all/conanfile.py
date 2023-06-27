from conan import ConanFile
from conan.tools.files import apply_conandata_patches, copy, get
from conan.tools.layout import basic_layout
import os

required_conan_version = ">=1.52.0"


class BanditConan(ConanFile):
    name = "bandit"
    description = "Human-friendly unit testing for C++11"
    license = "MIT"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/banditcpp/bandit"
    topics = ("testing", "header-only")

    package_type = "header-library"
    settings = "os", "arch", "compiler", "build_type"
    no_copy_source = True

    def export_sources(self):
        for p in self.conan_data.get("patches", {}).get(self.version, []):
            copy(self, p["patch_file"], self.recipe_folder, self.export_sources_folder)

    def layout(self):
        basic_layout(self)

    def requirements(self):
        self.requires("snowhouse/5.0.0")

    def package_id(self):
        self.info.clear()

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def build(self):
        apply_conandata_patches(self)

    def package(self):
        copy(
            self,
            "LICENSE.txt",
            src=os.path.join(self.source_folder, "docs"),
            dst=os.path.join(self.package_folder, "licenses"),
        )
        copy(
            self,
            pattern="*",
            dst=os.path.join(self.package_folder, "include", "bandit"),
            src=os.path.join(self.source_folder, "bandit"),
        )

    def package_info(self):
        self.cpp_info.bindirs = []
        self.cpp_info.frameworkdirs = []
        self.cpp_info.libdirs = []
        self.cpp_info.resdirs = []
