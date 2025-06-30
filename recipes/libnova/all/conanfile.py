import os

import requests
from conan import ConanFile
from conan.errors import ConanException
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout
from conan.tools.files import *

required_conan_version = ">=2.4"


class LibnovaConan(ConanFile):
    name = "libnova"
    description = (
        "libnova is a general purpose, double precision, celestial mechanics, "
        "astrometry and astrodynamics library."
    )
    license = "LGPL-2.0-only"
    topics = ("celestial-mechanics", "astrometry", "astrodynamics")
    homepage = "https://sourceforge.net/projects/libnova"
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
    languages = ["C"]

    def export_sources(self):
        export_conandata_patches(self)

    def layout(self):
        cmake_layout(self, src_folder="src")

    @staticmethod
    def _generate_git_tag_archive_sourceforge(url, timeout=10, retry=2):
        for _ in range(retry):
            try:
                response = requests.get(url, timeout=timeout)
                response.raise_for_status()
                return
            except Exception:
                pass
        raise ConanException("All attempts to generate an archive url have failed.")

    def source(self):
        # Generate the archive download link
        self._generate_git_tag_archive_sourceforge(self.conan_data["sources"][self.version]["post"]["url"])
        # Download archive
        get(self, **self.conan_data["sources"][self.version]["archive"], strip_root=True)
        apply_conandata_patches(self)
        # CMake v4 support
        replace_in_file(self, "CMakeLists.txt",
                        "cmake_minimum_required(VERSION 3.1)",
                        "cmake_minimum_required(VERSION 3.5)")

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["BUILD_SHARED_LIBRARY"] = self.options.shared
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "COPYING", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()

    def package_info(self):
        postfix = "d" if self.settings.build_type == "Debug" else ""
        self.cpp_info.libs = [f"nova{postfix}"]
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs.append("m")
