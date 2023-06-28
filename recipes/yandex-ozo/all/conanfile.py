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

required_conan_version = ">=1.52.0"


class YandexOzoConan(ConanFile):
    name = "yandex-ozo"
    description = "C++ header-only library for asynchronous access to PostgreSQL databases using ASIO"
    license = "PostgreSQL"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/yandex/ozo"
    topics = ("ozo", "yandex", "postgres", "postgresql", "cpp17", "database", "db", "asio", "header-only")

    package_type = "header-library"
    settings = "os", "arch", "compiler", "build_type"
    no_copy_source = True

    @property
    def _compilers_minimum_version(self):
        return {
            "gcc": "7",
            "Visual Studio": "15",
            "clang": "5",
            "apple-clang": "10",
        }

    def layout(self):
        basic_layout(self, src_folder="src")

    def requirements(self):
        self.requires("boost/1.76.0")
        self.requires("resource_pool/cci.20210322")
        self.requires("libpq/13.2")

    def package_id(self):
        self.info.clear()

    def _validate_compiler_settings(self):
        compiler = self.settings.compiler
        if compiler.get_safe("cppstd"):
            check_min_cppstd(self, "17")
        minimum_version = self._compilers_minimum_version.get(str(self.settings.compiler), False)

        if not minimum_version:
            self.output.warning("ozo requires C++17. Your compiler is unknown. Assuming it supports C++17.")
        elif Version(self.settings.compiler.version) < minimum_version:
            raise ConanInvalidConfiguration("ozo requires a compiler that supports at least C++17")

    def validate(self):
        if self.settings.os == "Windows":
            raise ConanInvalidConfiguration("ozo does currently not support windows")

        self._validate_compiler_settings()

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def package(self):
        copy(
            self,
            pattern="*",
            dst=os.path.join("include", "ozo"),
            src=os.path.join(self.source_folder, "include", "ozo"),
        )
        copy(self, "LICENSE", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder)

    def package_info(self):
        self.cpp_info.bindirs = []
        self.cpp_info.libdirs = []

        main_comp = self.cpp_info.components["_ozo"]
        main_comp.requires = [
            "boost::boost",
            "boost::system",
            "boost::thread",
            "boost::coroutine",
            "resource_pool::resource_pool",
            "libpq::pq",
        ]
        main_comp.defines = ["BOOST_HANA_CONFIG_ENABLE_STRING_UDL", "BOOST_ASIO_USE_TS_EXECUTOR_AS_DEFAULT"]
        main_comp.names["cmake_find_package"] = "ozo"
        main_comp.names["cmake_find_package_multi"] = "ozo"

        compiler = self.settings.compiler
        version = Version(compiler.version)
        if compiler == "clang" or compiler == "apple-clang" or (compiler == "gcc" and version >= 9):
            main_comp.cxxflags = [
                "-Wno-gnu-string-literal-operator-template",
                "-Wno-gnu-zero-variadic-macro-arguments",
            ]

        self.cpp_info.filenames["cmake_find_package"] = "ozo"
        self.cpp_info.filenames["cmake_find_package_multi"] = "ozo"
        self.cpp_info.names["cmake_find_package"] = "yandex"
        self.cpp_info.names["cmake_find_package_multi"] = "yandex"
