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
import functools
import os

required_conan_version = ">=1.43.0"


class MagnumIntegrationConan(ConanFile):
    name = "magnum-integration"
    description = "Integration libraries for the Magnum C++11/C++14 graphics engine"
    license = "MIT"
    topics = ("magnum", "graphics", "rendering", "3d", "2d", "opengl")
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://magnum.graphics"

    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "with_bullet": [True, False],
        "with_dart": [True, False],
        "with_eigen": [True, False],
        "with_glm": [True, False],
        "with_imgui": [True, False],
        "with_ovr": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "with_bullet": True,
        "with_dart": False,
        "with_eigen": True,
        "with_glm": True,
        "with_imgui": True,
        "with_ovr": False,
    }

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")

    def requirements(self):
        self.requires("magnum/{}".format(self.version))
        if self.options.with_bullet:
            self.requires("bullet3/3.22a")
        if self.options.with_eigen:
            self.requires("eigen/3.4.0")
        if self.options.with_glm:
            self.requires("glm/0.9.9.8")
        if self.options.with_imgui:
            self.requires("imgui/1.87")

    def validate(self):
        if self.options.with_dart:
            # FIXME: Add 'dart' requirement
            raise ConanInvalidConfiguration("DART library is not available in ConanCenter (yet)")
        if self.options.with_ovr:
            # FIXME: Add 'ovr' requirement
            raise ConanInvalidConfiguration("OVR library is not available in ConanCenter (yet)")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["BUILD_STATIC"] = not self.options.shared
        tc.variables["BUILD_STATIC_PIC"] = self.options.get_safe("fPIC", True)
        tc.variables["BUILD_TESTS"] = False
        tc.variables["BUILD_GL_TESTS"] = False
        tc.variables["WITH_BULLET"] = self.options.with_bullet
        tc.variables["WITH_DART"] = self.options.with_dart
        tc.variables["WITH_EIGEN"] = self.options.with_eigen
        tc.variables["WITH_GLM"] = self.options.with_glm
        tc.variables["WITH_IMGUI"] = self.options.with_imgui
        tc.variables["WITH_OVR"] = self.options.with_ovr
        tc.variables["MAGNUM_INCLUDE_INSTALL_DIR"] = "include/Magnum"
        tc.variables["MAGNUM_EXTERNAL_INCLUDE_INSTALL_DIR"] = "include/MagnumExternal"
        tc.generate()

        tc = CMakeDeps(self)
        tc.generate()

    def _patch_sources(self):
        apply_conandata_patches(self)

        replace_in_file(
            self,
            os.path.join(self.source_folder, "CMakeLists.txt"),
            'set(CMAKE_MODULE_PATH "${PROJECT_SOURCE_DIR}/modules/" ${CMAKE_MODULE_PATH})',
            "",
        )
        # Casing
        replace_in_file(
            self,
            os.path.join(self.source_folder, "src", "Magnum", "GlmIntegration", "CMakeLists.txt"),
            "find_package(GLM REQUIRED)",
            "find_package(glm REQUIRED)",
        )
        replace_in_file(
            self,
            os.path.join(self.source_folder, "src", "Magnum", "GlmIntegration", "CMakeLists.txt"),
            "GLM::GLM",
            "glm::glm",
        )
        replace_in_file(
            self,
            os.path.join(self.source_folder, "src", "Magnum", "ImGuiIntegration", "CMakeLists.txt"),
            "find_package(ImGui REQUIRED Sources)",
            "find_package(imgui REQUIRED Sources)",
        )
        replace_in_file(
            self,
            os.path.join(self.source_folder, "src", "Magnum", "ImGuiIntegration", "CMakeLists.txt"),
            "ImGui::ImGui",
            "imgui::imgui",
        )
        replace_in_file(
            self,
            os.path.join(self.source_folder, "src", "Magnum", "ImGuiIntegration", "CMakeLists.txt"),
            "ImGui::Sources",
            "",
        )

    def build(self):
        self._patch_sources()
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "share"))
        copy(self, "COPYING", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "MagnumIntegration")
        self.cpp_info.names["cmake_find_package"] = "MagnumIntegration"
        self.cpp_info.names["cmake_find_package_multi"] = "MagnumIntegration"

        lib_suffix = "-d" if self.settings.build_type == "Debug" else ""

        if self.options.with_bullet:
            self.cpp_info.components["bullet"].set_property("cmake_target_name", "MagnumIntegration::Bullet")
            self.cpp_info.components["bullet"].names["cmake_find_package"] = "Bullet"
            self.cpp_info.components["bullet"].names["cmake_find_package_multi"] = "Bullet"
            self.cpp_info.components["bullet"].libs = ["MagnumBulletIntegration{}".format(lib_suffix)]
            self.cpp_info.components["bullet"].requires = [
                "magnum::magnum_main",
                "magnum::gl",
                "magnum::shaders",
                "bullet3::bullet3",
            ]

        if self.options.with_dart:
            raise ConanException("Recipe doesn't define this component 'dart'. Please contribute it")

        if self.options.with_eigen:
            self.cpp_info.components["eigen"].set_property("cmake_target_name", "MagnumIntegration::Eigen")
            self.cpp_info.components["eigen"].names["cmake_find_package"] = "Eigen"
            self.cpp_info.components["eigen"].names["cmake_find_package_multi"] = "Eigen"
            self.cpp_info.components["eigen"].requires = ["magnum::magnum_main", "eigen::eigen"]

        if self.options.with_glm:
            self.cpp_info.components["glm"].set_property("cmake_target_name", "MagnumIntegration::Glm")
            self.cpp_info.components["glm"].names["cmake_find_package"] = "Glm"
            self.cpp_info.components["glm"].names["cmake_find_package_multi"] = "Glm"
            self.cpp_info.components["glm"].libs = ["MagnumGlmIntegration{}".format(lib_suffix)]
            self.cpp_info.components["glm"].requires = ["magnum::magnum_main", "glm::glm"]

        if self.options.with_imgui:
            self.cpp_info.components["imgui"].set_property("cmake_target_name", "MagnumIntegration::ImGui")
            self.cpp_info.components["imgui"].names["cmake_find_package"] = "ImGui"
            self.cpp_info.components["imgui"].names["cmake_find_package_multi"] = "ImGui"
            self.cpp_info.components["imgui"].libs = ["MagnumImGuiIntegration{}".format(lib_suffix)]
            self.cpp_info.components["imgui"].requires = [
                "magnum::magnum_main",
                "magnum::gl",
                "magnum::shaders",
                "imgui::imgui",
            ]

        if self.options.with_ovr:
            raise ConanException("Recipe doesn't define this component 'ovr'. Please contribute it")
