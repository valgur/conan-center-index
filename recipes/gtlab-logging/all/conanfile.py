import os
from pathlib import Path

from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeToolchain, CMakeDeps, cmake_layout
from conan.tools.files import get, rmdir, copy, export_conandata_patches, apply_conandata_patches

required_conan_version = ">=2.0.9"

class GTLabLoggingConan(ConanFile):
    name = "gtlab-logging"
    description = "Simple logging interface with Qt support"
    license = "BSD-3-Clause"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/dlr-gtlab/gt-logging"
    topics = ("logging", "qt")

    settings = "os", "arch", "compiler", "build_type"
    package_type = "library"

    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "with_qt": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "with_qt": False,
    }

    implements = ["auto_shared_fpic"]

    def export_sources(self):
        export_conandata_patches(self)

    def requirements(self):
        if self.options.with_qt:
            self.requires("qt/[>=5.15 <7]", transitive_headers=True, transitive_libs=True)

    def validate(self):
        check_min_cppstd(self, 14)

    def generate(self):
        CMakeToolchain(self).generate()
        CMakeDeps(self).generate()

    def layout(self):
        cmake_layout(self, src_folder="src")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        apply_conandata_patches(self)

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "BSD-3-Clause.txt", os.path.join(self.source_folder, "LICENSES"), os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "GTlabLogging")
        self.cpp_info.set_property("cmake_target_name", "GTlab::Logging")
        self.cpp_info.libs = ["GTlabLogging"] if self.settings.build_type != "Debug" else ["GTlabLogging-d"]
        self.cpp_info.includedirs.append(os.path.join("include", "logging"))
        self.cpp_info.libdirs = [os.path.join("lib", "logging")]
        if self.options.with_qt:
            self.cpp_info.defines = ["GT_LOG_USE_QT_BINDINGS"]
