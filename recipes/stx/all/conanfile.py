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

required_conan_version = ">=1.33.0"


class STXConan(ConanFile):
    name = "stx"
    homepage = "https://github.com/lamarrr/STX"
    license = "MIT"
    url = "https://github.com/conan-io/conan-center-index"
    description = "C++17 & C++ 20 error-handling and utility extensions."
    topics = ("error-handling", "result", "option", "backtrace", "panic")

    settings = "os", "compiler", "build_type", "arch"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "backtrace": [True, False],
        "panic_handler": [None, "default", "backtrace"],
        "visible_panic_hook": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "backtrace": False,
        "panic_handler": "default",
        "visible_panic_hook": False,
    }

    exports_sources = ["CMakeLists.txt", "patches/*"]

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")

    def requirements(self):
        if self.options.backtrace:
            self.requires("abseil/20200923.1")

    def validate(self):
        if self.options.panic_handler == "backtrace" and not self.options.backtrace:
            raise ConanInvalidConfiguration("panic_handler=backtrace requires backtrace=True")

        compiler = self.settings.compiler
        compiler_version = Version(self.settings.compiler.version)

        if compiler.get_safe("cppstd"):
            check_min_cppstd(self, 17)

        if compiler == "Visual Studio" and compiler_version < 16:
            raise ConanInvalidConfiguration(
                "STX requires C++17 language and standard library features " "which VS < 2019 lacks"
            )

        if compiler == "gcc" and compiler_version < 8:
            raise ConanInvalidConfiguration(
                "STX requires C++17 language and standard library features " "which GCC < 8 lacks"
            )

        if (
            compiler == "clang"
            and compiler.libcxx
            and compiler.libcxx in ["libstdc++", "libstdc++11"]
            and compiler_version < 9
        ):
            raise ConanInvalidConfiguration(
                "STX requires C++17 language and standard library features "
                "which clang < 9 with libc++ lacks"
            )

        if compiler == "clang" and compiler.libcxx and compiler.libcxx == "libc++" and compiler_version < 10:
            raise ConanInvalidConfiguration(
                "STX requires C++17 language and standard library features "
                "which clang < 10 with libc++ lacks"
            )

        if compiler == "apple-clang" and compiler_version < 12:
            raise ConanInvalidConfiguration(
                "STX requires C++17 language and standard library features "
                "which apple-clang < 12 with libc++ lacks"
            )

        if compiler == "Visual Studio" and self.options.shared and Version(self.version) <= "1.0.1":
            raise ConanInvalidConfiguration(
                "shared library build does not work on windows with " "STX version <= 1.0.1"
            )

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["STX_BUILD_SHARED"] = self.options.shared
        tc.variables["STX_ENABLE_BACKTRACE"] = self.options.backtrace
        tc.variables["STX_ENABLE_PANIC_BACKTRACE"] = self.options.panic_handler == "backtrace"
        tc.variables["STX_OVERRIDE_PANIC_HANDLER"] = self.options.panic_handler == None
        tc.variables["STX_VISIBLE_PANIC_HOOK"] = self.options.visible_panic_hook
        tc.generate()

        tc = CMakeDeps(self)
        tc.generate()

    def build(self):
        apply_conandata_patches(self)
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "*.h", dst="include", src=os.path.join(self.source_folder, "include"))

        copy(self, "*.lib", dst="lib", keep_path=False)
        copy(self, "*.dll", dst="bin", keep_path=False)
        copy(self, "*.so", dst="lib", keep_path=False)
        copy(self, "*.dylib", dst="lib", keep_path=False)
        copy(self, "*.a", dst="lib", keep_path=False)

        copy(self, "LICENSE", dst="licenses", src=self.source_folder)

    def package_info(self):
        self.cpp_info.libs = collect_libs(self)

        if self.options.backtrace:
            self.cpp_info.requires = ["abseil::absl_stacktrace", "abseil::absl_symbolize"]

        if self.options.visible_panic_hook:
            self.cpp_info.defines.append("STX_VISIBLE_PANIC_HOOK")

        if self.options.panic_handler == None:
            self.cpp_info.defines.append("STX_OVERRIDE_PANIC_HANDLER")

        if self.options.panic_handler == "backtrace":
            self.cpp_info.defines.append("STX_ENABLE_PANIC_BACKTRACE")

        if self.settings.os == "Android":
            self.cpp_info.system_libs = ["atomic"]
