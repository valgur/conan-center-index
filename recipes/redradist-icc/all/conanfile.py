from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.apple import is_apple_os
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout
from conan.tools.files import *

required_conan_version = ">=2.1"


class ICCConan(ConanFile):
    name = "redradist-icc"
    description = (
        "I.C.C. - Inter Component Communication, This is a library created to simplify communication between "
        "components inside of single application. It is thread safe and could be used for creating "
        "components that works in different threads. "
    )
    license = "MIT"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/redradist/Inter-Component-Communication"
    topics = ("thread-safe", "active-object", "communication")

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

    def validate(self):
        check_min_cppstd(self, 11)

        if is_apple_os(self):
            raise ConanInvalidConfiguration(f"OS {self.settings.os} is not supported")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.cache_variables["ICC_BUILD_SHARED"] = self.options.shared
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        cmake = CMake(self)
        cmake.install()

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "icc")
        self.cpp_info.set_property("cmake_target_name", "icc::icc")

        if self.options.shared:
            self.cpp_info.libs = ["ICC"]
        else:
            self.cpp_info.libs = ["ICC_static"]

        if self.settings.os == "Windows":
            self.cpp_info.system_libs = ["ws2_32", "wsock32"]
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs = ["pthread"]
