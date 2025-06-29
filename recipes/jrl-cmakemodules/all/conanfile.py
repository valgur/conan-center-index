import os

from conan import ConanFile
from conan.tools.files import *
from conan.tools.layout import basic_layout

required_conan_version = ">=2.1"


class JrlCMakeModulesConan(ConanFile):
    name = "jrl-cmakemodules"
    description = "Shared CMake submodule for any project from CNRS LAAS/HPP or JRL."
    license = "LGPL-3.0-or-later AND GPL-3.0-or-later"
    homepage = "https://github.com/jrl-umi3218/jrl-cmakemodules"
    topics = ("cmake", "robotics")
    package_type = "build-scripts"
    settings = "os", "arch", "compiler", "build_type"
    no_copy_source = True

    def export_sources(self):
        export_conandata_patches(self)

    def layout(self):
        basic_layout(self, src_folder="src")

    def build_requirements(self):
        self.tool_requires("cmake/[>=3.22 <5]", visible=True)

    def package_id(self):
        self.info.clear()

    def source(self):
        get(self, **self.conan_data["sources"][self.version]["cmake"], strip_root=True)
        rmdir(self, "stubgen")
        get(self, **self.conan_data["sources"][self.version]["stubgen"], strip_root=True, destination="stubgen")
        apply_conandata_patches(self)
        rmdir(self, ".github")
        rmdir(self, ".docs")
        rmdir(self, "_unittests")
        rm(self, ".*", self.source_folder)

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        copy(self, "*", self.source_folder, os.path.join(self.package_folder, "share", self.name))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "jrl-cmakemodules")
        self.cpp_info.set_property("cmake_target_name", "jrl-cmakemodules::jrl-cmakemodules")
        self.cpp_info.bindirs = []
        self.cpp_info.libdirs = []
        self.cpp_info.includedirs = [os.path.join("share", self.name)]
        self.cpp_info.builddirs = [os.path.join("share", self.name)]
