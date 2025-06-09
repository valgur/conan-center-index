import os
import stat
import textwrap

from conan import ConanFile
from conan.tools.files import *
from conan.tools.layout import basic_layout

required_conan_version = ">=2.1"


class Antlr4Conan(ConanFile):
    name = "antlr4"
    description = "powerful parser generator for reading, processing, executing, or translating structured text or binary files."
    license = "BSD-3-Clause"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/antlr/antlr4"
    topics = ("parser", "generator")
    package_type = "application"
    settings = "os", "arch", "compiler", "build_type"

    def layout(self):
        basic_layout(self, src_folder="src")

    def requirements(self):
        self.requires("openjdk/21.0.1")

    def package_id(self):
        del self.info.settings.arch
        del self.info.settings.compiler
        del self.info.settings.build_type

    def source(self):
        info = self.conan_data["sources"][self.version]
        download(self, **info["jar"], filename=os.path.join(self.source_folder, "antlr-complete.jar"))
        download(self, **info["license"], filename=os.path.join(self.source_folder, "LICENSE.txt"))

    def package(self):
        copy(self, "LICENSE.txt", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder)
        copy(self, "antlr-complete.jar", dst=os.path.join(self.package_folder, "share", "java"), src=self.source_folder)
        if self.settings.os == "Windows":
            save(self, os.path.join(self.package_folder, "bin", "antlr4.bat"), textwrap.dedent("""\
                 java -classpath %CLASSPATH% org.antlr.v4.Tool %*
             """))
        else:
            bin_path = os.path.join(self.package_folder, "bin", "antlr4")
            save(self, bin_path, textwrap.dedent("""\
                 #!/bin/bash
                 java -classpath $CLASSPATH org.antlr.v4.Tool $@
             """))
            st = os.stat(bin_path)
            os.chmod(bin_path, st.st_mode | stat.S_IEXEC)

    def package_info(self):
        self.cpp_info.frameworkdirs = []
        self.cpp_info.libdirs = []
        self.cpp_info.includedirs = []
        self.cpp_info.resdirs = ["share"]

        jar = os.path.join(self.package_folder, "share", "java", "antlr-complete.jar")
        self.runenv_info.prepend_path("CLASSPATH", jar)
