import os

from conan import ConanFile
from conan.tools.build import can_run
from conan.tools.cmake import CMake, CMakeToolchain, CMakeDeps, cmake_layout
from conan.tools.files import apply_conandata_patches, copy, export_conandata_patches, get, rmdir, replace_in_file
from conan.tools.microsoft import is_msvc
from conan.tools.scm import Version
from conans.errors import ConanInvalidConfiguration

required_conan_version = ">=2.0.9"


class QXlsxConan(ConanFile):
    name = "qxlsx"
    description = "Excel file(*.xlsx) reader/writer library using Qt 5 or 6."
    license = "MIT"
    topics = ("excel", "xlsx")
    homepage = "https://github.com/QtExcel/QXlsx"
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

    @property
    def _qt_version(self):
        return self.dependencies["qt"].ref.version.major

    def export_sources(self):
        export_conandata_patches(self)

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        # INFO: QXlsx/xlsxdocument.h includes QtGlobal
        # INFO: transitive libs: undefined reference to symbol '_ZN10QArrayData10deallocateEPS_mm@@Qt_5'
        self.requires("qt/[>=5.15 <7]", transitive_headers=True, transitive_libs=True, run=can_run(self))

    def validate(self):
        if not self.dependencies["qt"].options.gui:
            raise ConanInvalidConfiguration(f"{self.ref} requires Qt with gui component. Use '-o qt/*:gui=True'")
        if Version(self.version) == "1.4.4" and is_msvc(self) and self.options.shared:
            # FIXME: xlsxworksheet.cpp.obj : error LNK2019: unresolved external symbol " __cdecl QVector<class QXmlStreamAttribute>::begin(
            raise ConanInvalidConfiguration(f"{self.ref} Conan recipe does not support shared library with MSVC. Use version 1.4.5 or later.")

    def build_requirements(self):
        if Version(self.version) >= "1.4.4":
            self.tool_requires("cmake/[>=3.16 <4]")
        if not can_run(self):
            self.tool_requires("qt/<host_version>")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        apply_conandata_patches(self)
        replace_in_file(self, os.path.join(self.source_folder, "QXlsx", "CMakeLists.txt"),
                        "find_package(Qt${QT_VERSION_MAJOR} 5.9",
                        "find_package(Qt${QT_VERSION_MAJOR}")

    def generate(self):
        tc = CMakeToolchain(self)
        tc.cache_variables["QT_VERSION_MAJOR"] = str(self._qt_version)
        tc.generate()
        tc = CMakeDeps(self)
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure(build_script_folder=os.path.join(self.source_folder, "QXlsx"))
        cmake.build()

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))

    def package_info(self):
        cmake_name = f"QXlsxQt{self._qt_version}" if Version(self.version) >= "1.4.5" else "QXlsx"
        self.cpp_info.set_property("cmake_file_name", cmake_name)
        self.cpp_info.set_property("cmake_target_name", "QXlsx::QXlsx")
        self.cpp_info.libs = [cmake_name]
        self.cpp_info.includedirs = ["include", os.path.join("include", "QXlsx")]
        self.cpp_info.requires = ["qt::qtCore", "qt::qtGui"]
