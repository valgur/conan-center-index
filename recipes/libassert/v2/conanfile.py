import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeToolchain, CMakeDeps, cmake_layout
from conan.tools.files import *
from conan.tools.microsoft import check_min_vs, is_msvc_static_runtime, is_msvc
from conan.tools.scm import Version

required_conan_version = ">=2.1"

class LibassertConan(ConanFile):
    name = "libassert"
    description = "The most over-engineered C++ assertion library"
    license = "MIT"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/jeremy-rifkin/libassert"
    topics = ("assert", "library", "assertions", "stacktrace", "diagnostics", "defensive programming", "testing")
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
    def _min_cppstd(self):
        return 17

    @property
    def _compilers_minimum_version(self):
        return {
            "gcc": "8",
            "clang": "9"
        }

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        if Version(self.version) >= "2.1.2":
            self.requires("cpptrace/0.7.2", transitive_headers=True, transitive_libs=True)
        else:
            self.requires("cpptrace/0.7.1", transitive_headers=True, transitive_libs=True)

    def validate(self):
        check_min_cppstd(self, self._min_cppstd)

        check_min_vs(self, 192)
        if not is_msvc(self):
            minimum_version = self._compilers_minimum_version.get(str(self.settings.compiler), False)
            if minimum_version and Version(self.settings.compiler.version) < minimum_version:
                raise ConanInvalidConfiguration(f"{self.ref} requires C++{self._min_cppstd}, which your compiler does not support.")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        apply_conandata_patches(self)

    def export_sources(self):
        export_conandata_patches(self)

    def generate(self):
        tc = CMakeToolchain(self)

        if is_msvc(self):
            tc.variables["USE_MSVC_RUNTIME_LIBRARY_DLL"] = not is_msvc_static_runtime(self)

        tc.variables["LIBASSERT_USE_EXTERNAL_CPPTRACE"] = True
        deps = CMakeDeps(self)
        deps.generate()

        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, pattern="LICENSE",
             dst=os.path.join(self.package_folder, "licenses"),
             src=self.source_folder)
        cmake = CMake(self)
        cmake.install()

        if self.settings.os == "Windows" and self.options.shared:
            copy(
                self,
                "*.dll",
                src=self.build_folder,
                dst=os.path.join(self.package_folder, "bin"),
                keep_path=False
            )

        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))

    def package_info(self):
        self.cpp_info.libs = ["assert"]

        self.cpp_info.set_property("cmake_file_name", "libassert")
        self.cpp_info.set_property("cmake_target_name", "libassert::assert")

        # the first version of this library used assert/assert as include folder
        # appending this one but not removing the default to not break consumers
        self.cpp_info.includedirs.append(os.path.join("include", "libassert"))

        self.cpp_info.components["assert"].requires = ["cpptrace::cpptrace"]
        self.cpp_info.components["assert"].libs = ["assert"]
        if not self.options.shared:
            self.cpp_info.components["assert"].defines.append("LIBASSERT_STATIC_DEFINE")

        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs.append("m")
        self.cpp_info.requires = ["cpptrace::cpptrace"]
