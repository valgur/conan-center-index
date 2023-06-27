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
from contextlib import contextmanager
from conan.tools.cmake import (
    CMake,
    CMakeDeps,
    CMakeToolchain,
    cmake_layout,
)
import os
import re
import shlex
import shutil

required_conan_version = ">=1.33.0"


class LibUSBCompatConan(ConanFile):
    name = "libusb-compat"
    description = "A compatibility layer allowing applications written for libusb-0.1 to work with libusb-1.0"
    license = ("LGPL-2.1", "BSD-3-Clause")
    homepage = "https://github.com/libusb/libusb-compat-0.1"
    url = "https://github.com/conan-io/conan-center-index"
    topics = ("libusb", "compatibility", "usb")
    settings = "os", "compiler", "build_type", "arch"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "enable_logging": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "enable_logging": False,
    }

    def export_sources(self):
        copy(self, "CMakeLists.txt.in", src=self.recipe_folder, dst=self.export_sources_folder)

    def export_sources(self):
        export_conandata_patches(self)

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")
        self.settings.rm_safe("compiler.libcxx")
        self.settings.rm_safe("compiler.cppstd")

    def requirements(self):
        self.requires("libusb/1.0.24")
        if self.settings.compiler == "Visual Studio":
            self.requires("dirent/1.23.2")

    @property
    def _settings_build(self):
        return self.settings_build if hasattr(self, "settings_build") else self.settings

    def build_requirements(self):
        self.build_requires("gnu-config/cci.20201022")
        self.build_requires("libtool/2.4.6")
        self.build_requires("pkgconf/1.7.4")
        if self._settings_build.os == "Windows" and not get_env(self, "CONAN_BASH_PATH"):
            self.build_requires("msys2/cci.latest")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def _iterate_lib_paths_win(self, lib):
        """Return all possible library paths for lib"""
        for lib_path in self.deps_cpp_info.libdirs:
            for prefix in "", "lib":
                for suffix in "", ".a", ".dll.a", ".lib", ".dll.lib":
                    fn = os.path.join(lib_path, "{}{}{}".format(prefix, lib, suffix))
                    if not fn.endswith(".a") and not fn.endswith(".lib"):
                        continue
                    yield fn

    @property
    def _absolute_dep_libs_win(self):
        absolute_libs = []
        for lib in self.deps_cpp_info.libs:
            for fn in self._iterate_lib_paths_win(lib):
                if not os.path.isfile(fn):
                    continue
                absolute_libs.append(fn)
                break
        return absolute_libs

    def generate(self):
        tc = CMakeToolchain(self, source_dir=os.path.join(self.source_folder, "libusb"))
        tc.generate()
        tc = CMakeDeps(self)
        tc.generate()
        tc = PkgConfigDeps(self)
        tc.generate()

    def _configure_autotools(self):
        if self._autotools:
            return self._autotools
        self._autotools = AutoToolsBuildEnvironment(self, win_bash=tools.os_info.is_windows)
        if self.settings.compiler == "Visual Studio":
            # Use absolute paths of the libraries instead of the library names only.
            # Otherwise, the configure script will say that the compiler not working
            # (because it interprets the libs as input source files)
            self._autotools.libs = (
                list(unix_path(self, l) for l in self._absolute_dep_libs_win) + self.deps_cpp_info.system_libs
            )
        conf_args = [
            "--disable-examples-build",
            "--enable-log" if self.options.enable_logging else "--disable-log",
        ]
        if self.options.shared:
            conf_args.extend(["--enable-shared", "--disable-static"])
        else:
            conf_args.extend(["--disable-shared", "--enable-static"])
        pkg_config_paths = [unix_path(self, os.path.abspath(self.install_folder))]
        self._autotools.configure(
            args=conf_args, configure_dir=self.source_folder, pkg_config_paths=pkg_config_paths
        )
        return self._autotools

    @contextmanager
    def _build_context(self):
        if self.settings.compiler == "Visual Studio":
            with vcvars(self.settings):
                env = {
                    "CC": "{} cl -nologo".format(unix_path(self.deps_user_info["automake"].compile)),
                    "CXX": "{} cl -nologo".format(unix_path(self.deps_user_info["automake"].compile)),
                    "LD": "link -nologo",
                    "AR": "{} lib".format(unix_path(self.deps_user_info["automake"].ar_lib)),
                    "DLLTOOL": ":",
                    "OBJDUMP": ":",
                    "RANLIB": ":",
                    "STRIP": ":",
                }
                with environment_append(self, env):
                    yield
        else:
            yield

    def _extract_makefile_variable(self, makefile, variable):
        makefile_contents = load(self, makefile)
        match = re.search(
            '{}[ \t]*=[ \t]*((?:(?:[a-zA-Z0-9 \t.=/_-])|(?:\\\\"))*(?:\\\\\n(?:(?:[a-zA-Z0-9 \t.=/_-])|(?:\\"))*)*)\n'.format(
                variable
            ),
            makefile_contents,
        )
        if not match:
            raise ConanException("Cannot extract variable {} from {}".format(variable, makefile_contents))
        lines = [line.strip(" \t\\") for line in match.group(1).split()]
        return [item for line in lines for item in shlex.split(line) if item]

    def _extract_autotools_variables(self):
        makefile = os.path.join(self.source_folder, "libusb", "Makefile.am")
        sources = self._extract_makefile_variable(makefile, "libusb_la_SOURCES")
        headers = self._extract_makefile_variable(makefile, "include_HEADERS")
        return sources, headers

    def _patch_sources(self):
        apply_conandata_patches(self)
        shutil.copy(
            self._user_info_build["gnu-config"].CONFIG_SUB, os.path.join(self.source_folder, "config.sub")
        )
        shutil.copy(
            self._user_info_build["gnu-config"].CONFIG_GUESS, os.path.join(self.source_folder, "config.guess")
        )
        if self.settings.os == "Windows":
            api = "__declspec(dllexport)" if self.options.shared else ""
            replace_in_file(
                self,
                os.path.join(self.source_folder, "configure.ac"),
                "\nAC_DEFINE([API_EXPORTED]",
                "\nAC_DEFINE([API_EXPORTED], [{}], [API])\n#".format(api),
            )
            # libtool disallows building shared libraries that link to static libraries
            # This will override this and add the dependency
            replace_in_file(
                self,
                os.path.join(self.source_folder, "ltmain.sh"),
                "droppeddeps=yes",
                'droppeddeps=no && func_append newdeplibs " $a_deplib"',
            )

    @property
    def _user_info_build(self):
        return getattr(self, "user_info_build", None) or self.deps_user_info

    def build(self):
        self._patch_sources()
        with self._build_context():
            autotools = self._configure_autotools()
        if self.settings.os == "Windows":
            cmakelists_in = load(self, "CMakeLists.txt.in")
            sources, headers = self._extract_autotools_variables()
            save(
                self,
                os.path.join(self.source_folder, "libusb", "CMakeLists.txt"),
                cmakelists_in.format(libusb_sources=" ".join(sources), libusb_headers=" ".join(headers)),
            )
            replace_in_file(self, "config.h", "\n#define API_EXPORTED", "\n#define API_EXPORTED //")
            cmake = CMake(self)
            cmake.configure()
            cmake.build()
        else:
            with self._build_context():
                autotools.make()

    def package(self):
        copy(self, "LICENSE", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        if self.settings.os == "Windows":
            cmake = CMake(self)
            cmake.install()
        else:
            with self._build_context():
                autotools = self._configure_autotools()
                autotools.install()

            os.unlink(os.path.join(self.package_folder, "bin", "libusb-config"))
            os.unlink(os.path.join(self.package_folder, "lib", "libusb.la"))
            rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))

    def package_info(self):
        self.cpp_info.names["pkg_config"] = "libusb"
        self.cpp_info.libs = ["usb"]
        if not self.options.shared:
            self.cpp_info.defines = ["LIBUSB_COMPAT_STATIC"]
