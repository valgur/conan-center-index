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

required_conan_version = ">=1.47.0"


class ConanXqilla(ConanFile):
    name = "xsd"
    description = (
        "XSD is a W3C XML Schema to C++ translator. It generates vocabulary-specific, statically-typed C++"
        " mappings (also called bindings) from XML Schema definitions. XSD supports two C++ mappings:"
        " in-memory C++/Tree and event-driven C++/Parser."
    )
    license = ("GPL-2.0", "FLOSSE")
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://codesynthesis.com/projects/xsd/"
    topics = ("xml", "c++")

    package_type = "application"
    settings = "os", "arch", "compiler", "build_type"

    def export_sources(self):
        export_conandata_patches(self)

    @property
    def _make_install_cmd(self):
        make_install_cmd = f"{self._make_cmd} install_prefix={self.package_folder} install"
        return make_install_cmd

    def layout(self):
        basic_layout(self, src_folder="src")

    def requirements(self):
        self.requires("xerces-c/3.2.3")

    def package_id(self):
        del self.info.settings.compiler

    @property
    def _doc_folder(self):
        return os.path.join(self.source_folder, "xsd", "doc")

    @property
    def _make_cmd(self):
        return self._gnumake_cmd

    @property
    def _make_program(self):
        return get_env(self, "CONAN_MAKE_PROGRAM", which(self, "make"))

    @property
    def _gnumake_cmd(self):
        make_ldflags = "LDFLAGS='{libs} -pthread'".format(
            libs=" ".join(
                [
                    "-L{}".format(os.path.join(self.deps_cpp_info["xerces-c"].rootpath, it))
                    for it in self.deps_cpp_info["xerces-c"].libdirs
                ]
            )
        )
        flags = []
        flags.append(
            " ".join(
                [
                    "-I{}".format(os.path.join(self.deps_cpp_info["xerces-c"].rootpath, it))
                    for it in self.deps_cpp_info["xerces-c"].includedirs
                ]
            )
        )
        if self.settings.compiler == "gcc":
            flags.append("-std=c++11")
        make_ccpflags = "CPPFLAGS='{}'".format(" ".join(flags))
        make_cmd = f"{make_ldflags} {make_ccpflags} {self._make_program} -j{cpu_count(self)}"
        return make_cmd

    def validate(self):
        if self.settings.os != "Linux":
            raise ConanInvalidConfiguration("The xsd recipe currently only supports Linux.")
        if self.settings.compiler.cppstd:
            check_min_cppstd(self, 11)

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def build(self):
        apply_conandata_patches(self)

        with chdir(self, self.source_folder):
            self.run(self._make_cmd)

    def package(self):
        copy(
            self,
            "LICENSE",
            dst=os.path.join(self.package_folder, "licenses"),
            src=os.path.join(self.source_folder, "xsd"),
        )
        copy(
            self,
            "GPLv2",
            dst=os.path.join(self.package_folder, "licenses"),
            src=os.path.join(self.source_folder, "xsd"),
        )
        copy(
            self,
            "FLOSSE",
            dst=os.path.join(self.package_folder, "licenses"),
            src=os.path.join(self.source_folder, "xsd"),
        )

        with chdir(self, self.source_folder):
            self.run(self._make_install_cmd)

        rmdir(self, os.path.join(self.package_folder, "share"))

    def package_info(self):
        self.cpp_info.frameworkdirs = []
        self.cpp_info.libdirs = []
        self.cpp_info.resdirs = []
        self.cpp_info.includedirs = []
        bin_path = os.path.join(self.package_folder, "bin")
        self.output.info(f"Appending PATH environment variable: {bin_path}")
        self.env_info.path.append(bin_path)
