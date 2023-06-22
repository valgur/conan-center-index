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
from conan.tools.cmake import (
    CMake,
    CMakeDeps,
    CMakeToolchain,
    cmake_layout,
)


class ExtracmakemodulesConan(ConanFile):
    name = "extra-cmake-modules"
    license = ("MIT", "BSD-2-Clause", "BSD-3-Clause")
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://api.kde.org/ecm/"
    topics = ("cmake", "toolchain", "build-settings")
    description = "KDE's CMake modules"
    generators = "cmake"
    no_copy_source = False

    def source(self):
        tools.get(**self.conan_data["sources"][self.version])
        os.rename("extra-cmake-modules-{}".format(self.version), self._source_subfolder)

    def generate(self):

        # KB-H016: do not install Find*.cmake
        tools.replace_path_in_file(
            os.path.join(self._source_subfolder, "CMakeLists.txt"),
            "install(FILES ${installFindModuleFiles} DESTINATION ${FIND_MODULES_INSTALL_DIR})",
            "",
        )

        tc = CMakeToolchain(self)
        tc.variables["BUILD_HTML_DOCS"] = False
        tc.variables["BUILD_QTHELP_DOCS"] = False
        tc.variables["BUILD_MAN_DOCS"] = False
        tc.variables["SHARE_INSTALL_DIR"] = os.path.join(self.package_folder, "res")
        self._cmake.configure(source_folder=os.path.join(self.source_folder, self._source_subfolder))
        return self._cmake

    def build(self):
        cmake = self._configure_cmake()
        cmake.build()

    def package(self):
        cmake = self._configure_cmake()
        cmake.install()
        self.copy(
            "testhelper.h",
            src=os.path.join(self.source_folder, self._source_subfolder, "tests/ECMAddTests"),
            dst="res/tests",
        )
        self.copy(
            "*", src=os.path.join(self.source_folder, self._source_subfolder, "LICENSES"), dst="licenses"
        )

    def package_info(self):
        self.cpp_info.resdirs = ["res"]
        self.cpp_info.builddirs = [
            "res/ECM/cmake",
            "res/ECM/kde-modules",
            "res/ECM/modules",
            "res/ECM/test-modules",
            "res/ECM/toolchain",
        ]

    def package_id(self):
        self.info.header_only()
