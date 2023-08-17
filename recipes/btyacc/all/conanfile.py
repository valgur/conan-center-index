import os
import textwrap

from conan import ConanFile
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import copy, get, rmdir, save

required_conan_version = ">=1.52.0"


class BtyaccConan(ConanFile):
    name = "btyacc"
    description = "Backtracking yacc"
    license = "Unlicense"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/ChrisDodd/btyacc"
    topics = ("yacc", "parser", "header-only")

    package_type = "application"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "fPIC": [True, False],
    }
    default_options = {
        "fPIC": True,
    }
    no_copy_source = True

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        self.settings.rm_safe("compiler.libcxx")
        self.settings.rm_safe("compiler.cppstd")

    def layout(self):
        cmake_layout(self, src_folder="src")

    def package_id(self):
        self.info.clear()

    def source(self):
        root = self.source_folder
        get_args = self.conan_data["sources"][self.version]
        get(self, **get_args, destination=root, strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.generate()
        tc = CMakeDeps(self)
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    @property
    def _variables(self):
        return os.path.join("bin", "conan-official-btyacc-variables.cmake")

    def package(self):
        copy(self, "README",
             src=os.path.join(self.source.folder, "licenses"),
             dst=self.source_folder)
        copy(self, "README.BYACC",
             src=os.path.join(self.source.folder, "licenses"),
             dst=self.source_folder)
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "share"))
        variables = os.path.join(self.package_folder, self._variables)
        content = textwrap.dedent("""\
            set(BTYACC_EXECUTABLE "${CMAKE_CURRENT_LIST_DIR}/btyacc")
            if(NOT EXISTS "${BTYACC_EXECUTABLE}")
              set(BTYACC_EXECUTABLE "${BTYACC_EXECUTABLE}.exe")
            endif()
        """)
        save(self, variables, content)

    def package_info(self):
        self.cpp_info.includedirs = []
        self.cpp_info.frameworkdirs = []
        self.cpp_info.libdirs = []
        self.cpp_info.resdirs = []

        bindir = os.path.join(self.package_folder, "bin")
        self.cpp_info.bindirs = [bindir]
        self.output.info(f"Appending PATH environment variable: {bindir}")
        self.env_info.PATH.append(bindir)
        self.cpp_info.build_modules["cmake"] = [self._variables]
        self.cpp_info.build_modules["cmake_find_package"] = [self._variables]
        self.cpp_info.build_modules["cmake_find_package_multi"] = [self._variables]
        self.cpp_info.builddirs = ["bin"]
