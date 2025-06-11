import os

from conan import ConanFile
from conan.tools.apple import fix_apple_shared_install_name
from conan.tools.build import cross_building
from conan.tools.cmake import CMakeToolchain, CMake, cmake_layout
from conan.tools.env import VirtualRunEnv
from conan.tools.files import *
from conan.tools.gnu import Autotools, AutotoolsToolchain

required_conan_version = ">=2.4"


class TreConan(ConanFile):
    name = "tre"
    description = "TRE is a lightweight, robust, and efficient POSIX-compliant regexp matching library with some exciting features such as approximate (fuzzy) matching."
    license = "BSD-2-Clause"
    homepage = "https://github.com/laurikari/tre"
    url = "https://github.com/conan-io/conan-center-index"
    topics = "regex", "fuzzy matching"

    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "i18n": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "i18n": False,
    }
    implements = ["auto_shared_fpic"]
    languages = ["C"]

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")
        if self.settings.os == "Windows":
            del self.options.i18n

    def export_sources(self):
        copy(self, "CMakeLists.txt", src=self.recipe_folder, dst=self.export_sources_folder)

    def layout(self):
        cmake_layout(self, src_folder="src")

    def build_requirements(self):
        if self.settings.os != "Windows":
            self.tool_requires("libtool/[^2.4.7]")
        if self.options.get_safe("i18n"):
            self.tool_requires("gettext/[>=0.21 <1]")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        if self.settings.os == "Windows":
            tc = CMakeToolchain(self)
            tc.generate()
        else:
            if not cross_building(self):
                env = VirtualRunEnv(self)
                env.generate(scope="build")
            tc = AutotoolsToolchain(self)
            tc.generate()

    def _patch_sources(self):
        if not self.options.i18n:
            replace_in_file(self, os.path.join(self.source_folder, "configure.ac"), "AM_GNU_GETTEXT", "# AM_GNU_GETTEXT")
            replace_in_file(self, os.path.join(self.source_folder, "configure.ac"), "po/Makefile.in", "")
            replace_in_file(self, os.path.join(self.source_folder, "Makefile.am"), " po ", " ")
        replace_in_file(self, os.path.join(self.source_folder, "Makefile.am"), " tests ", " ")

    def build(self):
        if self.settings.os == "Windows":
            copy(self, "CMakeLists.txt", src=self.export_sources_folder, dst=self.source_folder)
            cmake = CMake(self)
            cmake.configure()
            cmake.build()
        else:
            self._patch_sources()
            autotools = Autotools(self)
            autotools.autoreconf()
            autotools.configure()
            autotools.make()

    def package(self):
        copy(self, "LICENSE", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder)
        if self.settings.os == "Windows":
            cmake = CMake(self)
            cmake.install()
        else:
            autotools = Autotools(self)
            autotools.install()
            rm(self, "*.la", os.path.join(self.package_folder, "lib"))
            rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))
            rmdir(self, os.path.join(self.package_folder, "share", "man"))
            fix_apple_shared_install_name(self)

    def package_info(self):
        self.cpp_info.set_property("pkg_config_name", "tre")
        self.cpp_info.libs = ["tre"]
        if self.options.get_safe("i18n"):
            self.cpp_info.resdirs = ["share"]
