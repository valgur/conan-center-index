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
from conan.tools.cmake import (
    CMake,
    CMakeDeps,
    CMakeToolchain,
    cmake_layout,
)


class CgltfConan(ConanFile):
    name = "cgltf"
    description = "Single-file glTF 2.0 loader and writer written in C99."
    license = "MIT"
    topics = ("gltf", "header-only")
    homepage = "https://github.com/jkuhlmann/cgltf"
    url = "https://github.com/conan-io/conan-center-index"

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
        copy(self, "CMakeLists.txt", src=self.recipe_folder, dst=self.export_sources_folder)
        export_conandata_patches(self)

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")
        self.settings.rm_safe("compiler.libcxx")
        self.settings.rm_safe("compiler.cppstd")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        os.rename(self.name + "-" + self.version, self.source_folder)

    def _create_source_files(self):
        cgltf_c = "#define CGLTF_IMPLEMENTATION\n" '#include "cgltf.h"\n'
        cgltf_write_c = "#define CGLTF_WRITE_IMPLEMENTATION\n" '#include "cgltf_write.h"\n'
        save(self, os.path.join(self.build_folder, self.source_folder, "cgltf.c"), cgltf_c)
        save(self, os.path.join(self.build_folder, self.source_folder, "cgltf_write.c"), cgltf_write_c)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.generate()
        tc = CMakeDeps(self)
        tc.generate()

    def build(self):
        self._create_source_files()
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder)
        cmake = CMake(self)
        cmake.install()
        for header_file in ["cgltf.h", "cgltf_write.h"]:
            header_fullpath = os.path.join(self.package_folder, "include", header_file)
            self._remove_implementation(header_fullpath)

    @staticmethod
    def _remove_implementation(header_fullpath):
        header_content = load(self, header_fullpath)
        begin = header_content.find("/*\n *\n * Stop now, if you are only interested in the API.")
        end = header_content.find("/* cgltf is distributed under MIT license:", begin)
        implementation = header_content[begin:end]
        replace_in_file(
            self,
            header_fullpath,
            implementation,
            (
                "/**\n"
                " * Implementation removed by conan during packaging.\n"
                " * Don't forget to link libs provided in this package.\n"
                " */\n\n"
            ),
        )

    def package_info(self):
        self.cpp_info.libs = ["cgltf"]
