import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import check_min_cppstd
from conan.tools.files import copy, get
from conan.tools.layout import basic_layout
from conan.tools.microsoft import is_msvc
from conan.tools.scm import Version

required_conan_version = ">=1.47.0"


class PlatformInterfacesConan(ConanFile):
    name = "platform.hashing"
    description = (
        "platform.hashing is one of the libraries of the LinksPlatform modular framework, "
        "which contains std::hash specializations for:\n"
        " - trivial and standard-layout types\n"
        " - types constrained by std::ranges::range\n"
        " - std::any"
    )
    license = "LGPL-3.0-only"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/linksplatform/Hashing"
    topics = ("linksplatform", "cpp20", "hashing", "any", "ranges", "native", "header-only")

    package_type = "header-library"
    settings = "os", "arch", "compiler", "build_type"
    no_copy_source = True

    @property
    def _minimum_cpp_standard(self):
        return 20

    @property
    def _compilers_minimum_version(self):
        return {
            "gcc": "10",
            "Visual Studio": "16",
            "clang": "14",
            "apple-clang": "14",
        }

    def layout(self):
        basic_layout(self, src_folder="src")

    def package_id(self):
        self.info.clear()

    def validate(self):
        minimum_version = self._compilers_minimum_version.get(str(self.settings.compiler))

        if not minimum_version:
            self.output.warning(f"{self.name} recipe lacks information about the {self.settings.compiler} compiler support.")

        elif Version(self.settings.compiler.version) < minimum_version:
            raise ConanInvalidConfiguration(
                f"{self.name}/{self.version} requires c++{self._minimum_cpp_standard}, which is not supported"
                f" by {self.settings.compiler} {self.settings.compiler.version}."
            )

        if self.settings.compiler.get_safe("cppstd"):
            check_min_cppstd(self, self._minimum_cpp_standard)

        if self.settings.arch in ("x86",):
            raise ConanInvalidConfiguration(f"{self.name} does not support arch={self.settings.arch}")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    @property
    def _internal_cpp_subfolder(self):
        return os.path.join(self.source_folder, "cpp", "Platform.Hashing")

    def package(self):
        copy(self, "*.h", dst=os.path.join(self.package_folder, "include"), src=self._internal_cpp_subfolder)
        copy(self, "LICENSE", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder)

    def package_info(self):
        self.cpp_info.libdirs = []
        suggested_flags = ""
        if not is_msvc(self):
            suggested_flags = {
                "x86_64": "-march=haswell",
                "armv7": "-march=armv7",
                "armv8": "-march=armv8-a",
            }.get(str(self.settings.arch), "")
        self.conf_info.define("user.platform.hashing:suggested_flags", suggested_flags)

        if "-march" not in "{} {}".format(os.environ.get("CPPFLAGS", ""), os.environ.get("CXXFLAGS", "")):
            self.output.warning(
                "platform.hashing needs to have `-march=ARCH` added to CPPFLAGS/CXXFLAGS. "
                f"A suggestion is available in deps_user_info[{self.name}].suggested_flags."
            )

        # TODO: to remove in conan v2
        self.user_info.suggested_flags = suggested_flags
