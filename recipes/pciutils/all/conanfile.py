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


class PciUtilsConan(ConanFile):
    name = "pciutils"
    license = "BSD-3-Clause"
    description = "The PCI Utilities package contains a library for portable access to PCI bus"
    topics = ("pci", "pci-bus", "hardware", "local-bus")
    homepage = "https://github.com/pciutils/pciutils"
    url = "https://github.com/conan-io/conan-center-index"
    settings = "os", "compiler", "build_type", "arch"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "with_zlib": [True, False],
        "with_udev": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "with_zlib": True,
        "with_udev": False,
    }

    def configure(self):
        if self.settings.os != "Linux":
            raise ConanInvalidConfiguration(
                "Platform {} is currently not supported by this recipe".format(self.settings.os)
            )

        if self.options.shared:
            self.options.rm_safe("fPIC")
        self.settings.rm_safe("compiler.libcxx")
        self.settings.rm_safe("compiler.cppstd")

    def requirements(self):
        if self.options.with_zlib:
            self.requires("zlib/1.2.11")
        if self.options.with_udev:
            # TODO: Enable libudev option when available
            raise ConanInvalidConfiguration("libudev requires conan-io/conan-center-index#2468")
            self.requires("systemd/system")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        extracted_dir = self.name + "-" + self.version
        rename(self, extracted_dir, self.source_folder)

    def _make(self, targets):
        yes_no = lambda v: "yes" if v else "no"
        autotools = AutoToolsBuildEnvironment(self)
        autotools.make(
            args=[
                "SHARED={}".format(yes_no(self.options.shared)),
                "ZLIB={}".format(yes_no(self.options.with_zlib)),
                "HWDB={}".format(yes_no(self.options.with_udev)),
                "PREFIX={}".format(self.package_folder),
                "OPT={}".format("{} {}".format(autotools.vars["CPPFLAGS"], autotools.vars["CFLAGS"])),
                "DNS=no",
            ],
            target=" ".join(targets),
        )

    def build(self):
        with chdir(self.source_folder):
            self._make(["all"])

    def package(self):
        with chdir(self.source_folder):
            self._make(["install", "install-pcilib"])

        copy(self, "COPYING", src=self.source_folder, dst="licenses")
        copy(self, "*.h", src=self.source_folder, dst="include", keep_path=True)

        if self.options.shared:
            rename(
                self,
                src=os.path.join(self.source_folder, "lib", "libpci.so.3.7.0"),
                dst=os.path.join(self.package_folder, "lib", "libpci.so"),
            )

        rmdir(self, os.path.join(self.package_folder, "sbin"))
        rmdir(self, os.path.join(self.package_folder, "share"))
        rmdir(self, os.path.join(self.package_folder, "man"))

    def package_info(self):
        self.cpp_info.names["pkg_config"] = "libpci"
        self.cpp_info.libs = ["pci"]
