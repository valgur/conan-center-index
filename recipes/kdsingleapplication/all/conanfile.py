import os

from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.env.virtualrunenv import VirtualRunEnv
from conan.tools.files import *

required_conan_version = ">=2.1"


class KDSingleApplicationConan(ConanFile):
    name = "kdsingleapplication"
    description = "KDAB's helper class for single-instance policy applications."
    topics = ("qt", "kdab")
    license = "MIT"
    homepage = "https://github.com/KDAB/KDSingleApplication"
    url = "https://github.com/conan-io/conan-center-index"
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
    }
    default_options = {
        "shared": True,
        "fPIC": True,
    }
    implements = ["auto_shared_fpic"]

    def layout(self):
        cmake_layout(self, src_folder="src")

    def validate(self):
        check_min_cppstd(self, 14)

    def requirements(self):
        self.requires("qt/[>=5 <7]", transitive_headers=True, transitive_libs=True)

    def build_requirements(self):
        self.tool_requires("cmake/[>=3.27 <5]")
        self.tool_requires("qt/<host_version>")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        replace_in_file(self, "CMakeLists.txt", "set(CMAKE_CXX_STANDARD 14)", "")
        replace_in_file(self, os.path.join("src", "CMakeLists.txt"), "Qt::", "Qt${QT_VERSION_MAJOR}::")

    def generate(self):
        # FIXME: workaround for libicui18n.so.75 not being found
        VirtualRunEnv(self).generate(scope="build")

        tc = CMakeToolchain(self)
        tc.cache_variables["KDSingleApplication_QT6"] = self.dependencies["qt"].ref.version.major == 6
        tc.cache_variables["KDSingleApplication_EXAMPLES"] = False
        tc.cache_variables["BUILD_TRANSLATIONS"] = False
        tc.generate()

        deps = CMakeDeps(self)
        deps.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE.txt", self.source_folder, os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))
        rmdir(self, os.path.join(self.package_folder, "share"))

    def package_info(self):
        suffix = "-qt6" if self.dependencies["qt"].ref.version.major == 6 else ""
        self.cpp_info.set_property("cmake_file_name", "KDSingleApplication")
        self.cpp_info.set_property("cmake_target_name", "kdsingleapplication")
        self.cpp_info.libs = [f"kdsingleapplication{suffix}"]
        self.cpp_info.includedirs.append(os.path.join("include", f"kdsingleapplication{suffix}"))
