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


class LibEstConan(ConanFile):
    name = "libest"
    license = "BSD-3-Clause"
    description = "EST is used for secure certificate enrollment"
    topics = ("EST", "RFC 7030", "certificate enrollment")
    homepage = "https://github.com/cisco/libest"
    url = "https://github.com/conan-io/conan-center-index"
    settings = "os", "compiler", "build_type", "arch"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
    }

    _autotools = None

    def export_sources(self):
        export_conandata_patches(self)

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.settings.os in ("Windows", "Macos"):
            raise ConanInvalidConfiguration("Platform is currently not supported by this recipe")
        if self.options.shared:
            self.options.rm_safe("fPIC")
        self.settings.rm_safe("compiler.libcxx")
        self.settings.rm_safe("compiler.cppstd")

    def requirements(self):
        self.requires("openssl/1.1.1q")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        extracted_dir = self.name + "-r" + self.version
        os.rename(extracted_dir, self.source_folder)

    def _configure_autotools(self):
        if not self._autotools:
            self._autotools = AutoToolsBuildEnvironment(self)
            # TODO:
            # - Static only build: https://github.com/cisco/libest/blob/70824ddc09bee661329b9416082d88566efefb32/intro.txt#L140
            # - Release build: https://github.com/cisco/libest/blob/70824ddc09bee661329b9416082d88566efefb32/intro.txt#L253
            args = []
            if self.options.shared:
                args.extend(["--enable-shared", "--disable-static"])
            else:
                args.extend(["--disable-shared", "--enable-static"])
            self._autotools.configure(args=args)
        return self._autotools

    def build(self):
        apply_conandata_patches(self)
        with chdir(self.source_folder):
            autotools = self._configure_autotools()
            autotools.make()

    def package(self):
        copy(self, "*LICENSE", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        with chdir(self.source_folder):
            autotools = self._configure_autotools()
            autotools.install()
        os.unlink(os.path.join(self.package_folder, "lib", "libest.la"))

    def package_info(self):
        self.cpp_info.libs = ["est"]
        if self.settings.os == "Linux":
            self.cpp_info.system_libs = ["dl", "pthread"]
