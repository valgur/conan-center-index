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


class PackageConan(ConanFile):
    name = "objectbox-generator"
    description = "ObjectBox Generator based on FlatBuffers schema files (fbs) for C and C++"
    license = "GPL-3.0"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/objectbox/objectbox-generator"
    topics = ("database", "code-generator", "objectbox")
    settings = "os", "arch", "compiler", "build_type"

    def validate(self):
        if self.settings.os not in ["Linux", "Windows", "Macos"] or self.settings.arch != "x86_64":
            raise ConanInvalidConfiguration("{} doesn't support current environment".format(self.name))

    def package_id(self):
        del self.info.settings.compiler
        del self.info.settings.build_type

    def source(self):
        tools.get(
            **self.conan_data["sources"][self.version][str(self.settings.os)], destination=self.source_folder
        )
        tools.download(**self.conan_data["sources"][self.version]["License"], filename="LICENSE.txt")

    def package(self):
        if self.settings.os != "Windows":
            bin_path = os.path.join(self.source_folder, "objectbox-generator")
            os.chmod(bin_path, os.stat(bin_path).st_mode | 0o111)
        self.copy("objectbox-generator*", src=self.source_folder, dst="bin", keep_path=False)
        self.copy("LICENSE.txt", dst="licenses", src=self.source_folder)

    def package_info(self):
        binpath = os.path.join(self.package_folder, "bin")
        self.output.info("Appending PATH env var: {}".format(binpath))
        self.env_info.PATH.append(binpath)

        self.cpp_info.includedirs = []
        self.cpp_info.frameworkdirs = []
        self.cpp_info.libdirs = []
        self.cpp_info.resdirs = []
