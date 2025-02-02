import os

from conan import ConanFile
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import apply_conandata_patches, export_conandata_patches, get, copy
from conan.tools.microsoft import is_msvc_static_runtime, is_msvc

required_conan_version = ">=2.0.9"

class QtAwesomeConan(ConanFile):
    name = "qtawesome"
    description = "Font Awesome for Qt Applications"
    license = "MIT"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/gamecreature/QtAwesome"
    topics = ("font", "icons", "qt")
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
        self.requires("qt/[>=5.15 <7]", transitive_headers=True, transitive_libs=True)

    def build_requirements(self):
        self.tool_requires("cmake/[>=3.16 <4]")
        self.tool_requires("qt/<host_version>")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        apply_conandata_patches(self)

    def _qt_tool(self, tool):
        tools_dir = self.dependencies.build["qt"].conf_info.get("user.qt:tools_directory")
        suffix = ".exe" if self.settings_build.os == "Windows" else ""
        return os.path.join(tools_dir, tool + suffix).replace("\\", "/")

    def generate(self):
        tc = CMakeToolchain(self)
        if is_msvc(self):
            tc.cache_variables["USE_MSVC_RUNTIME_LIBRARY_DLL"] = not is_msvc_static_runtime(self)
        tc.cache_variables["CMAKE_POLICY_DEFAULT_CMP0077"] = "NEW"
        tc.cache_variables["CMAKE_AUTOMOC_EXECUTABLE"] = self._qt_tool("moc")
        tc.cache_variables["CMAKE_AUTOUIC_EXECUTABLE"] = self._qt_tool("uic")
        tc.cache_variables["CMAKE_AUTORCC_EXECUTABLE"] = self._qt_tool("rcc")
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

    def package_info(self):
        self.cpp_info.libs = ["QtAwesome"]
