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

required_conan_version = ">=1.47.0"


class MoldConan(ConanFile):
    name = "mold"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/rui314/mold/"
    license = "AGPL-3.0"
    description = "mold is a faster drop-in replacement for existing Unix linkers. It is several times faster than the LLVM lld linker"
    topics = ("ld", "linkage", "compilation")

    settings = "os", "arch", "compiler", "build_type"

    generators = "make"

    def validate(self):
        if self.settings.build_type == "Debug":
            raise ConanInvalidConfiguration(
                "Mold is a build tool, specify mold:build_type=Release in your build profile, see https://github.com/conan-io/conan-center-index/pull/11536#issuecomment-1195607330"
            )
        if (
            self.settings.compiler in ["gcc", "clang", "intel-cc"]
            and self.settings.compiler.libcxx != "libstdc++11"
        ):
            raise ConanInvalidConfiguration(
                "Mold can only be built with libstdc++11; specify mold:compiler.libcxx=libstdc++11 in your build profile"
            )
        if self.settings.os == "Windows":
            raise ConanInvalidConfiguration(f"{self.name} can not be built on {self.settings.os}.")
        if self.settings.compiler == "gcc" and Version(self.settings.compiler.version) < "10":
            raise ConanInvalidConfiguration("GCC version 10 or higher required")
        if (self.settings.compiler == "clang" or self.settings.compiler == "apple-clang") and Version(
            self.settings.compiler.version
        ) < "12":
            raise ConanInvalidConfiguration("Clang version 12 or higher required")
        if self.settings.compiler == "apple-clang" and "armv8" == self.settings.arch:
            raise ConanInvalidConfiguration(f"{self.name} is still not supported by Mac M1.")

    def _get_include_path(self, dependency):
        include_path = self.deps_cpp_info[dependency].rootpath
        include_path = os.path.join(include_path, "include")
        return include_path

    def _patch_sources(self):
        if self.settings.compiler == "apple-clang" or (
            self.settings.compiler == "gcc" and Version(self.settings.compiler.version) < "11"
        ):
            replace_in_file(self, "source_subfolder/Makefile", "-std=c++20", "-std=c++2a")

        replace_in_file(
            self,
            "source_subfolder/Makefile",
            "-Ithird-party/xxhash ",
            "-I{} -I{} -I{} -I{} -I{}".format(
                self._get_include_path("zlib"),
                self._get_include_path("openssl"),
                self._get_include_path("xxhash"),
                self._get_include_path("mimalloc"),
                self._get_include_path("onetbb"),
            ),
        )

        replace_in_file(
            self,
            "source_subfolder/Makefile",
            "MOLD_LDFLAGS += -ltbb",
            "MOLD_LDFLAGS += -L{} -ltbb".format(self.deps_cpp_info["onetbb"].lib_paths[0]),
        )

        replace_in_file(
            self,
            "source_subfolder/Makefile",
            "MOLD_LDFLAGS += -lmimalloc",
            "MOLD_LDFLAGS += -L{} -lmimalloc".format(self.deps_cpp_info["mimalloc"].lib_paths[0]),
        )

    def requirements(self):
        self.requires("zlib/1.2.12")
        self.requires("openssl/1.1.1q")
        self.requires("xxhash/0.8.1")
        self.requires("onetbb/2021.3.0")
        self.requires("mimalloc/2.0.6")

    def source(self):
        get(
            self,
            **self.conan_data["sources"][self.version],
            strip_root=True,
        )

    def build(self):
        self._patch_sources()
        with chdir(self, self.source_folder):
            autotools = AutoToolsBuildEnvironment(self)
            autotools.make(target="mold", args=["SYSTEM_TBB=1", "SYSTEM_MIMALLOC=1"])

    def package(self):
        copy(self, "LICENSE", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        copy(self, "mold", src="bin", dst=os.path.join(self.package_folder, "bin"), keep_path=False)
        copy(
            self,
            "mold",
            src=self.source_folder,
            dst=os.path.join(self.package_folder, "bin"),
            keep_path=False,
        )

    def package_id(self):
        del self.info.settings.compiler

    def package_info(self):
        bindir = os.path.join(self.package_folder, "bin")
        mold_location = os.path.join(bindir, "bindir")

        self.output.info("Appending PATH environment variable: {}".format(bindir))
        self.env_info.PATH.append(bindir)
        self.env_info.LD = mold_location
        self.buildenv_info.prepend_path("MOLD_ROOT", bindir)
        self.cpp_info.includedirs = []

        if self.settings.os == "Linux":
            self.cpp_info.system_libs.extend(["m", "pthread", "dl"])
