import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration, ConanException
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *
from conan.tools.microsoft import is_msvc
from conan.tools.scm import Version

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
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "utf8": False,
    }
    implements = ["auto_shared_fpic"]

    @property
    def _with_xxd(self):
        # FIXME: create conan recipe for xxd, and use it unconditionally (returning False means cross build doesn't work)
        return self.settings.os != "Windows"

    def layout(self):
        cmake_layout(self, src_folder="src")

    def validate(self):
        check_min_cppstd(self, 11)
        if self.info.options.shared and is_msvc(self):
            raise ConanInvalidConfiguration(f"{self.ref} shared not supported with Visual Studio")

    def build_requirements(self):
        # FIXME: add unconditional xxd build requirement
        pass

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        if Version(self.version) >= "0.9":
            tc.variables["LITEHTML_BUILD_TESTING"] = False
        else:
            tc.variables["BUILD_TESTING"] = False
        tc.variables["LITEHTML_UTF8"] = self.options.utf8
        tc.variables["EXTERNAL_GUMBO"] = False # FIXME: add cci recipe, and use it unconditionally (option value should be True)
        tc.variables["EXTERNAL_XXD"] = self._with_xxd  # FIXME: should be True unconditionally
        tc.cache_variables["CMAKE_POLICY_VERSION_MINIMUM"] = "3.15" # CMake 4 support
        if Version(self.version) > "0.9":
            raise ConanException("CMAKE_POLICY_VERSION_MINIMUM hardcoded to 3.5, check if new version supports CMake 4")
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

        if True: # FIXME: remove once we use a vendored gumbo library
            self.cpp_info.components["gumbo"].set_property("cmake_target_name", "gumbo")
            self.cpp_info.components["gumbo"].libs = ["gumbo"]
