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

required_conan_version = ">=1.28.0"


class CppTaskflowConan(ConanFile):
    name = "cpp-taskflow"
    description = "A fast C++ header-only library to help you quickly write parallel programs with complex task dependencies."
    topics = ("taskflow", "tasking", "parallelism")
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/cpp-taskflow/cpp-taskflow"
    license = "MIT"
    no_copy_source = True
    settings = "os", "compiler"
    deprecated = "taskflow"

    def configure(self):
        compiler = str(self.settings.compiler)
        compiler_version = Version(self.settings.compiler.version)
        min_req_cppstd = "17" if Version(self.version) <= "2.2.0" else "14"

        if self.settings.compiler.cppstd:
            check_min_cppstd(self, min_req_cppstd)
        else:
            self.output.warn(
                "%s recipe lacks information about the %s compiler"
                " standard version support" % (self.name, compiler)
            )

        minimal_version = {
            "17": {
                "Visual Studio": "16",
                "gcc": "7.3",
                "clang": "6.0",
                "apple-clang": "10.0",
            },
            "14": {
                "Visual Studio": "15",
                "gcc": "5",
                "clang": "4.0",
                "apple-clang": "8.0",
            },
        }

        if compiler not in minimal_version[min_req_cppstd]:
            self.output.info(
                "%s requires a compiler that supports at least C++%s" % (self.name, min_req_cppstd)
            )
            return

        # Exclude compilers not supported by cpp-taskflow
        if compiler_version < minimal_version[min_req_cppstd][compiler]:
            raise ConanInvalidConfiguration(
                "%s requires a compiler that supports"
                " at least C++%s. %s %s is not"
                " supported."
                % (self.name, min_req_cppstd, compiler, Version(self.settings.compiler.version.value))
            )

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        os.rename("taskflow-" + self.version, self.source_folder)

    def package(self):
        copy(
            self, pattern="LICENSE", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder
        )
        copy(
            self,
            pattern="*",
            dst=os.path.join(self.package_folder, "include/taskflow"),
            src=os.path.join(self.source_folder, "taskflow"),
        )

    def package_id(self):
        self.info.header_only()

    def package_info(self):
        if self.settings.os == "Linux":
            self.cpp_info.system_libs.append("pthread")
        if self.settings.compiler == "Visual Studio":
            self.cpp_info.defines.append("_ENABLE_EXTENDED_ALIGNED_STORAGE")
