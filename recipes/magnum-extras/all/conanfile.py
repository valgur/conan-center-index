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
from conan.tools.cmake import (
    CMake,
    CMakeDeps,
    CMakeToolchain,
    cmake_layout,
)
import functools
import os

required_conan_version = ">=1.43.0"


class MagnumExtrasConan(ConanFile):
    name = "magnum-extras"
    description = "Extras for the Magnum C++11/C++14 graphics engine"
    license = "MIT"
    topics = ("magnum", "graphics", "rendering", "3d", "2d", "opengl")
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://magnum.graphics"

    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "player": [True, False],
        "ui": [True, False],
        "ui_gallery": [True, False],
        "application": ["android", "emscripten", "glfw", "glx", "sdl2", "xegl"],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "player": True,
        "ui": True,
        "ui_gallery": True,
        "application": "sdl2",
    }

    def export_sources(self):
        export_conandata_patches(self)

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

        if self.settings.os == "Android":
            self.options.application = "android"
        if self.settings.os == "Emscripten":
            self.options.application = "emscripten"
            # FIXME: Requires 'magnum:basis_importer=True'
            self.options.player = False
            # FIXME: Fails to compile
            self.options.ui_gallery = False

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")

    def requirements(self):
        self.requires("magnum/{}".format(self.version))
        self.requires("corrade/{}".format(self.version))
        if self.settings.os in ["iOS", "Emscripten", "Android"] and self.options.ui_gallery:
            self.requires("magnum-plugins/{}".format(self.version))

    def validate(self):
        opt_name = "{}_application".format(self.options.application)
        if not getattr(self.options["magnum"], opt_name):
            raise ConanInvalidConfiguration("Magnum needs option '{opt}=True'".format(opt=opt_name))
        if self.settings.os == "Emscripten" and self.options["magnum"].target_gl == "gles2":
            raise ConanInvalidConfiguration("OpenGL ES 3 required, use option 'magnum:target_gl=gles3'")

    def build_requirements(self):
        self.build_requires("corrade/{}".format(self.version))

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["BUILD_STATIC"] = not self.options.shared
        tc.variables["BUILD_STATIC_PIC"] = self.options.get_safe("fPIC", False)
        tc.variables["BUILD_TESTS"] = False
        tc.variables["BUILD_GL_TESTS"] = False
        tc.variables["WITH_PLAYER"] = self.options.player
        tc.variables["WITH_UI"] = self.options.ui
        tc.variables["WITH_UI_GALLERY"] = self.options.ui_gallery
        tc.variables["MAGNUM_INCLUDE_INSTALL_DIR"] = os.path.join("include", "Magnum")
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

        cmakelists = [
            os.path.join("src", "Magnum", "Ui", "CMakeLists.txt"),
            os.path.join("src", "player", "CMakeLists.txt"),
        ]
        app_name = "{}Application".format(
            "XEgl" if self.options.application == "xegl" else str(self.options.application).capitalize()
        )
        for cmakelist in cmakelists:
            replace_in_file(
                self,
                os.path.join(self.source_folder, cmakelist),
                "Magnum::Application",
                "Magnum::{}".format(app_name),
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
        self.cpp_info.set_property("cmake_file_name", "MagnumExtras")
        self.cpp_info.names["cmake_find_package"] = "MagnumExtras"
        self.cpp_info.names["cmake_find_package_multi"] = "MagnumExtras"

        lib_suffix = "-d" if self.settings.build_type == "Debug" else ""
        if self.options.ui:
            self.cpp_info.components["ui"].set_property("cmake_target_name", "MagnumExtras::Ui")
            self.cpp_info.components["ui"].names["cmake_find_package"] = "Ui"
            self.cpp_info.components["ui"].names["cmake_find_package_multi"] = "Ui"
            self.cpp_info.components["ui"].libs = ["MagnumUi{}".format(lib_suffix)]
            self.cpp_info.components["ui"].requires = [
                "corrade::interconnect",
                "magnum::magnum_main",
                "magnum::gl",
                "magnum::text",
            ]

        if self.options.player or self.options.ui_gallery:
            bin_path = os.path.join(self.package_folder, "bin")
            self.output.info("Appending PATH environment variable: %s" % bin_path)
            self.env_info.path.append(bin_path)
