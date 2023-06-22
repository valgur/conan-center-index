# TODO: verify the Conan v2 migration

import os

from conan import ConanFile, conan_version
from conan.errors import ConanInvalidConfiguration, ConanException
from conan.tools.android import android_abi
from conan.tools.apple import (
    XCRun,
    fix_apple_shared_install_name,
    is_apple_os,
    to_apple_arch,
)
from conan.tools.build import (
    build_jobs,
    can_run,
    check_min_cppstd,
    cross_building,
    default_cppstd,
    stdcpp_library,
    valid_min_cppstd,
)
from conan.tools.cmake import (
    CMake,
    CMakeDeps,
    CMakeToolchain,
    cmake_layout,
)
from conan.tools.env import (
    Environment,
    VirtualBuildEnv,
    VirtualRunEnv,
)
from conan.tools.files import (
    apply_conandata_patches,
    chdir,
    collect_libs,
    copy,
    download,
    export_conandata_patches,
    get,
    load,
    mkdir,
    patch,
    patches,
    rename,
    replace_in_file,
    rm,
    rmdir,
    save,
    symlinks,
    unzip,
)
from conan.tools.gnu import (
    Autotools,
    AutotoolsDeps,
    AutotoolsToolchain,
    PkgConfig,
    PkgConfigDeps,
)
from conan.tools.layout import basic_layout
from conan.tools.meson import MesonToolchain, Meson
from conan.tools.microsoft import (
    MSBuild,
    MSBuildDeps,
    MSBuildToolchain,
    NMakeDeps,
    NMakeToolchain,
    VCVars,
    check_min_vs,
    is_msvc,
    is_msvc_static_runtime,
    msvc_runtime_flag,
    unix_path,
    unix_path_package_info_legacy,
    vs_layout,
)
from conan.tools.microsoft.visual import vs_ide_version
from conan.tools.scm import Version
from conan.tools.system import package_manager
from conan.tools.cmake import (
    CMake,
    CMakeDeps,
    CMakeToolchain,
    cmake_layout,
)

required_conan_version = ">=1.33.0"


class DatadogOpenTracingConan(ConanFile):
    name = "dd-opentracing-cpp"
    description = "Monitoring service for cloud-scale applications based on OpenTracing "
    license = "Apache-2.0"
    topics = ("instrumentration", "monitoring", "security", "tracing")
    homepage = "https://github.com/DataDog/dd-opentracing-cpp"
    url = "https://github.com/conan-io/conan-center-index"

    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
    }

    generators = "cmake", "cmake_find_package"
    _cmake = None

    @property
    def _build_subfolder(self):
        return "build_subfolder"

    @property
    def _compilers_minimum_version(self):
        return {
            "gcc": "5",
            "Visual Studio": "15",
            "clang": "3.4",
            "apple-clang": "7",
        }

    def export_sources(self):
        self.copy("CMakeLists.txt")
        for patch in self.conan_data.get("patches", {}).get(self.version, []):
            self.copy(patch["patch_file"])

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            del self.options.fPIC

    def requirements(self):
        self.requires("opentracing-cpp/1.6.0")
        self.requires("zlib/1.2.11")
        self.requires("libcurl/7.80.0")
        self.requires("msgpack/3.3.0")
        self.requires("nlohmann_json/3.10.5")

    def validate(self):
        if self.settings.compiler.get_safe("cppstd"):
            tools.check_min_cppstd(self, 14)

        minimum_version = self._compilers_minimum_version.get(str(self.settings.compiler), False)
        if minimum_version:
            if tools.Version(self.settings.compiler.version) < minimum_version:
                raise ConanInvalidConfiguration(
                    "Datadog-opentracing requires C++14, which your compiler does not support."
                )
        else:
            self.output.warn(
                "Datadog-opentracing requires C++14. Your compiler is unknown. Assuming it supports C++14."
            )

    def source(self):
        tools.get(
            **self.conan_data["sources"][self.version], strip_root=True, destination=self._source_subfolder
        )

    def build(self):
        for patch in self.conan_data.get("patches", {}).get(self.version, []):
            tools.patch(**patch)
        cmake = self._configure_cmake()
        cmake.build()

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["BUILD_PLUGIN"] = False
        tc.variables["BUILD_SHARED"] = self.options.shared
        tc.variables["BUILD_STATIC"] = not self.options.shared
        tc.variables["BUILD_TESTING"] = False
        self._cmake.configure(build_folder=self._build_subfolder)
        return self._cmake

    def package(self):
        self.copy("LICENSE", dst="licenses", src=self._source_subfolder)
        cmake = self._configure_cmake()
        cmake.install()

    def package_info(self):
        # TODO: back to global scope in conan v2 once cmake_find_package_* generators removed
        self.cpp_info.components["dd_opentracing"].libs = ["dd_opentracing"]
        self.cpp_info.components["dd_opentracing"].defines.append(
            "DD_OPENTRACING_SHARED" if self.options.shared else "DD_OPENTRACING_STATIC"
        )
        if self.settings.os in ("Linux", "FreeBSD"):
            self.cpp_info.components["dd_opentracing"].system_libs.append("pthread")

        # TODO: to remove in conan v2 once cmake_find_package_* generators removed.
        #       Do not support these names in CMakeDeps, it was a mistake, upstream doesn't export targets
        self.cpp_info.names["cmake_find_package"] = "DataDogOpenTracing"
        self.cpp_info.names["cmake_find_package_multi"] = "DataDogOpenTracing"
        target_suffix = "" if self.options.shared else "-static"
        self.cpp_info.components["dd_opentracing"].names["cmake_find_package"] = (
            "dd_opentracing" + target_suffix
        )
        self.cpp_info.components["dd_opentracing"].names["cmake_find_package_multi"] = (
            "dd_opentracing" + target_suffix
        )
        self.cpp_info.components["dd_opentracing"].requires = [
            "opentracing-cpp::opentracing-cpp",
            "zlib::zlib",
            "libcurl::libcurl",
            "msgpack::msgpack",
            "nlohmann_json::nlohmann_json",
        ]
