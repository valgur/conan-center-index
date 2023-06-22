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
import os.path
import glob


class MattiasgustavssonLibsConan(ConanFile):
    name = "mattiasgustavsson-libs"
    description = "Single-file public domain libraries for C/C++"
    homepage = "https://github.com/mattiasgustavsson/libs"
    url = "https://github.com/conan-io/conan-center-index"
    license = ("Unlicense", "MIT")
    topics = ("utilities", "mattiasgustavsson", "libs")
    no_copy_source = True

    @property
    def _source_subfolder(self):
        return os.path.join(self.source_folder, "source_subfolder")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        extracted_dir = glob.glob("libs-*/")[0]
        os.rename(extracted_dir, self.source_folder)

    def _extract_licenses(self):
        header = load(self, os.path.join(self.source_folder, "thread.h"))
        mit_content = header[header.find("ALTERNATIVE A - ") : header.find("ALTERNATIVE B -")]
        save(self, "LICENSE_MIT", mit_content)
        unlicense_content = header[header.find("ALTERNATIVE B - ") : header.rfind("*/", 1)]
        save(self, "LICENSE_UNLICENSE", unlicense_content)

    def package(self):
        copy(self, pattern="*.h", dst=os.path.join(self.package_folder, "include"), src=self.source_folder)
        self._extract_licenses()
        copy(self, "LICENSE_MIT", dst=os.path.join(self.package_folder, "licenses"))
        copy(self, "LICENSE_UNLICENSE", dst=os.path.join(self.package_folder, "licenses"))

    def package_id(self):
        self.info.header_only()
