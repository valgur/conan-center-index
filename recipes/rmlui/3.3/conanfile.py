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


class RmluiConan(ConanFile):
    name = "rmlui"
    description = "RmlUi - The HTML/CSS User Interface Library Evolved"
    homepage = "https://github.com/mikke89/RmlUi"
    url = "https://github.com/conan-io/conan-center-index"
    license = "MIT"
    topics = ("css", "gui", "html", "lua", "rmlui")
    settings = "os", "compiler", "build_type", "arch"
    options = {
        "enable_rtti_and_exceptions": [True, False],
        "font_interface": ["freetype", None],
        "fPIC": [True, False],
        "shared": [True, False],
        "with_lua_bindings": [True, False],
        "with_thirdparty_containers": [True, False],
    }
    default_options = {
        "enable_rtti_and_exceptions": True,
        "font_interface": "freetype",
        "fPIC": True,
        "shared": False,
        "with_lua_bindings": False,
        "with_thirdparty_containers": True,
    }

    @property
    def _minimum_compilers_version(self):
        # Reference: https://en.cppreference.com/w/cpp/compiler_support/14
        return {
            "apple-clang": "5.1",
            "clang": "3.4",
            "gcc": "5",
            "intel": "17",
            "sun-cc": "5.15",
            "Visual Studio": "15",
        }

    @property
    def _minimum_cpp_standard(self):
        return 14

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")

    def validate(self):
        if self.settings.compiler.get_safe("cppstd"):
            check_min_cppstd(self, self._minimum_cpp_standard)
        min_version = self._minimum_compilers_version.get(str(self.settings.compiler))
        if not min_version:
            self.output.warn(
                f"{self.name} recipe lacks information about the {self.settings.compiler} compiler support."
            )
        else:
            if Version(self.settings.compiler.version) < min_version:
                raise ConanInvalidConfiguration(
                    f"{self.name} requires C++{self._minimum_cpp_standard} support. "
                    f"The current compiler {self.settings.compiler} {self.settings.compiler.version} does not support it."
                )

    def requirements(self):
        if self.options.font_interface == "freetype":
            self.requires("freetype/2.10.1")

        if self.options.with_lua_bindings:
            self.requires("lua/5.3.5")

    def build_requirements(self):
        self.tool_requires("cmake/3.23.2")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def _patch_sources(self):
        # The *.cmake files that conan generates using cmake_find_package for CMake's find_package to consume use
        # different variable naming than described in CMake's documentation, thus the need for most of the replacements.
        # References:
        #  * https://cmake.org/cmake/help/latest/module/FindFreetype.html
        #  * https://cmake.org/cmake/help/latest/module/FindLua.html
        replace_mapping = {
            "FREETYPE_FOUND": "Freetype_FOUND",
            "FREETYPE_INCLUDE_DIRS": "Freetype_INCLUDE_DIRS",
            "FREETYPE_LINK_DIRS": "Freetype_LINK_DIRS",
            "FREETYPE_LIBRARY": "Freetype_LIBRARIES",
            "LUA_FOUND": "lua_FOUND",
            "LUA_INCLUDE_DIR": "lua_INCLUDE_DIR",
            "LUA_LIBRARIES": "lua_LIBRARIES",
            # disables the built-in generation of package configuration files
            "if(PkgHelpers_AVAILABLE)": "if(FALSE)",
        }

        cmakelists_path = os.path.join(self.source_folder, "CMakeLists.txt")

        for key, value in replace_mapping.items():
            replace_in_file(self, cmakelists_path, key, value)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["BUILD_LUA_BINDINGS"] = self.options.with_lua_bindings
        tc.variables["BUILD_SAMPLES"] = False
        tc.variables["DISABLE_RTTI_AND_EXCEPTIONS"] = not self.options.enable_rtti_and_exceptions
        tc.variables["ENABLE_PRECOMPILED_HEADERS"] = True
        tc.variables["ENABLE_TRACY_PROFILING"] = False
        tc.variables["NO_FONT_INTERFACE_DEFAULT"] = self.options.font_interface is None
        tc.variables["NO_THIRDPARTY_CONTAINERS"] = not self.options.with_thirdparty_containers
        tc.generate()
        tc = CMakeDeps(self)
        tc.generate()

    def build(self):
        self._patch_sources()
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        cmake = CMake(self)
        cmake.install()
        copy(self, "LICENSE", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder)

    def package_info(self):
        if not self.options.enable_rtti_and_exceptions:
            self.cpp_info.defines.append("RMLUI_USE_CUSTOM_RTTI")

        if not self.options.shared:
            self.cpp_info.defines.append("RMLUI_STATIC_LIB")

        if not self.options.with_thirdparty_containers:
            self.cpp_info.defines.append("RMLUI_NO_THIRDPARTY_CONTAINERS")

        self.cpp_info.libs.append("RmlDebugger")

        if self.options.with_lua_bindings:
            self.cpp_info.libs.append("RmlControlsLua")
        self.cpp_info.libs.append("RmlControls")

        if self.options.with_lua_bindings:
            self.cpp_info.libs.append("RmlCoreLua")
        self.cpp_info.libs.append("RmlCore")
