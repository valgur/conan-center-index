import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeToolchain, CMakeDeps, cmake_layout
from conan.tools.files import *
from conan.tools.scm import Version

required_conan_version = ">=2.1"


class SQLiteCppConan(ConanFile):
    name = "sqlitecpp"
    description = "SQLiteCpp is a smart and easy to use C++ sqlite3 wrapper"
    license = "MIT"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/SRombauts/SQLiteCpp"
    topics = ("sqlite", "sqlite3", "data-base")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "stack_protection": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "stack_protection": True,
    }
    implements = ["auto_shared_fpic"]

    def export_sources(self):
        export_conandata_patches(self)

    def requirements(self):
        self.requires("sqlite3/[>=3.45.0 <4]")

    def validate(self):
        if Version(self.version) >= "3.0.0":
            check_min_cppstd(self, 11)
        if self.info.settings.os == "Windows" and self.info.options.shared:
            raise ConanInvalidConfiguration("SQLiteCpp cannot be built as shared lib on Windows")

    def layout(self):
        cmake_layout(self, src_folder="src")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        apply_conandata_patches(self)

    def _patch_sources(self):
        if self.settings.compiler == "clang" and \
           Version(self.settings.compiler.version) < "6.0" and \
                 self.settings.compiler.libcxx == "libc++" and \
                 Version(self.version) < "3":
            replace_in_file(self,
                os.path.join(self.source_folder, "include", "SQLiteCpp", "Utils.h"),
                "const nullptr_t nullptr = {};",
                "")

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["SQLITECPP_INTERNAL_SQLITE"] = False
        tc.variables["SQLITECPP_RUN_CPPLINT"] = False
        tc.variables["SQLITECPP_RUN_CPPCHECK"] = False
        tc.variables["SQLITECPP_RUN_DOXYGEN"] = False
        tc.variables["SQLITECPP_BUILD_EXAMPLES"] = False
        tc.variables["SQLITECPP_BUILD_TESTS"] = False
        tc.variables["SQLITECPP_USE_STACK_PROTECTION"] = self.options.stack_protection
        tc.generate()

        tc = CMakeDeps(self)
        tc.generate()

    def build(self):
        self._patch_sources()
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE.txt", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))
        rmdir(self, os.path.join(self.package_folder, "share"))

    @property
    def _is_mingw(self):
        return self.settings.os == "Windows" and self.settings.compiler == "gcc"

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "SQLiteCpp")
        self.cpp_info.set_property("cmake_target_name", "SQLiteCpp")
        self.cpp_info.libs = ["SQLiteCpp"]
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs = ["pthread", "dl", "m"]

        if self._is_mingw:
            self.cpp_info.system_libs = ["ssp"]
