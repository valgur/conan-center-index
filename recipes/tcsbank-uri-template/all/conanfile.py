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

required_conan_version = ">=1.33.0"


class TCSBankUriTemplateConan(ConanFile):
    name = "tcsbank-uri-template"
    description = "URI Templates expansion and reverse-matching for C++"
    topics = ("uri-template", "url-template", "rfc-6570")
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/TinkoffCreditSystems/uri-template"
    license = "Apache-2.0"

    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
    }

    def export_sources(self):
        export_conandata_patches(self)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["URITEMPLATE_BUILD_TESTING"] = False
        tc.generate()

        tc = CMakeDeps(self)
        tc.generate()

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")

    def validate(self):
        compiler_name = str(self.settings.compiler)
        compiler_version = Version(self.settings.compiler.version)

        # Exclude compiler.cppstd < 17
        min_req_cppstd = "17"
        if self.settings.compiler.cppstd:
            check_min_cppstd(self, min_req_cppstd)
        else:
            self.output.warn(
                "%s recipe lacks information about the %s compiler"
                " standard version support." % (self.name, compiler_name)
            )

        # Exclude not supported compilers
        compilers_required = {
            "Visual Studio": "16",
            "gcc": "7.3",
            "clang": "6.0",
            "apple-clang": "10.0",
        }
        if compiler_name not in compilers_required or compiler_version < compilers_required[compiler_name]:
            raise ConanInvalidConfiguration(
                "%s requires a compiler that supports at least C++%s. %s %s is not supported."
                % (self.name, min_req_cppstd, compiler_name, compiler_version)
            )

        # Check stdlib ABI compatibility
        if compiler_name == "gcc" and self.settings.compiler.libcxx != "libstdc++11":
            raise ConanInvalidConfiguration(
                'Using %s with GCC requires "compiler.libcxx=libstdc++11"' % self.name
            )
        elif compiler_name == "clang" and self.settings.compiler.libcxx not in ["libstdc++11", "libc++"]:
            raise ConanInvalidConfiguration(
                'Using %s with Clang requires either "compiler.libcxx=libstdc++11"'
                ' or "compiler.libcxx=libc++"' % self.name
            )

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))

    def package_info(self):
        self.cpp_info.names["pkg_config"] = "uri-template"
        self.cpp_info.names["cmake_find_package"] = "uri-template"
        self.cpp_info.names["cmake_find_package_multi"] = "uri-template"
        self.cpp_info.libs = collect_libs(self)
