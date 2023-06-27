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
from conan.tools.scm import Version
from conan.tools.system import package_manager
import contextlib
import functools
import os

required_conan_version = ">=1.47.0"


class NsprConan(ConanFile):
    name = "nspr"
    homepage = "https://developer.mozilla.org/en-US/docs/Mozilla/Projects/NSPR"
    description = "Netscape Portable Runtime (NSPR) provides a platform-neutral API for system level and libc-like functions."
    topics = "libc"
    url = "https://github.com/conan-io/conan-center-index"
    license = "MPL-2.0"

    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "with_mozilla": [True, False],
        "win32_target": ["winnt", "win95"],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "with_mozilla": True,
        "win32_target": "winnt",
    }

    @property
    def _settings_build(self):
        return getattr(self, "settings_build", self.settings)

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC
        else:
            self.options.rm_safe("win32_target")

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")
        self.settings.rm_safe("compiler.cppstd")
        self.settings.rm_safe("compiler.libcxx")

    def validate(self):
        # https://bugzilla.mozilla.org/show_bug.cgi?id=1658671
        if Version(self.version) < "4.29":
            if self.settings.os == "Macos" and self.settings.arch == "armv8":
                raise ConanInvalidConfiguration("NSPR does not support mac M1 before 4.29")

    def build_requirements(self):
        if self._settings_build.os == "Windows":
            self.build_requires("mozilla-build/3.3")
            if not get_env(self, "CONAN_BASH_PATH"):
                self.build_requires("msys2/cci.latest")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], destination="tmp", strip_root=True)
        rename(self, os.path.join("tmp", "nspr"), self.source_folder)
        rmdir(self, "tmp")

    @contextlib.contextmanager
    def _build_context(self):
        if is_msvc(self):
            with vcvars(self):
                with environment_append(
                    self,
                    {
                        "CC": "cl",
                        "CXX": "cl",
                        "LD": "link",
                    },
                ):
                    yield
        else:
            yield

    @functools.lru_cache(1)
    def _configure_autotools(self):
        autotools = AutoToolsBuildEnvironment(self, win_bash=tools.os_info.is_windows)
        yes_no = lambda v: "yes" if v else "no"
        conf_args = [
            "--with-mozilla={}".format(yes_no(self.options.with_mozilla)),
            "--enable-64bit={}".format(
                yes_no(self.settings.arch in ("armv8", "x86_64", "mips64", "ppc64", "ppc64le"))
            ),
            "--enable-strip={}".format(yes_no(self.settings.build_type not in ("Debug", "RelWithDebInfo"))),
            "--enable-debug={}".format(yes_no(self.settings.build_type == "Debug")),
            "--datarootdir={}".format(unix_path(self, os.path.join(self.package_folder, "res"))),
            "--disable-cplus",
        ]
        if is_msvc(self):
            conf_args.extend(
                [
                    "{}-pc-mingw32".format("x86_64" if self.settings.arch == "x86_64" else "x86"),
                    "--enable-static-rtl={}".format(yes_no("MT" in msvc_runtime_flag(self))),
                    "--enable-debug-rtl={}".format(yes_no("d" in msvc_runtime_flag(self))),
                ]
            )
        elif self.settings.os == "Android":
            conf_args.extend(
                [
                    "--with-android-ndk={}".format(get_env(self, ["NDK_ROOT"])),
                    "--with-android-version={}".format(self.settings.os.api_level),
                    "--with-android-platform={}".format(get_env(self, "ANDROID_PLATFORM")),
                    "--with-android-toolchain={}".format(get_env(self, "ANDROID_TOOLCHAIN")),
                ]
            )
        elif self.settings.os == "Windows":
            conf_args.append("--enable-win32-target={}".format(self.options.win32_target))
        env = autotools.vars
        if self.settings.os == "Macos":
            if self.settings.arch == "armv8":
                # conan adds `-arch`, which conflicts with nspr's apple silicon support
                env["CFLAGS"] = env["CFLAGS"].replace("-arch arm64", "")
                env["CXXFLAGS"] = env["CXXFLAGS"].replace("-arch arm64", "")

        autotools.configure(args=conf_args, vars=env)
        return autotools

    def build(self):
        with chdir(self, self.source_folder):
            # relocatable shared libs on macOS
            replace_in_file(self, "configure", "-install_name @executable_path/", "-install_name @rpath/")
            with self._build_context():
                autotools = self._configure_autotools()
                autotools.make()

    def package(self):
        copy(
            self, pattern="LICENSE", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder
        )
        with chdir(self, self.source_folder):
            with self._build_context():
                autotools = self._configure_autotools()
                autotools.install()
        rmdir(self, os.path.join(self.package_folder, "bin"))
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))
        rmdir(self, os.path.join(self.package_folder, "share"))
        if self.settings.os == "Windows":
            if self.options.shared:
                os.mkdir(os.path.join(self.package_folder, "bin"))
            for lib in self._library_names:
                libsuffix = "lib" if is_msvc(self) else "a"
                libprefix = "" if is_msvc(self) else "lib"
                if self.options.shared:
                    os.unlink(os.path.join(self.package_folder, "lib", f"{libprefix}{lib}_s.{libsuffix}"))
                    rename(
                        self,
                        os.path.join(self.package_folder, "lib", f"{lib}.dll"),
                        os.path.join(self.package_folder, "bin", f"{lib}.dll"),
                    )
                else:
                    os.unlink(os.path.join(self.package_folder, "lib", f"{libprefix}{lib}.{libsuffix}"))
                    os.unlink(os.path.join(self.package_folder, "lib", f"{lib}.dll"))
            if not self.options.shared:
                replace_in_file(
                    self,
                    os.path.join(self.package_folder, "include", "nspr", "prtypes.h"),
                    "#define NSPR_API(__type) PR_IMPORT(__type)",
                    "#define NSPR_API(__type) extern __type",
                )
                replace_in_file(
                    self,
                    os.path.join(self.package_folder, "include", "nspr", "prtypes.h"),
                    "#define NSPR_DATA_API(__type) PR_IMPORT_DATA(__type)",
                    "#define NSPR_DATA_API(__type) extern __type",
                )
        else:
            shared_ext = "dylib" if self.settings.os == "Macos" else "so"
            for lib in self._library_names:
                if self.options.shared:
                    os.unlink(os.path.join(self.package_folder, "lib", f"lib{lib}.a"))
                else:
                    os.unlink(os.path.join(self.package_folder, "lib", f"lib{lib}.{shared_ext}"))

        if is_msvc(self):
            if self.settings.build_type == "Debug":
                for lib in self._library_names:
                    os.unlink(os.path.join(self.package_folder, "lib", f"{lib}.pdb"))

        if not self.options.shared or self.settings.os == "Windows":
            for f in os.listdir(os.path.join(self.package_folder, "lib")):
                os.chmod(os.path.join(self.package_folder, "lib", f), 0o644)

    @property
    def _library_names(self):
        return ["plds4", "plc4", "nspr4"]

    def package_info(self):
        self.cpp_info.set_property("pkg_config_name", "nspr")
        libs = self._library_names
        if self.settings.os == "Windows" and not self.options.shared:
            libs = list(f"{l}_s" for l in libs)
        self.cpp_info.libs = libs
        if self.settings.compiler == "gcc" and self.settings.os == "Windows":
            if self.settings.arch == "x86":
                self.cpp_info.defines.append("_M_IX86")
            elif self.settings.arch == "x86_64":
                self.cpp_info.defines.append("_M_X64")
        self.cpp_info.includedirs.append(os.path.join("include", "nspr"))
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs.extend(["dl", "pthread", "rt"])
        elif self.settings.os == "Windows":
            self.cpp_info.system_libs.extend(["winmm", "ws2_32"])

        aclocal = unix_path(self, os.path.join(self.package_folder, "res", "aclocal"))
        self.output.info(f"Appending AUTOMAKE_CONAN_INCLUDES environment variable: {aclocal}")
        self.env_info.AUTOMAKE_CONAN_INCLUDES.append(aclocal)

        self.cpp_info.resdirs = ["res"]
