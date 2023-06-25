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
import os

required_conan_version = ">=1.33.0"


class ScdocInstallerConan(ConanFile):
    name = "scdoc"
    description = "scdoc is a simple man page generator for POSIX systems written in C99."
    topics = ("manpage", "documentation", "posix")
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://git.sr.ht/~sircmpwn/scdoc"
    license = "MIT"
    settings = "os", "arch", "compiler", "build_type"
    _autotools = None

    def build_requirements(self):
        self.build_requires("make/4.3")

    def configure(self):
        self.settings.rm_safe("compiler.libcxx")
        self.settings.rm_safe("compiler.cppstd")

    def package_id(self):
        del self.info.settings.compiler

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    @staticmethod
    def _chmod_plus_x(filename):
        if os.name == "posix":
            os.chmod(filename, os.stat(filename).st_mode | 0o111)

    def _configure_autotools(self):
        if self._autotools:
            return self._autotools
        self._autotools = AutoToolsBuildEnvironment(self)
        return self._autotools

    def build(self):
        autotools = self._configure_autotools()
        with chdir(self, self.source_folder):
            autotools.make()

    def package(self):
        autotools = self._configure_autotools()
        with chdir(self, self.source_folder):
            autotools.install(args=[f"PREFIX={self.package_folder}"])
        copy(
            self, pattern="COPYING", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder
        )
        rmdir(self, os.path.join(self.package_folder, "share"))

    def package_info(self):
        self.cpp_info.libdirs = []

        scdoc_root = os.path.join(self.package_folder, "bin")
        self.output.info("Appending PATH environment variable: {}".format(scdoc_root))
        self.env_info.PATH.append(scdoc_root)
        self._chmod_plus_x(os.path.join(scdoc_root, "scdoc"))
        pkgconfig_variables = {
            "exec_prefix": "${prefix}/bin",
            "scdoc": "${exec_prefix}/scdoc",
        }
        self.cpp_info.set_property(
            "pkg_config_custom_content",
            "\n".join("%s=%s" % (key, value) for key, value in pkgconfig_variables.items()),
        )

    def validate(self):
        if self.settings.os in ["Macos", "Windows"]:
            raise ConanInvalidConfiguration(f"Builds aren't supported on {self.settings.os}")
