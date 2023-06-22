# TODO: verify the Conan v2 migration

import os
import shutil

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

class DepotToolsConan(ConanFile):
    name = "depot_tools"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://chromium.googlesource.com/chromium/tools/depot_tools"
    description = "Tools for working with Chromium development."
    topics = "chromium"
    license = "BSD-3-Clause"
    short_paths = True
    no_copy_source = True
    settings = "os", "arch", "build_type", "compiler"
    exports_sources = ["patches/**"]

    @property
    def _source_subfolder(self):
        return os.path.join(self.source_folder, "source_subfolder")

    def _dereference_symlinks(self):
        """
        Windows 10 started to introduce support for symbolic links. Unfortunately
        it caused a lot of trouble during packaging. Namely, opening symlinks causes
        `OSError: Invalid argument` rather than actually following the symlinks.
        Therefore, this workaround simply copies the destination file over the symlink
        """
        if self.settings.os != "Windows":
            return

        for root, dirs, files in os.walk(self._source_subfolder):
            symlinks = [os.path.join(root, f) for f in files if os.path.islink(os.path.join(root, f))]
            for symlink in symlinks:
                dest = os.readlink(symlink)
                os.remove(symlink)
                shutil.copy(os.path.join(root, dest), symlink, follow_symlinks=False)
                self.output.info("Replaced symlink '%s' with its destination file '%s'" % (symlink, dest))

    def source(self):
        tools.get(**self.conan_data["sources"][self.version], destination=self._source_subfolder)
        self._dereference_symlinks()

        for patch in self.conan_data.get("patches", {}).get(self.version, []):
            tools.patch(**patch)

    def package(self):
        self.copy(pattern="LICENSE", dst="licenses", src=self._source_subfolder)
        self.copy(pattern="*", dst="bin", src=self._source_subfolder)
        self._fix_permissions()

    def _fix_permissions(self):
        def chmod_plus_x(name):
            os.chmod(name, os.stat(name).st_mode | 0o111)

        if self.settings.os != "Windows":
            for root, _, files in os.walk(self.package_folder):
                for file_it in files:
                    filename = os.path.join(root, file_it)
                    with open(filename, "rb") as f:
                        sig = f.read(4)
                        if type(sig) is str:
                            sig = [ord(s) for s in sig]
                        if len(sig) >= 2 and sig[0] == 0x23 and sig[1] == 0x21:
                            self.output.info("chmod on script file %s" % file_it)
                            chmod_plus_x(filename)
                        elif sig == [0x7F, 0x45, 0x4C, 0x46]:
                            self.output.info("chmod on ELF file %s" % file_it)
                            chmod_plus_x(filename)
                        elif (
                            sig == [0xCA, 0xFE, 0xBA, 0xBE]
                            or sig == [0xBE, 0xBA, 0xFE, 0xCA]
                            or sig == [0xFE, 0xED, 0xFA, 0xCF]
                            or sig == [0xCF, 0xFA, 0xED, 0xFE]
                            or sig == [0xFE, 0xED, 0xFA, 0xCE]
                            or sig == [0xCE, 0xFA, 0xED, 0xFE]
                        ):
                            self.output.info("chmod on Mach-O file %s" % file_it)
                            chmod_plus_x(filename)

    def package_id(self):
        del self.info.settings.arch
        del self.info.settings.build_type
        del self.info.settings.compiler

    def package_info(self):
        bin_path = os.path.join(self.package_folder, "bin")
        self.output.info("Appending PATH env var with : {}".format(bin_path))
        self.env_info.PATH.append(bin_path)

        self.env_info.DEPOT_TOOLS_UPDATE = "0"
