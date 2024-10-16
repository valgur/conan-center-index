import os
from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMakeToolchain, CMake, cmake_layout, CMakeDeps
from conan.tools.files import copy, get, rmdir, replace_in_file
from conan.errors import ConanInvalidConfiguration
from conan.tools.scm import Version
from conan.tools.env import VirtualBuildEnv

required_conan_version = ">=1.47.0"


class MoldConan(ConanFile):
    name = "mold"
    description = (
        "mold is a faster drop-in replacement for existing Unix linkers. "
        "It is several times faster than the LLVM lld linker."
    )
    license = ("AGPL-3.0", "MIT")
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/rui314/mold/"
    topics = ("ld", "linkage", "compilation", "pre-built")

    package_type = "application"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "with_mimalloc": [True, False],
    }
    default_options = {
        "with_mimalloc": False,
    }

    @property
    def _min_cppstd(self):
        return 20

    @property
    def _compilers_minimum_version(self):
        return {
            "gcc": "11",
            "clang": "12",
            "apple-clang": "14",
            "Visual Studio": "16",
            "msvc": "192",
        }

    def export_sources(self):
        copy(self, "conan_deps.cmake", self.recipe_folder, os.path.join(self.export_sources_folder, "src"))

    def configure(self):
        if Version(self.version) < "2.0.0":
            self.license = "AGPL-3.0"
        else:
            self.license = "MIT"

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires("zlib/[>=1.2.11 <2]")
        self.requires("zstd/[~1.5]")
        self.requires("xxhash/0.8.2")
        if self.options.with_mimalloc:
            self.requires("mimalloc/2.1.7")
        if Version(self.version) < "2.2.0":
            # Newer versions use vendored-in BLAKE3
            self.requires("openssl/[>=1.1 <4]")

    def package_id(self):
        del self.info.settings.compiler

    def validate(self):
        # mold has required C+20 since 1.4.1. However, C++20 features are used for the first time in 2.34.0.
        if Version(self.version) >= "2.34.0":
            # validate the minimum cpp standard supported. For C++ projects only
            if self.settings.compiler.cppstd:
                check_min_cppstd(self, self._min_cppstd)
            minimum_version = self._compilers_minimum_version.get(str(self.settings.compiler), False)
            if minimum_version and Version(self.settings.compiler.version) < minimum_version:
                raise ConanInvalidConfiguration(
                    f"{self.ref} requires C++{self._min_cppstd}, which your compiler does not support."
                )

        # TODO most of these checks should run on validate_build, but the conan-center hooks are broken and fail the PR because they
        # think we're raising on the build() method
        if self.settings.build_type == "Debug":
            raise ConanInvalidConfiguration('Mold is a build tool, specify mold:build_type=Release in your build profile, see https://github.com/conan-io/conan-center-index/pull/11536#issuecomment-1195607330')
        if self.settings.compiler in ["gcc", "clang", "intel-cc"] and self.settings.compiler.libcxx != "libstdc++11":
            raise ConanInvalidConfiguration('Mold can only be built with libstdc++11; specify mold:compiler.libcxx=libstdc++11 in your build profile')
        if self.settings.os == "Windows":
            raise ConanInvalidConfiguration(f'{self.name} can not be built on {self.settings.os}.')
        if self.settings.compiler == "gcc" and Version(self.settings.compiler.version) < "10":
            raise ConanInvalidConfiguration("GCC version 10 or higher required")
        if self.settings.compiler in ('clang', 'apple-clang') and Version(self.settings.compiler.version) < "12":
            raise ConanInvalidConfiguration("Clang version 12 or higher required")
        if self.settings.compiler == "apple-clang" and "armv8" == self.settings.arch :
            raise ConanInvalidConfiguration(f'{self.name} is still not supported by Mac M1.')
        if Version(self.version) == "2.33.0" and self.settings.compiler == "apple-clang" and Version(self.settings.compiler.version) < "14":
            raise ConanInvalidConfiguration(f'{self.ref} doesn\'t support Apple-Clang < 14.')

    def build_requirements(self):
        self.tool_requires("cmake/[>=3.18.0 <4]")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["CMAKE_PROJECT_mold_INCLUDE"] = "conan_deps.cmake"
        tc.variables["MOLD_USE_MIMALLOC"] = self.options.with_mimalloc
        tc.variables["MOLD_USE_SYSTEM_MIMALLOC"] = True
        tc.variables["MOLD_USE_SYSTEM_TBB"] = False # see https://github.com/conan-io/conan-center-index/pull/23575#issuecomment-2059154281
        tc.variables["CMAKE_INSTALL_LIBEXECDIR"] = "libexec"
        tc.generate()

        cd = CMakeDeps(self)
        cd.set_property("zstd", "cmake_target_name", "zstd::zstd")
        cd.generate()

        vbe = VirtualBuildEnv(self)
        vbe.generate()

    def _patch_sources(self):
        # Make sure these have been unvendored correctly.
        for dep in ["mimalloc", "xxhash", "zlib", "zstd"]:
            # TODO: blake3, rust-demangle
            rmdir(self, os.path.join(self.source_folder, "third-party", dep))
        replace_in_file(self, os.path.join(self.source_folder, "lib", "common.h"),
                        '#include "../third-party/xxhash/xxhash.h"',
                        "#include <xxhash.h>")

    def build(self):
        self._patch_sources()
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        cmake = CMake(self)
        cmake.install()
        copy(self, "LICENSE", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))

        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))
        rmdir(self, os.path.join(self.package_folder, "share"))

    def package_info(self):
        self.cpp_info.includedirs = []
        self.cpp_info.libdirs = []
        self.cpp_info.frameworkdirs = []
        self.cpp_info.resdirs = []

        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs = ["m", "pthread", "dl"]

        bindir = os.path.join(self.package_folder, "bin")
        mold_executable = os.path.join(bindir, "mold")
        self.conf_info.define("user.mold:path", mold_executable)
        self.buildenv_info.define_path("MOLD_ROOT", bindir)
        self.buildenv_info.define("LD", mold_executable)

        # For legacy Conan 1.x consumers only:
        self.env_info.PATH.append(bindir)
        self.env_info.MOLD_ROOT = bindir
        self.env_info.LD = mold_executable
