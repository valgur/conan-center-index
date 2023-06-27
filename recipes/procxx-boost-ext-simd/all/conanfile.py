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


class ProCxxBoostExSimdConan(ConanFile):
    name = "procxx-boost-ext-simd"
    description = "Portable SIMD computation library - was proposed as a Boost library"
    homepage = "https://github.com/procxx/boost.simd"
    topics = ("boost", "simd")
    license = "BSL-1.0"
    url = "https://github.com/conan-io/conan-center-index"
    settings = "os", "arch", "compiler", "build_type"
    no_copy_source = True

    @property
    def _min_cppstd(self):
        return "11"

    def requirements(self):
        self.requires("boost/1.76.0")

    def validate(self):
        if self.settings.compiler.get_safe("cppstd"):
            check_min_cppstd(self, self._min_cppstd)

    def package_id(self):
        self.info.header_only()

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        extracted_folder = "boost.simd-" + self.version
        os.rename(extracted_folder, self.source_folder)

    def package(self):
        copy(
            self,
            pattern="*",
            dst=os.path.join(self.package_folder, "include"),
            src=os.path.join(self.source_folder, "include"),
        )
        copy(self, "LICENSE", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder)

    def package_info(self):
        # this technique was inspired by conan-center's "boost-ex-ut" recipe,
        # and has been fixed to use the upstream Capitalized `Boost::`
        # namespace for components
        self.cpp_info.names["cmake_find_package"] = "Boost"
        self.cpp_info.names["cmake_find_package_multi"] = "Boost"

        # The original find_package() name here:
        self.cpp_info.filenames["cmake_find_package"] = "Boost.SIMD"
        self.cpp_info.filenames["cmake_find_package_multi"] = "Boost.SIMD"
        self.cpp_info.components["SIMD"].names["cmake_find_package"] = "SIMD"
        self.cpp_info.components["SIMD"].names["cmake_find_package_multi"] = "SIMD"
        self.cpp_info.components["SIMD"].requires = ["boost::headers"]
