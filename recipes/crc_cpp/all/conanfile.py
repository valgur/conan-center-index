import os

from conan import ConanFile, tools
from conan.errors import ConanInvalidConfiguration
from conan.tools.files import get, copy
from conan.tools.layout import basic_layout
from conan.tools.microsoft import check_min_vs
from conan.tools.scm import Version

required_conan_version = ">=1.52.0"


class Crc_CppConan(ConanFile):
    name = "crc_cpp"
    description = "A header only constexpr / compile time small-table based CRC library for C++17 and newer"
    license = "MIT"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/AshleyRoll/crc_cpp"
    topics = ("crc_cpp", "crc", "constexpr", "cpp17", "cpp20", "header-only")

    package_type = "header-library"
    settings = "os", "arch", "compiler", "build_type"
    no_copy_source = True

    def layout(self):
        basic_layout(self, src_folder="src")

    def package_id(self):
        self.info.clear()

    @property
    def _supported_compiler(self):
        compiler = str(self.settings.compiler)
        version = Version(self.settings.compiler.version)
        if check_min_vs(self, 191, raise_invalid=False):
            return True
        elif compiler == "gcc" and version >= "9":
            return True
        elif compiler == "clang" and version >= "5":
            return True
        elif compiler == "apple-clang" and version >= "10":
            return True
        else:
            self.output.warning(
                "{} recipe lacks information about the {} compiler standard version support".format(
                    self.name, compiler
                )
            )
        return False

    def validate(self):
        if self.settings.compiler.get_safe("cppstd"):
            tools.build.check_min_cppstd(self, "17")
        if not self._supported_compiler:
            raise ConanInvalidConfiguration(
                "crc_cpp: Unsupported compiler: {}-{} Minimum C++17 constexpr features required.".format(
                    self.settings.compiler, self.settings.compiler.version
                )
            )

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def package(self):
        copy(self, "LICENSE", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder)
        copy(self, "*",
             dst=os.path.join(self.package_folder, "include"),
             src=os.path.join(self.source_folder, "include"))

    def package_info(self):
        self.cpp_info.bindirs = []
        self.cpp_info.libdirs = []
