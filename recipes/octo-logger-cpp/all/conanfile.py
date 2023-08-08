from conan import ConanFile
from conan.tools.cmake import CMake, CMakeToolchain, CMakeDeps, cmake_layout
from conan.tools.files import get, copy
from conan.tools.build import check_min_cppstd
from conan.errors import ConanInvalidConfiguration
from conan.tools.microsoft import is_msvc_static_runtime
from conan.tools.scm import Version
import os

required_conan_version = ">=1.53.0"


class OctoLoggerCPPConan(ConanFile):
    name = "octo-logger-cpp"
    description = "Octo logger library"
    license = "MIT"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/ofiriluz/octo-logger-cpp"
    topics = ("logging", "cpp")

    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "with_aws": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "with_aws": False,
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

    @property
    def _aws_supported(self):
        return Version(self.version) >= "1.2.0"

    def configure(self):
        if not self._aws_supported:
            self.options.rm_safe("with_aws")

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires("fmt/10.0.0")
        if self.options.get_safe("with_aws"):
            self.requires("nlohmann_json/3.11.2")
            self.requires("aws-sdk-cpp/1.9.234")

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
        if is_msvc_static_runtime(self):
            raise ConanInvalidConfiguration(
                f"{self.name} does not support MSVC MT/MTd configurations, only MD/MDd is supported"
            )
        if self.options.get_safe("with_aws"):
            if not self.dependencies["aws-sdk-cpp"].options.logs:
                raise ConanInvalidConfiguration(f"{self.name} requires the option aws-sdk-cpp:logs=True")

    def build_requirements(self):
        self.tool_requires("cmake/[>=3.24]")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["CMAKE_FIND_ROOT_PATH_MODE_PACKAGE"] = "NONE"
        tc.variables["DISABLE_TESTS"] = True
        tc.variables["DISABLE_EXAMPLES"] = True
        if self.options.get_safe("with_aws"):
            tc.variables["WITH_AWS"] = True
        tc.generate()
        cd = CMakeDeps(self)
        cd.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "octo-logger-cpp")
        self.cpp_info.set_property("cmake_target_name", "octo::octo-logger-cpp")
        self.cpp_info.set_property("pkg_config_name", "octo-logger-cpp")
        self.cpp_info.libs = ["octo-logger-cpp"]
        self.cpp_info.names["cmake_find_package"] = "octo-logger-cpp"
        self.cpp_info.names["cmake_find_package_multi"] = "octo-logger-cpp"
        self.cpp_info.requires = ["fmt::fmt"]
        if self.options.get_safe("with_aws"):
            self.cpp_info.requires.extend(["nlohmann_json::nlohmann_json", "aws-sdk-cpp::monitoring"])
