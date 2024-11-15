import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import apply_conandata_patches, export_conandata_patches, get, copy, rm, rmdir
from conan.tools.microsoft import check_min_vs, is_msvc_static_runtime, is_msvc
from conan.tools.scm import Version

required_conan_version = ">=1.53.0"


class EasyProfilerConan(ConanFile):
    name = "easy_profiler"
    description = "Lightweight profiler library for c++"
    license = "MIT"
    topics = ("profiler")
    homepage = "https://github.com/yse/easy_profiler/"
    url = "https://github.com/conan-io/conan-center-index"

    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False]
    }
    default_options = {
        "shared": False,
        "fPIC": True
    }

    @property
    def _min_cppstd(self):
        return 11

    @property
    def _compilers_minimum_version(self):
        return {
            "gcc": "4.8",
            "clang": "3.3",
            "apple-clang": "8.0",
        }

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def export_sources(self):
        export_conandata_patches(self)

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")

    def layout(self):
        cmake_layout(self, src_folder="src")

    def validate(self):
        check_min_cppstd(self, self._min_cppstd)
        check_min_vs(self, 191)
        if not is_msvc(self):
            minimum_version = self._compilers_minimum_version.get(str(self.settings.compiler), False)
            if minimum_version and Version(self.settings.compiler.version) < minimum_version:
                raise ConanInvalidConfiguration(
                    f"{self.ref} requires C++{self._min_cppstd}, which your compiler does not support."
                )
        if is_msvc_static_runtime(self) and self.options.shared:
            raise ConanInvalidConfiguration(
                "{} {} with static runtime not supported".format(self.settings.compiler,
                                                                 self.settings.compiler.version)
            )

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["EASY_PROFILER_NO_GUI"] = True
        tc.variables["EASY_PROFILER_NO_SAMPLES"] = True
        tc.generate()

        deps = CMakeDeps(self)
        deps.generate()

    def build(self):
        apply_conandata_patches(self)
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, pattern="LICENSE", dst=os.path.join(self.package_folder,"licenses"), src=self.source_folder)
        copy(self, pattern="LICENSE.MIT", dst=os.path.join(self.package_folder,"licenses"), src=self.source_folder)
        copy(self, pattern="LICENSE.APACHE", dst=os.path.join(self.package_folder,"licenses"), src=self.source_folder)
        cmake = CMake(self)
        cmake.install()

        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))
        rm(self, "LICENSE.MIT", self.package_folder)
        rm(self, "LICENSE.APACHE", self.package_folder)
        if self.settings.os == "Windows":
            for dll_prefix in ["concrt", "msvcp", "vcruntime"]:
                rm(self, "{}*.dll".format(dll_prefix), os.path.join(self.package_folder, "bin"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "easy_profiler")
        self.cpp_info.set_property("cmake_target_name", "easy_profiler")

        self.cpp_info.libs = ["easy_profiler"]
        self.cpp_info.builddirs.append(self._module_subfolder)
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs = ["m", "pthread"]
        elif self.settings.os == "Windows":
            self.cpp_info.system_libs = ["psapi", "ws2_32"]
            if not self.options.shared:
                self.cpp_info.defines.append("EASY_PROFILER_STATIC")
