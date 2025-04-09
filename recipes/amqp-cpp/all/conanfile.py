import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *
from conan.tools.scm import Version

required_conan_version = ">=2.1"


class AmqpcppConan(ConanFile):
    name = "amqp-cpp"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/CopernicaMarketingSoftware/AMQP-CPP"
    topics = ("amqp", "network", "queue")
    license = "Apache-2.0"
    description = "C++ library for asynchronous non-blocking communication with RabbitMQ"
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "linux_tcp_module": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "linux_tcp_module": True,
    }

    def export_sources(self):
        export_conandata_patches(self)

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC
            del self.options.linux_tcp_module

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        if self.options.get_safe("linux_tcp_module"):
            self.requires("openssl/[>=1.1 <4]")

    @property
    def _min_cppstd(self):
        return "11" if Version(self.version) < "4.3.20" else "17"

    @property
    def _compilers_minimum_version(self):
        return {
            "17": {
                "gcc": "7.4",
                "msvc": "191",
                "clang": "6",
                "apple-clang": "10",
            },
        }.get(self._min_cppstd, {})

    def validate(self):
        check_min_cppstd(self, self._min_cppstd)

        def loose_lt_semver(v1, v2):
            lv1 = [int(v) for v in v1.split(".")]
            lv2 = [int(v) for v in v2.split(".")]
            min_length = min(len(lv1), len(lv2))
            return lv1[:min_length] < lv2[:min_length]

        minimum_version = self._compilers_minimum_version.get(str(self.settings.compiler), False)
        if minimum_version and loose_lt_semver(str(self.settings.compiler.version), minimum_version):
            raise ConanInvalidConfiguration(
                f"{self.ref} requires C++{self._min_cppstd}, which your compiler does not support."
            )

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        apply_conandata_patches(self)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["AMQP-CPP_BUILD_SHARED"] = self.options.shared
        tc.variables["AMQP-CPP_BUILD_EXAMPLES"] = False
        tc.variables["AMQP-CPP_LINUX_TCP"] = self.options.get_safe("linux_tcp_module", False)
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
        rmdir(self, os.path.join(self.package_folder, "cmake"))
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "amqpcpp")
        self.cpp_info.set_property("cmake_target_name", "amqpcpp")
        self.cpp_info.set_property("pkg_config_name", "amqpcpp")
        self.cpp_info.libs = ["amqpcpp"]
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs = ["dl", "m", "pthread"]
        elif self.settings.os == "Windows":
            self.cpp_info.system_libs = ["ws2_32"]
