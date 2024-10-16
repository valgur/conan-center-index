import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.apple import is_apple_os
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout
from conan.tools.env import VirtualBuildEnv, Environment
from conan.tools.files import get, copy, replace_in_file, save
from conan.tools.gnu import GnuToolchain

required_conan_version = ">=2.3.0"


class ZenohCConan(ConanFile):
    name = "zenoh-c"
    description = "C API for Zenoh: a pub/sub/query protocol unifying data in motion, data at rest and computations"
    license = "EPL-2.0 OR Apache-2.0"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/eclipse-zenoh/zenoh-c"
    topics = ("networking", "pub-sub", "messaging", "robotics", "ros2", "iot", "edge-computing", "micro-controllers")

    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "logger_autoinit": [True, False],
        "shared_memory": [True, False],
        "extra_cargo_flags": ["ANY"],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "logger_autoinit": True,
        "shared_memory": True,
        "extra_cargo_flags": "",
    }
    options_description = {
        "logger_autoinit": ("Enable zenoh-c Zenoh's logging library automatically on init. "
                            "The logger can still be manually re-enabled with the zc_init_logger function."),
        "shared_memory": "Enables transferring data through shared memory if the receiver and transmitter are on the same host",
        "extra_cargo_flags": "Extra flags to pass to Cargo"
    }


    def config_options(self):
        # The library is always built as PIC
        del self.options.fPIC

    def configure(self):
        # Does not use the C or C++ compiler
        del self.settings.compiler

    def layout(self):
        cmake_layout(self, src_folder="src")

    def _is_supported_platform(self):
        if self.settings.os == "Windows" and self.settings.arch == "x86_64":
            return True
        if self.settings.os in ["Linux", "FreeBSD"] and self.settings.arch in ["x86_64", "armv6", "armv7hf", "armv8"]:
            return True
        if is_apple_os(self) and self.settings.arch in ["x86_64", "armv8"]:
            return True
        return False

    def validate(self):
        if not self._is_supported_platform():
            raise ConanInvalidConfiguration(
                f"{self.settings.os}/{self.settings.arch} combination is not supported"
            )

    def build_requirements(self):
        self.tool_requires("cmake/[>=3.16 <4]")
        self.tool_requires("rust/1.72.1")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        venv = VirtualBuildEnv(self)
        venv.generate()

        tc = CMakeToolchain(self)
        tc.variables["ZENOHC_INSTALL_STATIC_LIBRARY"] = not self.options.shared
        tc.variables["ZENOHC_BUILD_WITH_LOGGER_AUTOINIT"] = self.options.logger_autoinit
        tc.variables["ZENOHC_BUILD_WITH_SHARED_MEMORY"] = self.options.shared_memory
        tc.variables["ZENOHC_CARGO_FLAGS"] = str(self.options.extra_cargo_flags)
        tc.generate()

        env = Environment()
        # Ensure the correct linker is used, especially when cross-compiling
        target_upper = self.conf.get("user.rust:target", check_type=str).upper().replace("-", "_")
        cc = GnuToolchain(self).extra_env.vars(self)["CC"]
        env.define_path(f"CARGO_TARGET_{target_upper}_LINKER", cc)
        # Don't add the Cargo dependencies to a global Cargo cache
        env.define_path("CARGO_HOME", os.path.join(self.build_folder, "cargo"))
        env.vars(self).save_script("cargo_paths")

    def _patch_sources(self):
        # Cargo channels are only applicable when Rust has been installed via rustup
        replace_in_file(self, os.path.join(self.source_folder, "CMakeLists.txt"),
                        "+${ZENOHC_CARGO_CHANNEL}", "")
        # Disable building of examples and tests
        save(self, os.path.join(self.source_folder, "examples", "CMakeLists.txt"), "")
        save(self, os.path.join(self.source_folder, "tests", "CMakeLists.txt"), "")

    def build(self):
        self._patch_sources()
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    @property
    def _lib_name(self):
        if self.settings.build_type == "Debug":
            return "zenohcd"
        return "zenohc"

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        # Skip cmake.install() since it does not work correctly when cross-compiling.
        copy(self, "*.h", os.path.join(self.source_folder, "include"), os.path.join(self.package_folder, "include"))
        build_type = "debug" if self.settings.build_type == "Debug" else "release"
        dist_dir = os.path.join(self.build_folder, build_type)
        copy(self, "*.h", os.path.join(dist_dir, "include"), os.path.join(self.package_folder, "include"))
        lib_pattern = "*.dll.lib" if self.options.shared else "*.lib"
        for pattern in ["*.a", "*.so*", "*.dylib*", lib_pattern]:
            copy(self, pattern, dist_dir, os.path.join(self.package_folder, "lib"), keep_path=False)
        if self.settings.os == "Windows" and self.options.shared:
            copy(self, "*.dll", dist_dir, os.path.join(self.package_folder, "bin"), keep_path=False)

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "zenohc")
        self.cpp_info.set_property("cmake_target_name", "zenohc::lib")
        self.cpp_info.set_property("cmake_target_aliases", [f"zenohc::{'shared' if self.options.shared else 'static'}"])

        self.cpp_info.libs = [self._lib_name]
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs.extend(["dl", "m", "pthread", "rt"])
        elif self.settings.os == "Windows":
            self.cpp_info.system_libs.extend(["bcrypt", "crypt32", "iphlpapi", "ncrypt", "ntdll", "runtimeobject", "secur32", "userenv", "ws2_32"])
        elif is_apple_os(self):
            self.cpp_info.frameworks.extend(["Foundation", "Security"])
