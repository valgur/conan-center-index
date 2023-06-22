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


class LibRHashConan(ConanFile):
    name = "librhash"
    description = "Great utility for computing hash sums"
    topics = ("rhash", "hash", "checksum")
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "http://rhash.sourceforge.net/"
    license = "MIT"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "with_openssl": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "with_openssl": True,
    }

    exports_sources = "patches/*"
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
        self.settings.rm_safe("compiler.cppstd")
        self.settings.rm_safe("compiler.libcxx")

    def requirements(self):
        if self.options.with_openssl:
            self.requires("openssl/1.1.1q")

    def build_requirements(self):
        if self._settings_build.os == "Windows" and not get_env(self, "CONAN_BASH_PATH"):
            self.build_requires("msys2/cci.latest")

    def validate(self):
        if self.settings.compiler == "Visual Studio":
            raise ConanInvalidConfiguration("Visual Studio is not supported")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def _configure_autotools(self):
        if self._autotools:
            return self._autotools
        self._autotools = AutoToolsBuildEnvironment(self, win_bash=tools.os_info.is_windows)
        if self.settings.compiler in ("apple-clang",):
            if self.settings.arch in ("armv7",):
                self._autotools.link_flags.append("-arch armv7")
            elif self.settings.arch in ("armv8",):
                self._autotools.link_flags.append("-arch arm64")
        vars = self._autotools.vars
        conf_args = [
            # librhash's configure script does not understand `--enable-opt1=yes`
            "--enable-openssl" if self.options.with_openssl else "--disable-openssl",
            "--disable-gettext",
            # librhash's configure script is custom and does not understand "--bindir=${prefix}/bin" arguments
            "--prefix={}".format(unix_path(self.package_folder)),
            "--bindir={}".format(unix_path(self, os.path.join(self.package_folder, "bin"))),
            "--libdir={}".format(unix_path(self, os.path.join(self.package_folder, "lib"))),
            # the configure script does not use CPPFLAGS, so add it to CFLAGS/CXXFLAGS
            "--extra-cflags={}".format("{} {}".format(vars["CFLAGS"], vars["CPPFLAGS"])),
            "--extra-ldflags={}".format(vars["LDFLAGS"]),
        ]
        if self.options.shared:
            conf_args.extend(["--enable-lib-shared", "--disable-lib-static"])
        else:
            conf_args.extend(["--disable-lib-shared", "--enable-lib-static"])

        with environment_append(
            self,
            {
                "BUILD_TARGET": get_gnu_triplet(
                    self, str(self.settings.os), str(self.settings.arch), str(self.settings.compiler)
                )
            },
        ):
            self._autotools.configure(args=conf_args, use_default_install_dirs=False, build=False, host=False)
        return self._autotools

    def build(self):
        apply_conandata_patches(self)
        with chdir(self.source_folder):
            autotools = self._configure_autotools()
            autotools.make()

    def package(self):
        copy(self, "COPYING", src=self.source_folder, dst="licenses")
        with chdir(self.source_folder):
            autotools = self._configure_autotools()
            autotools.install()
            autotools.make(target="install-lib-headers")
            with chdir(self, "librhash"):
                if self.options.shared:
                    autotools.make(target="install-so-link")
        rmdir(self, os.path.join(self.package_folder, "bin"))
        rmdir(self, os.path.join(self.package_folder, "etc"))
        rmdir(self, os.path.join(self.package_folder, "share"))

    def package_info(self):
        self.cpp_info.names["cmake_find_package"] = "LibRHash"
        self.cpp_info.names["cmake_find_package_multi"] = "LibRHash"
        self.cpp_info.names["pkg_config"] = "librhash"
        self.cpp_info.libs = ["rhash"]
