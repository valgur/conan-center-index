# TODO: verify the Conan v2 migration

import glob
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


class RgbcxConan(ConanFile):
    name = "rgbcx"
    description = "High-performance scalar BC1-5 encoders."
    homepage = "https://github.com/richgel999/bc7enc"
    url = "https://github.com/conan-io/conan-center-index"
    topics = ("BC1", "BC5", "BCx", "encoding")
    license = "MIT", "Unlicense"

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        extracted_dir = glob.glob("bc7enc-*/")[0]
        os.rename(extracted_dir, self.source_folder)

    def build(self):
        replace_in_file(
            self,
            os.path.join(self.source_folder, "rgbcx.h"),
            "#include <stdlib.h>",
            "#include <stdlib.h>\n#include <string.h>",
        )

    def package(self):
        copy(self, "rgbcx.h", dst=os.path.join(self.package_folder, "include"), src=self.source_folder)
        copy(self, "rgbcx_table4.h", dst=os.path.join(self.package_folder, "include"), src=self.source_folder)
        copy(self, "LICENSE", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder)

    def package_id(self):
        self.info.header_only()
