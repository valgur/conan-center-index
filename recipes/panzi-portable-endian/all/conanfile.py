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


class PanziPortableEndian(ConanFile):
    name = "panzi-portable-endian"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://gist.github.com/panzi/6856583"
    description = (
        "This provides the endian conversion functions form endian.h on Windows, Linux, *BSD, and Mac OS X"
    )
    topics = "endian"
    license = "Unlicense"

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def _extract_license(self):
        header = load(self, os.path.join(self.source_folder, "portable_endian.h"))
        license_contents = header[0 : (header.find("#ifndef", 1))]
        save(self, "LICENSE", license_contents)

    def package(self):
        self._extract_license()
        copy(self, "LICENSE", dst=os.path.join(self.package_folder, "licenses"))
        copy(
            self,
            pattern="*.h",
            dst=os.path.join(self.package_folder, "include"),
            src=self.source_folder,
            keep_path=False,
        )

    def package_id(self):
        self.info.header_only()
