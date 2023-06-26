# TODO: verify the Conan v2 migration

import os

from conan import ConanFile
from conan.tools.files import copy, download

required_conan_version = ">=1.47.0"


class Djinni(ConanFile):
    name = "djinni-generator"
    description = "Djinni is a tool for generating cross-language type declarations and interface bindings."
    license = "Apache-2.0"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://djinni.xlcpp.dev"
    topics = ("java", "Objective-C", "ios", "Android", "pre-built")

    package_type = "application"
    settings = "os", "arch", "compiler", "build_type"

    def layout(self):
        pass

    def package_id(self):
        del self.info.settings.compiler
        del self.info.settings.build_type

    def source(self):
        filename = os.path.basename(self.conan_data["sources"][self.version]["url"])
        download(self, filename=filename, **self.conan_data["sources"][self.version])
        download(
            self,
            filename="LICENSE",
            url="https://raw.githubusercontent.com/cross-language-cpp/djinni-generator/main/LICENSE",
        )

    def build(self):
        pass

    def package(self):
        if self.settings.os == "Windows":
            os.rename("djinni", "djinni.bat")
            copy(self, "djinni.bat", dst=os.path.join(self.package_folder, "bin"), keep_path=False)
        else:
            copy(self, "djinni", dst=os.path.join(self.package_folder, "bin"), keep_path=False)
            executable = os.path.join(self.package_folder, "bin", "djinni")
            os.chmod(executable, os.stat(executable).st_mode | 0o111)
        copy(self, "LICENSE", dst=os.path.join(self.package_folder, "licenses"), keep_path=False)

    def package_info(self):
        self.cpp_info.frameworkdirs = []
        self.cpp_info.libdirs = []
        self.cpp_info.resdirs = []
        self.cpp_info.includedirs = []
        self.env_info.PATH.append(os.path.join(self.package_folder, "bin"))
