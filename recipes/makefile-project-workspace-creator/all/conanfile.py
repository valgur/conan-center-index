# TODO: verify the Conan v2 migration

import os

from conan import ConanFile
from conan.tools.files import copy, get

required_conan_version = ">=1.47.0"


class MPCGeneratorConan(ConanFile):
    name = "makefile-project-workspace-creator"
    description = "The Makefile, Project and Workspace Creator"
    license = "BSD-3-Clause"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://objectcomputing.com/"
    topics = ("objectcomputing", "installer", "pre-built")

    package_type = "application"
    settings = "os", "arch", "compiler", "build_type"

    def layout(self):
        pass

    def requirements(self):
        if self.settings.os == "Windows":
            self.requires("strawberryperl/5.30.0.1")

    def package_id(self):
        del self.info.settings.compiler
        del self.info.settings.build_type

    def build(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def package(self):
        copy(self, pattern="*", src=self.source_folder, dst=os.path.join(self.package_folder, "bin"))
        copy(
            self,
            pattern="LICENSE",
            src=os.path.join(self.source_folder, "docs"),
            dst=os.path.join(self.package_folder, "licenses"),
        )

    def package_info(self):
        self.cpp_info.frameworkdirs = []
        self.cpp_info.libdirs = []
        self.cpp_info.resdirs = []
        self.cpp_info.includedirs = []
        bin_path = os.path.join(self.package_folder, "bin")
        self.output.info(f"Appending PATH environment variable: {bin_path}")
        self.env_info.PATH.append(bin_path)
        self.env_info.MPC_ROOT = bin_path
