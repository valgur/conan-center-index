import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.apple import fix_apple_shared_install_name
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *
from conan.tools.gnu import PkgConfigDeps
from conan.tools.layout import basic_layout
from conan.tools.meson import Meson, MesonToolchain
from conan.tools.scm import Version

required_conan_version = ">=2.1"

class PistacheConan(ConanFile):
    name = "pistache"
    description = "Pistache is a modern and elegant HTTP and REST framework for C++"
    license = "Apache-2.0"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/pistacheio/pistache"
    topics = ("http", "rest", "framework", "networking")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "with_ssl": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "with_ssl": False,
    }
    implements = ["auto_shared_fpic"]

    @property
    def _min_cppstd(self):
        return 17

    @property
    def _compilers_minimum_version(self):
        return {
            "gcc": "7",
            "clang": "6",
        }

    def export_sources(self):
        export_conandata_patches(self)

    def layout(self):
        if self.version == "cci.20201127":
            cmake_layout(self, src_folder="src")
        else:
            basic_layout(self, src_folder="src")

    def requirements(self):
        self.requires("rapidjson/[^1.1.0]")
        if self.options.with_ssl:
            self.requires("openssl/[>=1.1 <4]")
        if self.version != "cci.20201127":
            self.requires("date/[^3.0]")

    def validate(self):
        if self.settings.os != "Linux":
            raise ConanInvalidConfiguration(f"{self.ref} is only support on Linux.")

        if self.settings.compiler == "clang" and self.version in ["cci.20201127", "0.0.5"]:
            raise ConanInvalidConfiguration(f"{self.ref}'s clang support is broken. See pistacheio/pistache#835.")

        check_min_cppstd(self, self._min_cppstd)
        minimum_version = self._compilers_minimum_version.get(str(self.settings.compiler), False)
        if minimum_version and Version(self.settings.compiler.version) < minimum_version:
            raise ConanInvalidConfiguration(
                f"{self.ref} requires C++{self._min_cppstd}, which your compiler does not support."
            )

    def build_requirements(self):
        if self.version != "cci.20201127":
            self.tool_requires("meson/[>=1.2.3 <2]")
            if not self.conf.get("tools.gnu:pkg_config", default=False, check_type=str):
                self.tool_requires("pkgconf/[>=2.2 <3]")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        apply_conandata_patches(self)

    def generate(self):
        if self.version == "cci.20201127":
            tc = CMakeToolchain(self)
            tc.variables["PISTACHE_ENABLE_NETWORK_TESTS"] = False
            tc.variables["PISTACHE_USE_SSL"] = self.options.with_ssl
            # pistache requires explicit value for fPIC
            tc.variables["CMAKE_POSITION_INDEPENDENT_CODE"] = self.options.get_safe("fPIC", True)
            tc.generate()

            tc = CMakeDeps(self)
            tc.generate()
        else:
            tc = MesonToolchain(self)
            tc.project_options["PISTACHE_USE_SSL"] = self.options.with_ssl
            tc.project_options["PISTACHE_BUILD_EXAMPLES"] = False
            tc.project_options["PISTACHE_BUILD_TESTS"] = False
            tc.project_options["PISTACHE_BUILD_DOCS"] = False
            tc.generate()

            tc = PkgConfigDeps(self)
            tc.generate()

    def build(self):
        if self.version != "cci.20201127":
            replace_in_file(self, os.path.join(self.source_folder, "meson.build"),
                                    "dependency('RapidJSON', fallback: ['rapidjson', 'rapidjson_dep'])",
                                    "dependency('rapidjson', fallback: ['rapidjson', 'rapidjson_dep'])")

        if self.version == "cci.20201127":
            cmake = CMake(self)
            cmake.configure()
            cmake.build()
        else:
            meson = Meson(self)
            meson.configure()
            meson.build()

    def package(self):
        copy(self, pattern="LICENSE", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder)
        if self.version == "cci.20201127":
            cmake = CMake(self)
            cmake.install()
        else:
            meson = Meson(self)
            meson.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))
        if self.options.shared:
            rm(self, "*.a", os.path.join(self.package_folder, "lib"))
        fix_apple_shared_install_name(self)

    def package_info(self):
        # TODO: Pistache does not use namespace
        # TODO: Pistache variables are CamelCase e.g Pistache_BUILD_DIRS
        self.cpp_info.set_property("cmake_file_name", "Pistache")
        self.cpp_info.set_property("cmake_target_name", "Pistache::Pistache")
        # if package provides a pkgconfig file (package.pc, usually installed in <prefix>/lib/pkgconfig/)
        self.cpp_info.set_property("pkg_config_name", "libpistache")

        self.cpp_info.components["libpistache"].libs = collect_libs(self)
        self.cpp_info.components["libpistache"].requires = ["rapidjson::rapidjson"]
        if self.version != "cci.20201127":
            self.cpp_info.components["libpistache"].requires.append("date::date")
        if self.options.with_ssl:
            self.cpp_info.components["libpistache"].requires.append("openssl::openssl")
            self.cpp_info.components["libpistache"].defines = ["PISTACHE_USE_SSL=1"]
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.components["libpistache"].system_libs = ["pthread"]
            if self.version != "cci.20201127":
                self.cpp_info.components["libpistache"].system_libs.append("m")
