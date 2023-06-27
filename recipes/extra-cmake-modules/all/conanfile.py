# TODO: verify the Conan v2 migration

import os

from conan import ConanFile
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import copy, get, replace_in_file

required_conan_version = ">=1.52.0"


class ExtracmakemodulesConan(ConanFile):
    name = "extra-cmake-modules"
    description = "KDE's CMake modules"
    license = ("MIT", "BSD-2-Clause", "BSD-3-Clause")
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://api.kde.org/ecm/"
    topics = ("cmake", "toolchain", "build-settings", "header-only")

    package_type = "build-scripts"
    settings = "os", "arch", "compiler", "build_type"
    no_copy_source = True

    def layout(self):
        cmake_layout(self, src_folder="src")

    def package_id(self):
        self.info.clear()

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["BUILD_HTML_DOCS"] = False
        tc.variables["BUILD_QTHELP_DOCS"] = False
        tc.variables["BUILD_MAN_DOCS"] = False
        tc.variables["SHARE_INSTALL_DIR"] = os.path.join(self.package_folder, "res")
        tc.generate()
        tc = CMakeDeps(self)
        tc.generate()

    def _patch_sources(self):
        # KB-H016: do not install Find*.cmake
        replace_in_file(
            self,
            os.path.join(self.source_folder, "CMakeLists.txt"),
            "install(FILES ${installFindModuleFiles} DESTINATION ${FIND_MODULES_INSTALL_DIR})",
            "",
        )

    def build(self):
        self._patch_sources()
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        cmake = CMake(self)
        cmake.install()
        copy(
            self,
            "testhelper.h",
            src=os.path.join(self.source_folder, "tests/ECMAddTests"),
            dst=os.path.join(self.package_folder, "res/tests"),
        )
        copy(
            self,
            "*",
            src=os.path.join(self.source_folder, "LICENSES"),
            dst=os.path.join(self.package_folder, "licenses"),
        )

    def package_info(self):
        self.cpp_info.bindirs = []
        self.cpp_info.libdirs = []
        self.cpp_info.resdirs = ["res"]
        self.cpp_info.builddirs = [
            "res/ECM/cmake",
            "res/ECM/kde-modules",
            "res/ECM/modules",
            "res/ECM/test-modules",
            "res/ECM/toolchain",
        ]
