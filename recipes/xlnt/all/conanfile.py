import os
from pathlib import Path

from conan import ConanFile
from conan.errors import ConanException
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *
from conan.tools.scm import Version

required_conan_version = ">=2.1"


class XlntConan(ConanFile):
    name = "xlnt"
    description = "Cross-platform user-friendly xlsx library for C++11+"
    license = "MIT"
    topics = ("excel", "xlsx", "spreadsheet", "reader", "writer")
    homepage = "https://github.com/tfussell/xlnt"
    url = "https://github.com/conan-io/conan-center-index"

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
        self.requires("libstudxml/[^1.1.0]")
        self.requires("miniz/[^3.0.2]")
        self.requires("utfcpp/[>=3.2.3 <4]")

    def validate(self):
        check_min_cppstd(self, 11)

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        apply_conandata_patches(self)
        # Remove unvendored third party libs
        for third_party in ("libstudxml", "miniz", "utfcpp"):
            rmdir(self, os.path.join(self.source_folder, "third-party", third_party))
        for path in [
            Path(self.source_folder, "include", "xlnt", "cell", "phonetic_run.hpp"),
            Path(self.source_folder, "include", "xlnt", "utils", "variant.hpp"),
            Path(self.source_folder, "source", "utils", "time.cpp"),
            Path(self.source_folder, "source", "utils", "timedelta.cpp"),
        ]:
            path.write_text("#include <cstdint>\n" + path.read_text())

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["STATIC"] = not self.options.shared
        tc.variables["TESTS"] = False
        tc.variables["SAMPLES"] = False
        tc.variables["BENCHMARKS"] = False
        tc.variables["PYTHON"] = False
        tc.cache_variables["CMAKE_POLICY_VERSION_MINIMUM"] = "3.15" # CMake 4 support
        if Version(self.version) > "1.5.0":
            raise ConanException("CMAKE_POLICY_VERSION_MINIMUM hardcoded to 3.5, check if new version supports CMake 4")
        tc.generate()
        deps = CMakeDeps(self)
        deps.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE.md", self.source_folder, os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))
        rmdir(self, os.path.join(self.package_folder, "share"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "Xlnt")
        self.cpp_info.set_property("cmake_target_name", "xlnt::xlnt")
        self.cpp_info.set_property("pkg_config_name", "xlnt")
        suffix = "d" if self.settings.build_type == "Debug" else ""
        self.cpp_info.libs = [f"xlnt{suffix}"]
        if not self.options.shared:
            self.cpp_info.defines.append("XLNT_STATIC")
