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

required_conan_version = ">=1.43.0"


class SerdeppConan(ConanFile):
    name = "serdepp"
    description = "c++ serialize and deserialize adaptor library like rust serde.rs"
    license = "MIT"
    topics = ("yaml", "toml", "serialization", "json", "reflection")
    homepage = "https://github.com/injae/serdepp"
    url = "https://github.com/conan-io/conan-center-index"
    settings = "arch", "build_type", "compiler", "os"
    options = {
        # keeping the option in case upstream support dynamic linking
        "with_nlohmann_json": [True, False],
        "with_rapidjson": [True, False],
        "with_fmt": [True, False],
        "with_toml11": [True, False],
        "with_yamlcpp": [True, False],
    }
    default_options = {
        "with_nlohmann_json": True,
        "with_rapidjson": True,
        "with_fmt": True,
        "with_toml11": True,
        "with_yamlcpp": True,
    }
    no_copy_source = True

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def package_id(self):
        self.info.header_only()

    @property
    def _compilers_minimum_version(self):
        return {
            "gcc": "7",
            "Visual Studio": "17",
            "clang": "5",
            "apple-clang": "10",
        }

    def validate(self):
        compiler = self.settings.compiler
        if compiler.get_safe("cppstd"):
            check_min_cppstd(self, "17")
        minimum_version = self._compilers_minimum_version.get(str(self.settings.compiler), False)

        if not minimum_version:
            self.output.warn(
                f"{self.name} requires C++17. Your compiler is unknown. Assuming it supports C++17."
            )
        elif Version(self.settings.compiler.version) < minimum_version:
            raise ConanInvalidConfiguration(f"{self.name} requires a compiler that supports at least C++17")

    def package(self):
        s = lambda x: os.path.join(self.source_folder, x)
        copy(self, "LICENSE", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder)
        include = os.path.join("include", "serdepp")
        copy(self, "*.hpp", dst=include, src=s(include))
        attribute = os.path.join(include, "attribute")
        copy(self, "*.hpp", dst=attribute, src=s(attribute))
        adaptor = os.path.join(include, "adaptor")
        copy(self, "reflection.hpp", dst=adaptor, src=s(adaptor))
        copy(self, "sstream.hpp", dst=adaptor, src=s(adaptor))
        if self.options.with_toml11:
            copy(self, "toml11.hpp", dst=adaptor, src=s(adaptor))
        if self.options.with_yamlcpp:
            copy(self, "yaml-cpp.hpp", dst=adaptor, src=s(adaptor))
        if self.options.with_rapidjson:
            copy(self, "rapidjson.hpp", dst=adaptor, src=s(adaptor))
        if self.options.with_fmt:
            copy(self, "fmt.hpp", dst=adaptor, src=s(adaptor))
        if self.options.with_nlohmann_json:
            copy(self, "nlohmann_json.hpp", dst=adaptor, src=s(adaptor))

    def requirements(self):
        self.requires("nameof/0.10.1")
        self.requires("magic_enum/0.7.3")
        if self.options.with_toml11:
            self.requires("toml11/3.7.0")
        if self.options.with_yamlcpp:
            self.requires("yaml-cpp/0.7.0")
        if self.options.with_rapidjson:
            self.requires("rapidjson/1.1.0")
        if self.options.with_fmt:
            self.requires("fmt/8.1.1")
        if self.options.with_nlohmann_json:
            self.requires("nlohmann_json/3.10.5")
