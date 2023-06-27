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
import os

required_conan_version = ">=1.47.0"


class Re2CConan(ConanFile):
    name = "re2c"
    description = "re2c is a free and open-source lexer generator for C, C++ and Go."
    license = "Unlicense"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "http://re2c.org/"
    topics = ("lexer", "language", "tokenizer", "flex")

    package_type = "application"
    settings = "os", "arch", "compiler", "build_type"

    @property
    def _settings_build(self):
        return getattr(self, "settings_build", self.settings)

    def export_sources(self):
        export_conandata_patches(self)

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        self.settings.rm_safe("compiler.cppstd")
        self.settings.rm_safe("compiler.libcxx")

    def layout(self):
        basic_layout(self, src_folder="src")

    def package_id(self):
        del self.info.settings.compiler

    def build_requirements(self):
        if self._settings_build.os == "Windows" and not get_env(self, "CONAN_BASH_PATH"):
            self.build_requires("msys2/cci.latest")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    @contextmanager
    def _build_context(self):
        if is_msvc(self):
            with vcvars(self):
                env = {
                    "CC": "{} -nologo".format(unix_path(self, os.path.join(self.build_folder, "msvc_cl.sh"))),
                    "CXX": "{} -nologo".format(
                        unix_path(self, os.path.join(self.build_folder, "msvc_cl.sh"))
                    ),
                    "LD": "{} -nologo".format(unix_path(self, os.path.join(self.build_folder, "msvc_cl.sh"))),
                    "CXXLD": "{} -nologo".format(
                        unix_path(self, os.path.join(self.build_folder, "msvc_cl.sh"))
                    ),
                    "AR": "lib",
                }
                with environment_append(self, env):
                    yield
        else:
            yield

    def _configure_autotools(self):
        tc = AutotoolsToolchain(self)
        if is_msvc(self):
            tc.cxxflags.append("-FS")
            tc.cxxflags.append("-EHsc")
        tc.generate()

    def build(self):
        apply_conandata_patches(self)
        with self._build_context():
            autotools = Autotools(self)
            autotools.configure()
            autotools.make(args=["V=1"])

    def package(self):
        copy(
            self,
            "LICENSE",
            src=self.source_folder,
            dst=os.path.join(self.package_folder, "licenses"),
            keep_path=False,
        )
        copy(
            self,
            "NO_WARRANTY",
            src=self.source_folder,
            dst=os.path.join(self.package_folder, "licenses"),
            keep_path=False,
        )
        with self._build_context():
            autotools = Autotools(self)
            autotools.install()

        rmdir(self, os.path.join(self.package_folder, "share"))

    def package_info(self):
        self.cpp_info.frameworkdirs = []
        self.cpp_info.libdirs = []
        self.cpp_info.resdirs = []
        self.cpp_info.includedirs = []
        bin_path = os.path.join(self.package_folder, "bin")
        self.output.info(f"Appending PATH environment variable: {bin_path}")
        self.env_info.PATH.append(bin_path)
