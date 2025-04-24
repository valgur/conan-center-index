from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *
from conan.tools.microsoft import is_msvc
from conan.tools.scm import Version
import os

required_conan_version = ">=2.1"


class OatppPostgresqlConan(ConanFile):
    name = "oatpp-postgresql"
    license = "Apache-2.0"
    homepage = "https://github.com/oatpp/oatpp-postgresql"
    url = "https://github.com/conan-io/conan-center-index"
    description = "oat++ PostgreSQL library"
    topics = ("oat", "postgresql", "orm", "database")

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
    implements = ["auto_shared_fpic"]

    def export_sources(self):
        export_conandata_patches(self)

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        # Most headers include oatpp's
        self.requires(f"oatpp/{self.version}", transitive_headers=True)
        self.requires("libpq/[^17.0]")

    def validate(self):
        check_min_cppstd(self, 11)

        if is_msvc(self) and self.info.options.shared:
            raise ConanInvalidConfiguration(f"{self.ref} cannot be built as shared library with msvc")

        if self.info.settings.compiler == "gcc" and Version(self.info.settings.compiler.version) < "5":
            raise ConanInvalidConfiguration(f"{self.ref} requires GCC >=5")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        apply_conandata_patches(self)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["OATPP_BUILD_TESTS"] = False
        tc.variables["OATPP_MODULES_LOCATION"] = "INSTALLED"
        # Honor BUILD_SHARED_LIBS from conan_toolchain (see https://github.com/conan-io/conan/issues/11840)
        tc.cache_variables["CMAKE_POLICY_DEFAULT_CMP0077"] = "NEW"
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
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "oatpp-postgresql")
        self.cpp_info.set_property("cmake_target_name", "oatpp::oatpp-postgresql")
        self.cpp_info.includedirs = [os.path.join("include", f"oatpp-{self.version}", "oatpp-postgresql")]
        self.cpp_info.libdirs = [os.path.join("lib", f"oatpp-{self.version}")]
        if self.settings.os == "Windows" and self.options.shared:
            self.cpp_info.bindirs = [os.path.join("bin", f"oatpp-{self.version}")]
        else:
            self.cpp_info.bindirs = []
        self.cpp_info.libs = ["oatpp-postgresql"]
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs = ["pthread"]
