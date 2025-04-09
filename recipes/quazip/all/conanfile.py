import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import *
from conan.tools.microsoft import is_msvc_static_runtime, is_msvc
from conan.tools.scm import Version

required_conan_version = ">=2.1"


class QuaZIPConan(ConanFile):
    name = "quazip"
    description = (
        "A simple C++ wrapper over Gilles Vollant's ZIP/UNZIP package "
        "that can be used to access ZIP archives."
    )
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/stachenov/quazip"
    license = "LGPL-2.1-linking-exception"
    topics = ("zip", "unzip", "compress")
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
    def _qt_major(self):
        return Version(self.dependencies["qt"].ref.version).major

    def export_sources(self):
        export_conandata_patches(self)

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires("qt/[~5.15]", transitive_headers=True, transitive_libs=True)
        self.requires("zlib/[>=1.2.11 <2]", transitive_headers=True)
        if Version(self.version) >= "1.4":
            self.requires("bzip2/1.0.8")

    def validate(self):
        if self.dependencies["qt"].ref.version.major == 6 and not self.dependencies["qt"].options.qt5compat:
            raise ConanInvalidConfiguration("QuaZip does not support Qt 6 without the qt5compat option enabled")

    def build_requirements(self):
        self.tool_requires("cmake/[>=3.27 <4]")
        self.tool_requires("qt/<host_version>")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        apply_conandata_patches(self)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["QUAZIP_QT_MAJOR_VERSION"] = self._qt_major
        if is_msvc(self):
            tc.variables["USE_MSVC_RUNTIME_LIBRARY_DLL"] = not is_msvc_static_runtime(self)
        tc.cache_variables["CMAKE_POLICY_DEFAULT_CMP0077"] = "NEW"
        tc.generate()
        deps = CMakeDeps(self)
        deps.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "COPYING", self.source_folder, os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))

    def package_info(self):
        quazip_major = Version(self.version).major
        self.cpp_info.set_property("cmake_file_name", f"QuaZip-Qt{self._qt_major}")
        self.cpp_info.set_property("cmake_target_name", "QuaZip::QuaZip")
        self.cpp_info.set_property("pkg_config_name", f"quazip{quazip_major}-qt{self._qt_major}")
        suffix = "d" if self.settings.build_type == "Debug" else ""
        self.cpp_info.libs = [f"quazip{quazip_major}-qt{self._qt_major}{suffix}"]
        self.cpp_info.includedirs = [os.path.join("include", f"QuaZip-Qt{self._qt_major}-{self.version}")]
        if not self.options.shared:
            self.cpp_info.defines.append("QUAZIP_STATIC")
