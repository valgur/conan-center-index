import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *
from conan.tools.microsoft import is_msvc

required_conan_version = ">=2.1"


class LitehtmlConan(ConanFile):
    name = "litehtml"
    description = "litehtml is the lightweight HTML rendering engine with CSS2/CSS3 support."
    license = "BSD-3-Clause"
    topics = ("render engine", "html", "parser")
    homepage = "https://github.com/litehtml/litehtml"
    url = "https://github.com/conan-io/conan-center-index"

    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "utf8": [True, False],
        "with_icu": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "utf8": False,
        "with_icu": False,
    }

    @property
    def _with_xxd(self):
        # FIXME: create conan recipe for xxd, and use it unconditionally (returning False means cross build doesn't work)
        return self.settings.os != "Windows"

    def export_sources(self):
        export_conandata_patches(self)

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC
        if self.version != "cci.20211028":
            del self.options.with_icu

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        # FIXME: add gumbo requirement (it is vendored right now)
        if self.options.get_safe("with_icu"):
            self.requires("icu/75.1")

    def validate(self):
        check_min_cppstd(self, 11)
        if self.info.options.shared and is_msvc(self):
            raise ConanInvalidConfiguration(f"{self.ref} shared not supported with Visual Studio")

    def build_requirements(self):
        # FIXME: add unconditional xxd build requirement
        pass

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        apply_conandata_patches(self)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["BUILD_TESTING"] = False
        tc.variables["LITEHTML_UTF8"] = self.options.utf8
        tc.variables["USE_ICU"] = self.options.get_safe("with_icu", False)
        tc.variables["EXTERNAL_GUMBO"] = False # FIXME: add cci recipe, and use it unconditionally (option value should be True)
        tc.variables["EXTERNAL_XXD"] = self._with_xxd  # FIXME: should be True unconditionally
        tc.generate()
        deps = CMakeDeps(self)
        deps.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "litehtml")
        self.cpp_info.set_property("cmake_target_name", "litehtml")

        self.cpp_info.components["litehtml_litehtml"].set_property("cmake_target_name", "litehtml")
        self.cpp_info.components["litehtml_litehtml"].libs = ["litehtml"]
        self.cpp_info.components["litehtml_litehtml"].requires = ["gumbo"]
        if self.options.get_safe("with_icu"):
            self.cpp_info.components["litehtml_litehtml"].requires.append("icu::icu")

        if True: # FIXME: remove once we use a vendored gumbo library
            self.cpp_info.components["gumbo"].set_property("cmake_target_name", "gumbo")
            self.cpp_info.components["gumbo"].libs = ["gumbo"]
