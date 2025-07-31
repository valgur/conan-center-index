import os

from conan import ConanFile
from conan.tools.files import download, copy
from conan.tools.layout import basic_layout

required_conan_version = ">=2.1"


class GasPreprocessorConan(ConanFile):
    name = "gas-preprocessor"
    description = "Perl script that implements a subset of the GNU as preprocessor that Apple's as doesn't"
    license = "GPL-2.0-or-later"
    homepage = "https://github.com/FFmpeg/gas-preprocessor"
    topics = ("ffmpeg", "preprocessor", "assembler", "arm64")
    package_type = "application"

    def export_sources(self):
        copy(self, "gpl-2.0.txt", self.recipe_folder, os.path.join(self.export_sources_folder, "src"))

    def layout(self):
        basic_layout(self, src_folder="src")

    def source(self):
        download(self, **self.conan_data["sources"][self.version], filename="gas-preprocessor.pl")

    @staticmethod
    def _chmod_plus_x(filename):
        if os.name == "posix":
            os.chmod(filename, os.stat(filename).st_mode | 0o111)

    def package(self):
        # https://github.com/FFmpeg/gas-preprocessor/blob/a120373ba30de06675d8c47617b315beef16c88e/gas-preprocessor.pl#L3
        # GPL-2.0 or later is mentioned in the file itself - we keep a copy of the license file in the recipe
        copy(self, "gpl-2.0.txt", self.source_folder, os.path.join(self.package_folder, "licenses"))
        copy(self, "gas-preprocessor.pl", self.source_folder, os.path.join(self.package_folder, "bin"))
        self._chmod_plus_x(os.path.join(self.package_folder, "bin", "gas-preprocessor.pl"))

    def package_info(self):
        self.cpp_info.includedirs = []
        self.cpp_info.libdirs = []
        self.cpp_info.bindirs = ["bin"]
