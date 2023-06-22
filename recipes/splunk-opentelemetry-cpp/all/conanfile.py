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
import os
import glob


class SplunkOpentelemetryConan(ConanFile):
    name = "splunk-opentelemetry-cpp"
    license = "Apache-2.0"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/signalfx/splunk-otel-cpp"
    description = "Splunk's distribution of OpenTelemetry C++"
    topics = ("opentelemetry", "observability", "tracing")
    settings = "os", "compiler", "build_type", "arch"
    options = {
        "fPIC": [True, False],
        "shared": [True, False],
    }
    default_options = {
        "fPIC": True,
        "shared": False,
    }

    def validate(self):
        if self.settings.arch != "x86_64":
            raise ConanInvalidConfiguration("Architecture not supported")

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def requirements(self):
        self.requires("opentelemetry-cpp/1.0.1")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["SPLUNK_CPP_EXAMPLES"] = False
        tc.generate()
        tc = CMakeDeps(self)
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def _remove_unnecessary_package_files(self):
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))

    def package(self):
        copy(
            self, pattern="LICENSE", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder
        )
        cmake = CMake(self)
        cmake.install()
        self._remove_unnecessary_package_files()

    def package_info(self):
        self.cpp_info.names["cmake_find_package"] = "SplunkOpenTelemetry"
        self.cpp_info.names["cmake_find_package_multi"] = "SplunkOpenTelemetry"
        self.cpp_info.libs = ["SplunkOpenTelemetry"]
