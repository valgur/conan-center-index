from conan import ConanFile
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout
from conan.tools.files import copy, get
import os

required_conan_version = ">=1.46.0"


class lmdbConan(ConanFile):
    name = "lmdb"
    description = "Fast and compat memory-mapped key-value database"
    license = "OLDAP-2.8"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://symas.com/lmdb/"
    topics = ("database", "key-value", "memory-mapped")

    package_type = "application"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "enable_robust_mutex": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "enable_robust_mutex": True,
    }

    def export_sources(self):
        copy(self, "CMakeLists.txt", self.recipe_folder, self.export_sources_folder)

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC
        if self.settings.os in ("Linux", "FreeBSD"):
            self.options.enable_robust_mutex = True
        else:
            self.options.enable_robust_mutex = False

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")
        self.settings.rm_safe("compiler.libcxx")
        self.settings.rm_safe("compiler.cppstd")

    def layout(self):
        cmake_layout(self, src_folder="src")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["LMDB_SRC_DIR"] = os.path.join(self.source_folder, "libraries", "liblmdb").replace(
            "\\", "/"
        )
        tc.variables["LMDB_ENABLE_ROBUST_MUTEX"] = self.options.enable_robust_mutex
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure(build_script_folder=os.path.join(self.source_folder, os.pardir))
        cmake.build()

    def package(self):
        copy(self, "LICENSE",
             src=os.path.join(self.source_folder, "libraries", "liblmdb"),
             dst=os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()

    def package_info(self):
        self.cpp_info.set_property("pkg_config_name", "lmdb")
        self.cpp_info.libs = ["lmdb"]

        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs = ["pthread"]

        bin_path = os.path.join(self.package_folder, "bin")
        self.output.info(f"Appending PATH environment variable: {bin_path}")
        self.env_info.PATH.append(bin_path)
