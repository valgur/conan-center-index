import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import check_min_cppstd, can_run
from conan.tools.cmake import CMake, CMakeToolchain, CMakeDeps, cmake_layout
from conan.tools.files import copy, get, replace_in_file
from conan.tools.microsoft import is_msvc


class LimereportConan(ConanFile):
    name = "limereport"
    description = "Report generator for Qt Framework"
    homepage = "https://limereport.ru"
    topics = ("pdf", "report", "qt")
    license = "LGPL-3.0", "GPL-3.0"
    url = "https://github.com/conan-io/conan-center-index"
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "with_zint": [True, False]
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "with_zint": False,
    }

    @property
    def _qt_version_major(self):
        return self.dependencies["qt"].ref.version.major

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")
        self.options["qt"].qtdeclarative = True
        self.options["qt"].qtsvg = True
        self.options["qt"].qttools = True
        if self.options.with_zint:
            self.options["zint"].with_qt = True

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        # QString included in Irglobal.h and Limereport expects be running Qt on customer side
        self.requires("qt/[>=5.15 <7]", transitive_headers=True, transitive_libs=True, run=can_run(self))
        if self.options.with_zint:
            self.requires("zint/2.10.0")

    def validate(self):
        check_min_cppstd(self, 17)
        if not self.dependencies["qt"].options.qtdeclarative:
            raise ConanInvalidConfiguration(f"{self.ref} requires -o='qt/*:qtdeclarative=True'")
        if not (self.dependencies["qt"].options.qtsvg and self.dependencies["qt"].options.qttools):
            raise ConanInvalidConfiguration(f"{self.ref} requires -o='qt/*:qtsvg=True' and -o='qt/*:qttools=True'")
        if self.options.with_zint and not self.dependencies["zint"].options.with_qt:
            raise ConanInvalidConfiguration(f"{self.ref} option with_zint=True requires -o 'zint/*:with_qt=True'")

    def build_requirements(self):
        if not can_run(self):
            self.tool_requires("qt/<host_version>")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        # Avoid using vendorized zint
        replace_in_file(self, os.path.join(self.source_folder, "CMakeLists.txt"), "add_subdirectory(3rdparty)", "")

    def generate(self):
        tc = CMakeToolchain(self)
        tc.cache_variables["LIMEREPORT_STATIC"] = not self.options.shared
        if is_msvc(self):
            tc.cache_variables["WINDOWS_BUILD"] = True
        tc.cache_variables["USE_QT6"] = self._qt_version_major == 6
        tc.cache_variables["ENABLE_ZINT"] = self.options.with_zint
        tc.generate()
        tc = CMakeDeps(self)
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        copy(self, "COPYING", self.source_folder, os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()

    def package_info(self):
        self.cpp_info.libs = [f"limereport-qt{self._qt_version_major}"]
        self.cpp_info.requires = ["qt::qtCore", "qt::qtWidgets", "qt::qtQml", "qt::qtXml", "qt::qtSql",
                                   "qt::qtPrintSupport", "qt::qtSvg", "qt::qtUiTools"]
        if self.options.with_zint:
            self.cpp_info.requires.append("zint::zint")
        if self.options.shared:
            self.cpp_info.defines.append("LIMEREPORT_IMPORTS")
