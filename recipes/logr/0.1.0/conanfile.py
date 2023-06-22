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
import os


class LogrConan(ConanFile):
    name = "logr"
    license = "BSD 3-Clause License"
    homepage = "https://github.com/ngrodzitski/logr"
    url = "https://github.com/conan-io/conan-center-index"
    description = "Logger frontend substitution for spdlog, glog, etc for server/desktop applications"
    topics = ("logger", "development", "util", "utils")
    settings = "os", "compiler", "build_type", "arch"

    options = {"backend": ["spdlog", "glog", "log4cplus", "log4cplus-unicode", None]}
    default_options = {
        "backend": "spdlog",
    }

    def requirements(self):
        self.requires("fmt/7.1.2")

        if self.options.backend == "spdlog":
            self.requires("spdlog/1.8.0")
        elif self.options.backend == "glog":
            self.requires("glog/0.4.0")
        elif self.options.backend == "log4cplus":
            self.requires("log4cplus/2.0.5")
        elif self.options.backend == "log4cplus-unicode":
            self.requires("log4cplus/2.0.5")

    def configure(self):
        minimal_cpp_standard = "17"
        if self.settings.compiler.cppstd:
            check_min_cppstd(self, minimal_cpp_standard)
        minimal_version = {
            "gcc": "7",
            "clang": "7",
            "apple-clang": "10",
            "Visual Studio": "16",
        }
        compiler = str(self.settings.compiler)
        if compiler not in minimal_version:
            self.output.warn(
                "%s recipe lacks information about the %s compiler standard version support"
                % (self.name, compiler)
            )
            self.output.warn(
                "%s requires a compiler that supports at least C++%s" % (self.name, minimal_cpp_standard)
            )
            return

        version = Version(self.settings.compiler.version)
        if version < minimal_version[compiler]:
            raise ConanInvalidConfiguration(
                "%s requires a compiler that supports at least C++%s" % (self.name, minimal_cpp_standard)
            )

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["LOGR_WITH_SPDLOG_BACKEND"] = self.options.backend == "spdlog"
        tc.variables["LOGR_WITH_GLOG_BACKEND"] = self.options.backend == "glog"
        tc.variables["LOGR_WITH_LOG4CPLUS_BACKEND"] = self.options.backend in [
            "log4cplus",
            "log4cplus-unicode",
        ]

        tc.variables["LOGR_INSTALL"] = True

        tc.generate()

        tc = CMakeDeps(self)
        tc.generate()

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        extracted_dir = self.name + "-" + self.version
        os.rename(extracted_dir, self.source_folder)

    def build(self):
        if self.options.backend == "log4cplus" and self.options["log4cplus"].unicode:
            raise ConanInvalidConfiguration("backend='log4cplus' requires log4cplus:unicode=False")
        elif self.options.backend == "log4cplus-unicode" and not self.options["log4cplus"].unicode:
            raise ConanInvalidConfiguration("backend='log4cplus-unicode' requires log4cplus:unicode=True")

    def package(self):
        copy(self, "LICENSE", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()

        rmdir(self, os.path.join(self.package_folder, "lib"))

    def package_id(self):
        self.info.header_only()
