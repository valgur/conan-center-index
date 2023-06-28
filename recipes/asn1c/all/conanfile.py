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
from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.files import get, rmdir, chdir
import os

required_conan_version = ">=1.47.0"


class Asn1cConan(ConanFile):
    name = "asn1c"
    description = "The ASN.1 Compiler"
    license = "BSD-2-Clause"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://lionet.info/asn1c"
    topics = ("asn.1", "compiler")

    package_type = "application"
    settings = "os", "arch", "compiler", "build_type"

    @property
    def _datarootdir(self):
        return os.path.join(self.package_folder, "res")

    def configure(self):
        self.settings.rm_safe("compiler.libcxx")
        self.settings.rm_safe("compiler.cppstd")

    def layout(self):
        basic_layout(self, src_folder="src")

    def package_id(self):
        del self.info.settings.compiler

    def validate(self):
        if is_msvc(self):
            raise ConanInvalidConfiguration("Visual Studio is not supported")

    def build_requirements(self):
        self.tool_requires("bison/3.7.6")
        self.tool_requires("flex/2.6.4")
        self.tool_requires("libtool/2.4.7")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def _configure_autotools(self):
        tc = AutotoolsToolchain(self)
        tc.configure_args = [f"--datarootdir={unix_path(self, self._datarootdir)}"]
        tc.generate()

    def build(self):
        with chdir(self, self.source_folder):
            self.run("{} -fiv".format(get_env(self, "AUTORECONF")))
        autotools = Autotools(self)
        autotools.configure()
        autotools.make()

    def package(self):
        copy(self, "LICENSE", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder)
        autotools = Autotools(self)
        autotools.install()
        rmdir(self, os.path.join(self.package_folder, "res", "doc"))
        rmdir(self, os.path.join(self.package_folder, "res", "man"))

    def package_info(self):
        self.cpp_info.frameworkdirs = []
        self.cpp_info.libdirs = []
        self.cpp_info.resdirs = []
        self.cpp_info.includedirs = []

        bin_path = os.path.join(self.package_folder, "bin")
        self.output.info(f"Appending PATH environment variable: {bin_path}")
        self.env_info.PATH.append(bin_path)

        # asn1c cannot use environment variables to specify support files path
        # so `SUPPORT_PATH` should be propagated to command line invocation to `-S` argument
        self.env_info.SUPPORT_PATH = os.path.join(self.package_folder, "res/asn1c")
