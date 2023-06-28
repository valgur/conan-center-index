from conan import ConanFile
from conan.tools.cmake import CMake, CMakeToolchain, CMakeDeps, cmake_layout
from conan.tools.files import get, copy
from conan.tools.build import check_min_cppstd
from conan.errors import ConanInvalidConfiguration
from conan.tools.microsoft import is_msvc
from conan.tools.scm import Version
import os

required_conan_version = ">=1.53.0"


class OctoKeygenCPPConan(ConanFile):
    name = "octo-keygen-cpp"
    description = "Octo keygen library"
    license = "MIT"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/ofiriluz/octo-keygen-cpp"
    topics = ("pki", "keypair", "certificates", "cpp")

    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
    }

    @property
    def _compilers_minimum_version(self):
        return {
            "gcc": "8",
            "clang": "9",
            "apple-clang": "11",
            "Visual Studio": "16",
            "msvc": "1923",
        }

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires("octo-logger-cpp/1.1.0")
        self.requires("octo-encryption-cpp/1.1.0")
        self.requires("fmt/9.0.0")
        self.requires("openssl/[>=1.1 <4]")

    def validate(self):
        if self.info.settings.compiler.cppstd:
            check_min_cppstd(self, "17")

        minimum_version = self._compilers_minimum_version.get(str(self.info.settings.compiler), False)
        if minimum_version and Version(self.info.settings.compiler.version) < minimum_version:
            raise ConanInvalidConfiguration(
                f"{self.name} requires C++17, which your compiler does not support."
            )
        else:
            self.output.warning(
                f"{self.name} requires C++17. Your compiler is unknown. Assuming it supports C++17."
            )
        if self.settings.compiler == "clang" and self.settings.compiler.get_safe("libcxx") == "libc++":
            raise ConanInvalidConfiguration(
                f"{self.name} does not support clang with libc++. Use libstdc++ instead."
            )
        if is_msvc(self) and self.settings.compiler.runtime in ["MTd", "MT"]:
            raise ConanInvalidConfiguration(
                f"{self.name} does not support MSVC MT/MTd configurations, only MD/MDd is supported"
            )

    def build_requirements(self):
        self.tool_requires("cmake/3.24.0")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["DISABLE_TESTS"] = True
        tc.generate()
        tc = CMakeDeps(self)
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "octo-keygen-cpp")
        self.cpp_info.set_property("cmake_target_name", "octo::octo-keygen-cpp")
        self.cpp_info.set_property("pkg_config_name", "octo-keygen-cpp")
        self.cpp_info.libs = ["octo-keygen-cpp"]
        self.cpp_info.requires = [
            "fmt::fmt",
            "openssl::openssl",
            "octo-logger-cpp::octo-logger-cpp",
            "octo-encryption-cpp::octo-encryption-cpp",
        ]

        self.cpp_info.names["cmake_find_package"] = "octo-keygen-cpp"
        self.cpp_info.names["cmake_find_package_multi"] = "octo-keygen-cpp"
