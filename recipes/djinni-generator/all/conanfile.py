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


class Djinni(ConanFile):
    name = "djinni-generator"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://djinni.xlcpp.dev"
    description = "Djinni is a tool for generating cross-language type declarations and interface bindings."
    topics = ("java", "Objective-C", "ios", "Android")
    license = "Apache-2.0"
    settings = "os", "arch"

    def source(self):
        filename = os.path.basename(self.conan_data["sources"][self.version]["url"])
        download(self, filename=filename, **self.conan_data["sources"][self.version])
        download(
            self,
            filename="LICENSE",
            url="https://raw.githubusercontent.com/cross-language-cpp/djinni-generator/main/LICENSE",
        )

    def build(self):
        pass  # avoid warning for missing build steps

    def package(self):
        if detected_os(self) == "Windows":
            os.rename("djinni", "djinni.bat")
            copy(self, "djinni.bat", dst=os.path.join(self.package_folder, "bin"), keep_path=False)
        else:
            copy(self, "djinni", dst=os.path.join(self.package_folder, "bin"), keep_path=False)
            executable = os.path.join(self.package_folder, "bin", "djinni")
            os.chmod(executable, os.stat(executable).st_mode | 0o111)
        copy(self, "LICENSE", dst=os.path.join(self.package_folder, "licenses"), keep_path=False)

    def package_info(self):
        self.cpp_info.includedirs = []
        self.env_info.PATH.append(os.path.join(self.package_folder, "bin"))
