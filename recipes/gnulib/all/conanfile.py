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
import shutil

required_conan_version = ">=1.33.0"


class GnuLibConanFile(ConanFile):
    name = "gnulib"
    description = (
        "Gnulib is a central location for common GNU code, intended to be shared among GNU packages."
    )
    homepage = "https://www.gnu.org/software/gnulib/"
    url = "https://github.com/conan-io/conan-center-index"
    topics = ("library", "gnu")
    license = ("GPL-3.0-or-later", "LGPL-3.0-or-later", "Unlicense")

    no_copy_source = True

    _source_subfolder = "source_subfolder"

    def package_id(self):
        self.info.header_only()

    def source(self):
        tools.get(
            **self.conan_data["sources"][self.version],
            destination=self._source_subfolder,
            strip_root=True,
            filename="gnulib.tar.gz"
        )

    def package(self):
        self.copy("COPYING", src=self._source_subfolder, dst="licenses")

        # The following line did not work, so do it the long way...
        # shutil.copy(os.path.join(self.source_folder, self._source_subfolder), os.path.join(self.package_folder, "bin"))

        gnulib_dir = os.path.join(self.source_folder, self._source_subfolder)
        for root, _, files in os.walk(gnulib_dir):
            relpath = os.path.relpath(root, gnulib_dir)
            dstdir = os.path.join(self.package_folder, "bin", relpath)
            try:
                os.makedirs(dstdir)
            except FileExistsError:
                pass
            for file in files:
                src = os.path.join(root, file)
                dst = os.path.join(dstdir, file)
                shutil.copy(src, dst)

    def package_info(self):
        self.cpp_info.libdirs = []

        binpath = os.path.join(self.package_folder, "bin")
        self.output.info("Appending PATH environment var: {}".format(binpath))
        self.env_info.PATH.append(binpath)
