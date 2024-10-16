import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import check_min_cppstd, can_run, valid_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import copy, get, rm, rmdir
from conan.tools.scm import Version

required_conan_version = ">=1.52.0"


class Stlab(ConanFile):
    name = "stlab"
    description = "The Software Technology Lab libraries."
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/stlab/libraries"
    license = "BSL-1.0"
    topics = "concurrency", "futures", "channels"
    settings = "arch", "os", "compiler", "build_type",
    options = {
        "with_boost": [True, False],
        "no_std_coroutines": [True, False],
        "future_coroutines": [True, False],
        "task_system": ["portable", "libdispatch", "emscripten", "pnacl", "windows"],
        "thread_system": ["win32", "pthread", "pthread-emscripten", "pthread-apple", "none"],
    }
    default_options = {
        "with_boost": False,
        "no_std_coroutines": True,
        "future_coroutines": False
        # Handle default value for `thread_system` in `config_options` method
        # Handle default value for `task_system` in `config_options` method
    }
    package_type = "header-library"
    short_paths = True

    def config_options(self):
        self.options.thread_system = {"Macos": "pthread-apple",
                                      "Linux": "pthread",
                                      "Windows": "win32",
                                      "Emscripten": "pthread-emscripten",}.get(str(self.settings.os), "none")
        self.options.task_system = {"Macos": "libdispatch",
                                    "Windows": "windows"}.get(str(self.settings.os), "portable")

    @property
    def _minimum_cpp_standard(self):
        return 17

    @property
    def _compilers_minimum_version(self):
        return {
            "gcc": "9",
            "clang": "8",
            "apple-clang": "13",
            "msvc": "192",
            "Visual Studio": "16",
        }

    def layout(self):
        cmake_layout(self, src_folder="src")

    def build_requirements(self):
        self.tool_requires("cmake/[>=3.23.3]")

    def requirements(self):
        if self.options.with_boost:
            self.requires("boost/1.85.0")
        # On macOS, it is not necessary to use the libdispatch conan package,
        # because the library is included in the OS.
        if self.options.task_system == "libdispatch" and self.settings.os != "Macos":
            self.requires("libdispatch/5.3.2")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], destination=self.source_folder, strip_root=True)

    def _validate_task_system(self):
        if self.options.task_system == "libdispatch":
            if self.settings.os == "Linux" and self.settings.compiler != "clang":
                raise ConanInvalidConfiguration(f"{self.ref} task_system=libdispatch needs Clang compiler when using OS: {self.settings.os}."
                                                f" Use Clang compiler or switch to task_system=portable")
            elif self.settings.os != "Macos":
                raise ConanInvalidConfiguration(f"{self.ref} task_system=libdispatch is not supported on {self.settings.os}")
        elif self.options.task_system == "windows" and self.settings.os != "Windows":
            raise ConanInvalidConfiguration(f"{self.ref} task_system=windows is not supported on {self.settings.os}")

    def _validate_thread_system(self):
        if any([self.options.thread_system == "pthread-apple" and self.settings.os != "Macos",
                self.options.thread_system == "pthread" and self.settings.os != "Linux",
                self.options.thread_system == "win32" and self.settings.os != "Windows",
                self.options.thread_system == "pthread-emscripten" and self.settings.os != "Emscripten"]):
            raise ConanInvalidConfiguration(f"{self.ref} thread_system={self.options.thread_system} is not supported on {self.settings.os}")

    def _validate_boost_components(self):
        if not any([self.settings.os != "Macos", self.settings.compiler != "apple-clang",
                    Version(str(self.settings.compiler.version)) >= "12", self.options.with_boost]):
            # On Apple we have to force the usage of boost.variant and boost.optional, because Apple's implementation of C++17
            # is not complete.
            raise ConanInvalidConfiguration(
                f"Compiler Apple-Clang < 12 versions do not correctly support std::optional or std::variant, "
                f"so we will use boost::optional and boost::variant instead. Try -o {self.ref}:with_boost=True.")

    def _validate_min_compiler_version(self):
        minimum_version = self._compilers_minimum_version.get(str(self.settings.compiler), False)
        if minimum_version and Version(str(self.settings.compiler.version)) < minimum_version:
            raise ConanInvalidConfiguration(
                f"{self.ref} requires C++{self._minimum_cpp_standard}, which your compiler does not support."
            )
        if self.settings.compiler == "clang" and str(self.settings.compiler.version) in ("13", "14"):
            raise ConanInvalidConfiguration(
                f"{self.ref} currently does not work with Clang {self.settings.compiler.version} on CCI, it enters "
                f"in an infinite build loop (smells like a compiler bug). Contributions are welcomed!")

    def validate(self):
        if self.settings.compiler.get_safe("cppstd"):
            check_min_cppstd(self, self._minimum_cpp_standard)

        self._validate_min_compiler_version()
        self._validate_task_system()
        self._validate_thread_system()
        self._validate_boost_components()

    def configure(self):
        self.output.info(f"STLab With Boost: {self.options.with_boost}.")
        self.output.info(f"STLab Future Coroutines: {self.options.future_coroutines}.")
        self.output.info(f"STLab No Standard Coroutines: {self.options.no_std_coroutines}.")
        self.output.info(f"STLab Task System: {self.options.task_system}.")
        self.output.info(f"STLab Thread System: {self.options.thread_system}.")

    @property
    def _has_coroutines_support(self):
        if self.settings.compiler.cppstd and not valid_min_cppstd(self, 20):
            return False
        min_ver = {
            "gcc": "10",
            "clang": "13",
            "apple-clang": "13",
            "msvc": "192",
            "Visual Studio": "16",
        }.get(str(self.settings.compiler))
        return min_ver and Version(self.settings.compiler.version) >= min_ver

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["BUILD_TESTING"] = False
        tc.variables["STLAB_USE_BOOST_CPP17_SHIMS"] = self.options.with_boost
        tc.variables["STLAB_NO_STD_COROUTINES"] = self.options.no_std_coroutines
        tc.variables["STLAB_THREAD_SYSTEM"] = self.options.thread_system
        tc.variables["STLAB_TASK_SYSTEM"] = self.options.task_system
        tc.variables["CMAKE_REQUIRE_FIND_PACKAGE_Boost"] = self.options.with_boost
        tc.variables["CMAKE_REQUIRE_FIND_PACKAGE_libdispatch"] = self.options.task_system == "libdispatch"
        tc.variables["CMAKE_DISABLE_FIND_PACKAGE_Qt6"] = True
        if not can_run(self):
            tc.variables["STLAB_HAVE_FUNCTIONAL_VARIANT_OPTIONAL"] = True
            tc.variables["STLAB_HAVE_FUNCTIONAL_COROUTINES"] = self._has_coroutines_support
        tc.generate()

        tc = CMakeDeps(self)
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "share"))
        rm(self, "msvcp*.dll", os.path.join(self.package_folder, "bin"))
        rm(self, "concrt*.dll", os.path.join(self.package_folder, "bin"))
        rm(self, "vcruntime*.dll", os.path.join(self.package_folder, "bin"))

    def package_id(self):
        self.info.settings.clear()

    def package_info(self):
        future_coroutines_value = 1 if self.options.future_coroutines else 0
        self.cpp_info.defines.append(f"STLAB_FUTURE_COROUTINES={future_coroutines_value}")
        if self.settings.os == "Windows":
            self.cpp_info.defines.append("NOMINMAX")
        if self.settings.os == "Linux":
            self.cpp_info.system_libs = ["pthread"]
