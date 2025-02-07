import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import apply_conandata_patches, copy, download, export_conandata_patches, get
from conan.tools.scm import Version

required_conan_version = ">=2.0.9"


class QtXlsxWriterConan(ConanFile):
    name = "qtxlsxwriter"
    license = "MIT"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/dbzhang800/QtXlsxWriter"
    description = ".xlsx file reader and writer for Qt5"
    topics = ("excel", "xlsx")

    settings = "os", "arch", "compiler", "build_type"
    package_type = "library"
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
        copy(self, "CMakeLists.txt", src=self.recipe_folder, dst=self.export_sources_folder)
        export_conandata_patches(self)

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires("qt/[~5.15]", transitive_headers=True, transitive_libs=True)

    def validate(self):
        if not self.dependencies["qt"].options.gui:
            raise ConanInvalidConfiguration(f"{self.ref} requires -o qt/*:gui=True")

    def build_requirements(self):
        self.tool_requires("cmake/[>=3.21 <4]")
        self.tool_requires("qt/<host_version>")

    def source(self):
        get(self, **self.conan_data["sources"][self.version]["source"], strip_root=True)
        download(self, **self.conan_data["sources"][self.version]["license"], filename="LICENSE")
        apply_conandata_patches(self)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["QTXLSXWRITER_SRC_DIR"] = self.source_folder.replace("\\", "/")
        tc.variables["QT_VERSION_MAJOR"] = str(Version(self.dependencies["qt"].ref.version).major)
        tc.variables["QT_ROOT"] = self.dependencies["qt"].package_folder.replace("\\", "/")
        tc.generate()
        deps = CMakeDeps(self)
        deps.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure(build_script_folder=os.path.join(self.source_folder, os.pardir))
        cmake.build()

    def package(self):
        copy(self, "LICENSE", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()

    def package_info(self):
        self.cpp_info.libs = ["qtxlsxwriter"]
        if not self.options.shared:
            self.cpp_info.defines = ["QTXLSX_STATIC"]
        self.cpp_info.requires = ["qt::qtCore", "qt::qtGui"]
