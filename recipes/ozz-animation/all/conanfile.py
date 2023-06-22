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

class OzzAnimationConan(ConanFile):
    name = "ozz-animation"
    description = "Open source c++ skeletal animation library and toolset."
    license = "MIT"
    topics = ("ozz", "animation", "skeletal")
    homepage = "https://github.com/guillaumeblanc/ozz-animation"
    url = "https://github.com/conan-io/conan-center-index"
    exports_sources = ["CMakeLists.txt"]
    generators = "cmake"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "fPIC": [True, False],
    }
    default_options = {
        "fPIC": True,
    }
    short_paths = True

    _source_subfolder = "source_subfolder"
    _build_subfolder = "build_subfolder"

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def source(self):
        tools.get(**self.conan_data["sources"][self.version])
        extracted_dir = self.name + "-" + self.version
        os.rename(extracted_dir, self._source_subfolder)

    def generate(self):
        cmake = CMake(self)
        cmake.definitions["ozz_build_fbx"] = False
        cmake.definitions["ozz_build_data"] = False
        cmake.definitions["ozz_build_samples"] = False
        cmake.definitions["ozz_build_howtos"] = False
        cmake.definitions["ozz_build_tests"] = False
        cmake.definitions["ozz_build_cpp11"] = True
        cmake.configure(build_folder=self._build_subfolder)
        return cmake

    def build(self):
        for before, after in [
            ('string(REGEX REPLACE "/MT" "/MD" ${flag} "${${flag}}")', ""),
            ('string(REGEX REPLACE "/MD" "/MT" ${flag} "${${flag}}")', ""),
        ]:
            tools.replace_in_file(
                os.path.join(self._source_subfolder, "build-utils", "cmake", "compiler_settings.cmake"),
                before,
                after,
            )

        tools.replace_in_file(
            os.path.join(self._source_subfolder, "src", "animation", "offline", "tools", "CMakeLists.txt"),
            "if(NOT EMSCRIPTEN)",
            "if(NOT CMAKE_CROSSCOMPILING)",
        )

        cmake = self._configure_cmake()
        cmake.build()

    def package(self):
        cmake = self._configure_cmake()
        cmake.install()

        os.remove(os.path.join(self.package_folder, "CHANGES.md"))
        os.remove(os.path.join(self.package_folder, "LICENSE.md"))
        os.remove(os.path.join(self.package_folder, "README.md"))
        self.copy(pattern="LICENSE.md", dst="licenses", src=self._source_subfolder)

    def package_info(self):
        self.cpp_info.libs = tools.collect_libs(self)
