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
from conan.errors import ConanInvalidConfiguration
import contextlib
import os

required_conan_version = ">=1.50.0"


class MpirConan(ConanFile):
    name = "mpir"
    description = (
        "MPIR is a highly optimised library for bignum arithmetic" "forked from the GMP bignum library."
    )
    topics = ("multiprecision", "math", "mathematics")
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "http://mpir.org/"
    license = "LGPL-3.0-or-later"

    provides = []

    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "enable_cxx": [True, False],
        "enable_gmpcompat": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "enable_cxx": True,
        "enable_gmpcompat": True,
    }

    _autotools = None

    @property
    def _settings_build(self):
        return getattr(self, "settings_build", self.settings)

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")
        if is_msvc(self) and self.options.shared:
            self.options.rm_safe("enable_cxx")
        if not self.options.get_safe("enable_cxx", False):
            self.settings.rm_safe("compiler.libcxx")
            self.settings.rm_safe("compiler.cppstd")
        if self.options.enable_gmpcompat:
            self.provides.append("gmp")

    def validate(self):
        if hasattr(self, "settings_build") and cross_building(self, skip_x64_x86=True):
            raise ConanInvalidConfiguration("Cross-building doesn't work (yet)")

    def build_requirements(self):
        self.tool_requires("yasm/1.3.0")
        if not is_msvc(self):
            self.tool_requires("m4/1.4.19")
            if self._settings_build.os == "Windows" and not get_env(self, "CONAN_BASH_PATH"):
                self.tool_requires("msys2/cci.latest")

    def source(self):
        get(
            self,
            keep_permissions=True,
            **self.conan_data["sources"][self.version],
            strip_root=True,
            destination=self.source_folder,
        )

    @property
    def _platforms(self):
        return {
            "x86": "Win32",
            "x86_64": "x64",
        }

    @property
    def _dll_or_lib(self):
        return "dll" if self.options.shared else "lib"

    @property
    def _vcxproj_paths(self):
        compiler_version = (
            self.settings.compiler.version if Version(self.settings.compiler.version) <= "17" else "17"
        )
        build_subdir = "build.vc{}".format(compiler_version)
        vcxproj_paths = [
            os.path.join(
                self.source_folder,
                build_subdir,
                "{}_mpir_gc".format(self._dll_or_lib),
                "{}_mpir_gc.vcxproj".format(self._dll_or_lib),
            )
        ]
        if self.options.get_safe("enable_cxx"):
            vcxproj_paths.append(
                os.path.join(self.source_folder, build_subdir, "lib_mpir_cxx", "lib_mpir_cxx.vcxproj")
            )
        return vcxproj_paths

    def _build_visual_studio(self):
        if not self.options.shared:  # RuntimeLibrary only defined in lib props files
            build_type = "debug" if self.settings.build_type == "Debug" else "release"
            props_path = os.path.join(self.source_folder, "build.vc", "mpir_{}_lib.props".format(build_type))
            old_runtime = "MultiThreaded{}".format("Debug" if build_type == "debug" else "")
            new_runtime = "MultiThreaded{}{}".format(
                "Debug" if "d" in msvc_runtime_flag(self) else "",
                "DLL" if "MD" in msvc_runtime_flag(self) else "",
            )
            replace_in_file(self, props_path, old_runtime, new_runtime)
        msbuild = MSBuild(self)
        for vcxproj_path in self._vcxproj_paths:
            msbuild.build(vcxproj_path, platforms=self._platforms, upgrade_project=False)

    @contextlib.contextmanager
    def _build_context(self):
        if self.settings.compiler == "apple-clang":
            env_build = {"CC": XCRun(self.settings).cc, "CXX": XCRun(self.settings).cxx}
            if hasattr(self, "settings_build"):
                # there is no CFLAGS_FOR_BUILD/CXXFLAGS_FOR_BUILD
                xcrun = XCRun(self.settings_build)
                flags = " -Wno-implicit-function-declaration -isysroot {} -arch {}".format(
                    xcrun.sdk_path, to_apple_arch(self.settings_build.arch)
                )
                env_build["CC_FOR_BUILD"] = xcrun.cc + flags
                env_build["CXX_FOR_BUILD"] = xcrun.cxx + flags
            with environment_append(self, env_build):
                yield
        else:
            yield

    def _configure_autotools(self):
        if not self._autotools:
            self._autotools = AutoToolsBuildEnvironment(self, win_bash=tools.os_info.is_windows)
            args = []
            if self.options.shared:
                args.extend(["--disable-static", "--enable-shared"])
            else:
                args.extend(["--disable-shared", "--enable-static"])
            args.append("--with-pic" if self.options.get_safe("fPIC", True) else "--without-pic")

            args.append("--disable-silent-rules")
            args.append("--enable-cxx" if self.options.get_safe("enable_cxx") else "--disable-cxx")
            args.append("--enable-gmpcompat" if self.options.enable_gmpcompat else "--disable-gmpcompat")

            # compiler checks are written for C89 but compilers that default to C99 treat implicit functions as error
            self._autotools.flags.append("-Wno-implicit-function-declaration")
            self._autotools.configure(args=args)
        return self._autotools

    def _patch_new_msvc_version(self, ver, toolset):
        new_dir = os.path.join(self.source_folder, f"build.vc{ver}")
        copy(self, pattern="*", src=os.path.join(self.source_folder, "build.vc15"), dst=new_dir)

        for root, _, files in os.walk(new_dir):
            for file in files:
                full_file = os.path.join(root, file)
                replace_in_file(
                    self,
                    full_file,
                    "<PlatformToolset>v141</PlatformToolset>",
                    f"<PlatformToolset>{toolset}</PlatformToolset>",
                    strict=False,
                )
                replace_in_file(
                    self,
                    full_file,
                    "prebuild skylake\\avx x64 15",
                    f"prebuild skylake\\avx x64 {ver}",
                    strict=False,
                )
                replace_in_file(
                    self, full_file, "prebuild p3 Win32 15", f"prebuild p3 Win32 {ver}", strict=False
                )
                replace_in_file(
                    self, full_file, "prebuild gc Win32 15", f"prebuild gc Win32 {ver}", strict=False
                )
                replace_in_file(self, full_file, "prebuild gc x64 15", f"prebuild gc x64 {ver}", strict=False)
                replace_in_file(
                    self,
                    full_file,
                    "prebuild haswell\\avx x64 15",
                    f"prebuild haswell\\avx x64 {ver}",
                    strict=False,
                )
                replace_in_file(
                    self, full_file, "prebuild core2 x64 15", f"prebuild core2 x64 {ver}", strict=False
                )
                replace_in_file(
                    self,
                    full_file,
                    'postbuild "$(TargetPath)" 15',
                    f'postbuild "$(TargetPath)" {ver}',
                    strict=False,
                )
                replace_in_file(
                    self,
                    full_file,
                    "check_config $(Platform) $(Configuration) 15",
                    f"check_config $(Platform) $(Configuration) {ver}",
                    strict=False,
                )

    def _patch_sources(self):
        if is_msvc(self):
            self._patch_new_msvc_version(16, "v142")
            self._patch_new_msvc_version(17, "v143")

    def build(self):
        self._patch_sources()
        if is_msvc(self):
            self._build_visual_studio()
        else:
            with chdir(self, self.source_folder), self._build_context():
                # relocatable shared lib on macOS
                replace_in_file(self, "configure", "-install_name \\$rpath/", "-install_name @rpath/")
                autotools = self._configure_autotools()
                autotools.make()

    def package(self):
        copy(
            self,
            "COPYING*",
            dst=os.path.join(self.package_folder, "licenses"),
            src=self.source_folder,
        )
        if is_msvc(self):
            lib_folder = os.path.join(
                self.build_folder,
                self.source_folder,
                self._dll_or_lib,
                self._platforms.get(str(self.settings.arch)),
                str(self.settings.build_type),
            )
            include_folder = os.path.join(self.package_folder, "include")
            copy(self, "mpir.h", dst=include_folder, src=lib_folder, keep_path=True)
            if self.options.enable_gmpcompat:
                copy(self, "gmp.h", dst=include_folder, src=lib_folder, keep_path=True)
            if self.options.get_safe("enable_cxx"):
                copy(self, "mpirxx.h", dst=include_folder, src=lib_folder, keep_path=True)
                if self.options.enable_gmpcompat:
                    copy(self, "gmpxx.h", dst=include_folder, src=lib_folder, keep_path=True)
            copy(
                self,
                pattern="*.dll*",
                dst=os.path.join(self.package_folder, "bin"),
                src=lib_folder,
                keep_path=False,
            )
            copy(
                self,
                pattern="*.lib",
                dst=os.path.join(self.package_folder, "lib"),
                src=lib_folder,
                keep_path=False,
            )
        else:
            with chdir(self, self.source_folder), self._build_context():
                autotools = self._configure_autotools()
                autotools.install()
            rmdir(self, os.path.join(self.package_folder, "share"))
            rm(self, "*.la", os.path.join(self.package_folder, "lib"))

    def package_info(self):
        if self.options.get_safe("enable_cxx"):
            self.cpp_info.libs.append("mpirxx")
        self.cpp_info.libs.append("mpir")
        if self.options.enable_gmpcompat and not is_msvc(self):
            if self.options.get_safe("enable_cxx"):
                self.cpp_info.libs.append("gmpxx")
            self.cpp_info.libs.append("gmp")
        if self.settings.os == "Windows" and self.options.shared:
            self.cpp_info.defines.append("MSC_USE_DLL")
