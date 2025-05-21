import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout
from conan.tools.files import *
from conan.tools.microsoft import is_msvc

required_conan_version = ">=2.1"


class LlvmLibunwindConan(ConanFile):
    name = "llvm-libunwind"
    description = "LLVM implementation of the interface defined by the HP libunwind project."
    license = "Apache-2.0 WITH LLVM-exception"
    topics = ("llvm", "unwind", "debuggers", "exception-handling", "introspection", "setjmp")
    homepage = "https://github.com/llvm/llvm-project/tree/main/libunwind"
    url = "https://github.com/conan-io/conan-center-index"
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "baremetal": [True, False],
        "threads": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "baremetal": False,
        "threads": True,
    }
    implements = ["auto_shared_fpic"]

    def layout(self):
        cmake_layout(self, src_folder="src")

    def build_requirements(self):
        self.tool_requires("cmake/[>=3.20 <5]")

    def validate(self):
        if is_msvc(self):
            raise ConanInvalidConfiguration(
                "MSVC is not supported - libunwind is tied to the Itanium C++ ABI and is not compatible with MS C++ ABI."
            )
        check_min_cppstd(self, 17)

    def source(self):
        sources = self.conan_data["sources"][self.version]
        get(self, **sources["libunwind"], destination="libunwind", strip_root=True)
        get(self, **sources["cmake"], destination="cmake", strip_root=True)
        get(self, **sources["runtimes"], destination="runtimes", strip_root=True)
        # Add missing project() command
        replace_in_file(self, "libunwind/CMakeLists.txt",
                        'set(LLVM_SUBPROJECT_TITLE "libunwind")',
                        'set(LLVM_SUBPROJECT_TITLE "libunwind")\n'
                        'project(libunwind LANGUAGES C CXX ASM)')

    def generate(self):
        tc = CMakeToolchain(self)
        tc.cache_variables["LIBUNWIND_ENABLE_SHARED"] = self.options.shared
        tc.cache_variables["LIBUNWIND_ENABLE_STATIC"] = not self.options.shared
        tc.cache_variables["LIBUNWIND_IS_BAREMETAL"] = self.options.baremetal
        tc.cache_variables["LIBUNWIND_ENABLE_THREADS"] = self.options.threads
        tc.cache_variables["LLVM_INCLUDE_TESTS"] = False
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure(build_script_folder="libunwind")
        cmake.build()

    def package(self):
        copy(self, "LICENSE.TXT", self.source_folder, os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()

    def package_info(self):
        # Unofficial file and target names
        self.cpp_info.set_property("cmake_file_name", "libunwind")
        self.cpp_info.set_property("cmake_target_name", "libunwind")
        self.cpp_info.set_property("cmake_target_alias", ["libunwind::libunwind"])
        self.cpp_info.set_property("pkg_config_name", "libunwind")

        self.cpp_info.libs = ["unwind"]
