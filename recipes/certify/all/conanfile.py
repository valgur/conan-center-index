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

required_conan_version = ">=1.43.0"


class CertifyConan(ConanFile):
    name = "certify"
    description = "Platform-specific TLS keystore abstraction for use with Boost.ASIO and OpenSSL"
    topics = ("boost", "asio", "tls", "ssl", "https")
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/djarek/certify"
    license = "BSL-1.0"
    settings = "os", "arch", "compiler", "build_type"
    no_copy_source = True

    @property
    def _compilers_minimum_version(self):
        return {
            "gcc": "9",
            "Visual Studio": "15.7",
            "clang": "7",
            "apple-clang": "11",
        }

    @property
    def _min_cppstd(self):
        return "17"

    def requirements(self):
        self.requires("boost/1.79.0")
        self.requires("openssl/1.1.1q")

    def validate(self):
        if self.settings.compiler.get_safe("cppstd"):
            check_min_cppstd(self, self._min_cppstd)

        def lazy_lt_semver(v1, v2):
            lv1 = [int(v) for v in v1.split(".")]
            lv2 = [int(v) for v in v2.split(".")]
            min_length = min(len(lv1), len(lv2))
            return lv1[:min_length] < lv2[:min_length]

        minimum_version = self._compilers_minimum_version.get(str(self.settings.compiler), False)
        if not minimum_version:
            self.output.warn(
                "{} requires C++17. Your compiler is unknown. Assuming it supports C++17.".format(self.name)
            )
        elif lazy_lt_semver(str(self.settings.compiler.version), minimum_version):
            raise ConanInvalidConfiguration(
                "{} requires C++17, which your compiler does not support.".format(self.name)
            )

    def package_id(self):
        self.info.header_only()

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def package(self):
        copy(
            self,
            pattern="LICENSE_1_0.txt",
            dst=os.path.join(self.package_folder, "licenses"),
            src=self.source_folder,
        )
        copy(
            self,
            pattern="*",
            dst=os.path.join(self.package_folder, "include"),
            src=os.path.join(self.source_folder, "include"),
        )

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "certify")
        self.cpp_info.set_property("cmake_target_name", "certify::core")
        self.cpp_info.components["_certify"].requires = ["boost::boost", "openssl::openssl"]

        self.cpp_info.components["_certify"].names["cmake_find_package"] = "core"
        self.cpp_info.components["_certify"].names["cmake_find_package_multi"] = "core"
        self.cpp_info.names["cmake_find_package"] = "certify"
        self.cpp_info.names["cmake_find_package_multi"] = "certify"
