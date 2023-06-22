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


class DjinniSuppotLib(ConanFile):
    name = "djinni-support-lib"
    homepage = "https://djinni.xlcpp.dev"
    url = "https://github.com/conan-io/conan-center-index"
    description = "Djinni is a tool for generating cross-language type declarations and interface bindings"
    topics = ("java", "Objective-C", "Android", "iOS")
    license = "Apache-2.0"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "target": ["jni", "objc", "auto"],
        "system_java": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "target": "auto",
        "system_java": False,
    }

    def export_sources(self):
        export_conandata_patches(self)

    @property
    def objc_support(self):
        if self.options.target == "auto":
            return is_apple_os(self.settings.os)
        else:
            return self.options.target == "objc"

    @property
    def jni_support(self):
        if self.options.target == "auto":
            return self.settings.os not in ["iOS", "watchOS", "tvOS"]
        else:
            return self.options.target == "jni"

    def build_requirements(self):
        if not self.options.system_java:
            self.build_requires("zulu-openjdk/11.0.8@")

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["CMAKE_WINDOWS_EXPORT_ALL_SYMBOLS"] = True
        if not self.options.shared:
            tc.variables["DJINNI_STATIC_LIB"] = True
        tc.variables["DJINNI_WITH_OBJC"] = self.objc_support
        tc.variables["DJINNI_WITH_JNI"] = self.jni_support
        if self.jni_support:
            tc.variables["JAVA_AWT_LIBRARY"] = "NotNeeded"
            tc.variables["JAVA_AWT_INCLUDE_PATH"] = "NotNeeded"
        tc.generate()

        tc = CMakeDeps(self)
        tc.generate()

    def build(self):
        apply_conandata_patches(self)
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        cmake = CMake(self)
        cmake.install()
        copy(self, "LICENSE", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder)

    def package_info(self):
        self.cpp_info.libs = collect_libs(self)
        # these should not be here, but to support old generated files ....
        if self.objc_support:
            self.cpp_info.includedirs.append(os.path.join("include", "djinni", "objc"))
        if self.jni_support:
            self.cpp_info.includedirs.append(os.path.join("include", "djinni", "jni"))
