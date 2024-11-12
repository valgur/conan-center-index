import os

from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import apply_conandata_patches, export_conandata_patches, get, copy, rmdir
from conan.tools.microsoft import is_msvc

required_conan_version = ">=1.53.0"

class DocoptCppConan(ConanFile):
    name = "docopt.cpp"
    description = "C++11 port of docopt"
    license = "MIT"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/docopt/docopt.cpp"
    topics = ("cli", "getopt", "options", "argparser")

    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "boost_regex": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "boost_regex": False,
    }

    @property
    def _min_cppstd(self):
        return 11

    def export_sources(self):
        export_conandata_patches(self)

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        if self.options.boost_regex:
            self.requires("boost/1.85.0")

    def validate(self):
        check_min_cppstd(self, self._min_cppstd)

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["USE_BOOST_REGEX"] = self.options.boost_regex
        tc.generate()

        dpes = CMakeDeps(self)
        dpes.generate()

    def build(self):
        apply_conandata_patches(self)
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, pattern="LICENSE*", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder)
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))

    @property
    def _cmake_target(self):
        return "docopt" if self.options.shared else "docopt_s"

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "docopt")
        self.cpp_info.set_property("cmake_target_name", self._cmake_target)
        self.cpp_info.set_property("pkg_config_name", "docopt")
        self.cpp_info.libs = ["docopt"]
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs = ["m"]
        if is_msvc(self) and self.options.shared:
            self.cpp_info.defines = ["DOCOPT_DLL"]
        if self.options.boost_regex:
            self.cpp_info.requires.append("boost::boost")
