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
import contextlib
import os

required_conan_version = ">=1.33.0"


class PExportsConan(ConanFile):
    name = "pexports"
    description = "pexports is a program to extract exported symbols from a PE image (executable)."
    homepage = "https://sourceforge.net/projects/mingw/files/MinGW/Extension/pexports/"
    license = "GPL-2.0-or-later"
    topics = ("windows", "dll", "PE", "symbols", "import", "library")
    url = "https://github.com/conan-io/conan-center-index"
    settings = "os", "arch", "compiler", "build_type"

    _autotools = None

    @property
    def _settings_build(self):
        return getattr(self, "settings_build", self.settings)

    def export_sources(self):
        export_conandata_patches(self)

    def configure(self):
        self.settings.rm_safe("compiler.cppstd")
        self.settings.rm_safe("compiler.libcxx")

    def build_requirements(self):
        self.build_requires("automake/1.16.3")
        if self._settings_build.os == "Windows" and not get_env(self, "CONAN_BASH_PATH"):
            self.build_requires("msys2/cci.latest")

    def package_id(self):
        del self.info.settings.compiler

    def source(self):
        filename = "pexports.tar.xz"
        get(self, **self.conan_data["sources"][self.version], filename=filename, strip_root=True)

    @property
    def _user_info_build(self):
        return getattr(self, "user_info_build", self.deps_user_info)

    @contextlib.contextmanager
    def _build_context(self):
        if self.settings.compiler == "Visual Studio":
            with vcvars(self):
                env = {
                    "CC": "{} cl -nologo".format(unix_path(self._user_info_build["automake"].compile)),
                    "LD": "{} link -nologo".format(unix_path(self._user_info_build["automake"].compile)),
                }
                with environment_append(self, env):
                    yield
        else:
            yield

    def _configure_autotools(self):
        if self._autotools:
            return self._autotools
        self._autotools = AutoToolsBuildEnvironment(self, win_bash=tools.os_info.is_windows)
        host = build = None
        if self.settings.compiler == "Visual Studio":
            self._autotools.defines.append("YY_NO_UNISTD_H")
            host = build = False
        self._autotools.configure(configure_dir=self.source_folder, host=host, build=build)
        return self._autotools

    def build(self):
        apply_conandata_patches(self)
        with chdir(self, self.source_folder):
            self.run("{} -fiv".format(get_env(self, "AUTORECONF")), win_bash=tools.os_info.is_windows)
        with self._build_context():
            autotools = self._configure_autotools()
            autotools.make()

    def package(self):
        copy(self, "COPYING", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        with self._build_context():
            autotools = self._configure_autotools()
            autotools.install()

    def package_info(self):
        self.cpp_info.libdirs = []

        bin_path = os.path.join(self.package_folder, "bin")
        self.output.info("Appending PATH environment variable: {}".format(bin_path))
        self.env_info.PATH.append(bin_path)
