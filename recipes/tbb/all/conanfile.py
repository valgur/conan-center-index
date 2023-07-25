# TODO: verify the Conan v2 migration

import os
from contextlib import nullcontext

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
import textwrap

required_conan_version = ">=1.53.0"


class TBBConan(ConanFile):
    deprecated = "onetbb"

    name = "tbb"
    description = (
        "Intel Threading Building Blocks (Intel TBB) lets you easily write "
        "parallel C++ programs that take full advantage of multicore "
        "performance, that are portable and composable, and that have "
        "future-proof scalability"
    )
    license = "Apache-2.0"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/oneapi-src/oneTBB"
    topics = ("threading", "parallelism", "tbbmalloc")

    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "tbbmalloc": [True, False],
        "tbbproxy": [True, False],
    }
    default_options = {
        "shared": True,
        "fPIC": True,
        "tbbmalloc": False,
        "tbbproxy": False,
    }

    @property
    def _settings_build(self):
        return getattr(self, "settings_build", self.settings)

    @property
    def _is_clanglc(self):
        return self.settings.os == "Windows" and self.settings.compiler == "clang"

    @property
    def _base_compiler(self):
        base = self.settings.get_safe("compiler.base")
        if base:
            return self.settings.compiler.base
        return self.settings.compiler

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")

    def layout(self):
        basic_layout(self, src_folder="src")

    def package_id(self):
        del self.info.options.tbbmalloc
        del self.info.options.tbbproxy

    def validate(self):
        if is_apple_os(self):
            if hasattr(self, "settings_build") and cross_building(self):
                # See logs from https://github.com/conan-io/conan-center-index/pull/8454
                raise ConanInvalidConfiguration(
                    "Cross building on Macos is not yet supported. Contributions are welcome"
                )
            if self.settings.compiler == "apple-clang" and Version(self.settings.compiler.version) < "8.0":
                raise ConanInvalidConfiguration(
                    f"{self.name} {self.version} couldn't be built by apple-clang < 8.0"
                )
        if not self.options.shared:
            self.output.warning("Intel-TBB strongly discourages usage of static linkage")
        if self.options.tbbproxy and (not self.options.shared or not self.options.tbbmalloc):
            raise ConanInvalidConfiguration("tbbproxy needs tbbmaloc and shared options")

    def build_requirements(self):
        if self._settings_build.os == "Windows":
            if "CONAN_MAKE_PROGRAM" not in os.environ and not which(self, "make"):
                self.build_requires("make/4.2.1")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        # TODO: fill in generate()
        pass

    def build(self):
        def add_flag(name, value):
            if name in os.environ:
                os.environ[name] += " " + value
            else:
                os.environ[name] = value

        # Get the version of the current compiler instead of gcc
        linux_include = os.path.join(self.source_folder, "build", "linux.inc")
        replace_in_file(self, linux_include, "shell gcc", "shell $(CC)")
        replace_in_file(self, linux_include, "= gcc", "= $(CC)")

        if self.version != "2019_u9" and self.settings.build_type == "Debug":
            replace_in_file(self, os.path.join(self.source_folder, "Makefile"), "release", "debug")

        if str(self._base_compiler) in ["Visual Studio", "msvc"]:
            save(
                self,
                os.path.join(self.source_folder, "build", "big_iron_msvc.inc"),
                # copy of big_iron.inc adapted for MSVC
                textwrap.dedent(f"""\
                    LIB_LINK_CMD = {"xilib" if self.settings.compiler == "intel" else "lib"}.exe
                    LIB_OUTPUT_KEY = /OUT:
                    LIB_LINK_FLAGS =
                    LIB_LINK_LIBS =
                    DYLIB_KEY =
                    override CXXFLAGS += -D__TBB_DYNAMIC_LOAD_ENABLED=0 -D__TBB_SOURCE_DIRECTLY_INCLUDED=1
                    ITT_NOTIFY =
                    DLL = lib
                    LIBEXT = lib
                    LIBPREF =
                    LIBDL =
                    TBB.DLL = $(LIBPREF)tbb$(DEBUG_SUFFIX).$(LIBEXT)
                    LINK_TBB.LIB = $(TBB.DLL)
                    TBB.DEF =
                    TBB_NO_VERSION.DLL =
                    MALLOC.DLL = $(LIBPREF)tbbmalloc$(DEBUG_SUFFIX).$(LIBEXT)
                    LINK_MALLOC.LIB = $(MALLOC.DLL)
                    MALLOC.DEF =
                    MALLOC_NO_VERSION.DLL =
                    MALLOCPROXY.DLL =
                    MALLOCPROXY.DEF =
                """),
            )
            extra = "" if self.options.shared else "extra_inc=big_iron_msvc.inc"
        else:
            extra = "" if self.options.shared else "extra_inc=big_iron.inc"

        arch = {
            "x86": "ia32",
            "x86_64": "intel64",
            "armv7": "armv7",
            "armv8": "aarch64",
        }[str(self.settings.arch)]
        extra += f" arch={arch}"

        if str(self._base_compiler) in ("gcc", "clang", "apple-clang"):
            if str(self._base_compiler.libcxx) in ("libstdc++", "libstdc++11"):
                extra += " stdlib=libstdc++"
            elif str(self._base_compiler.libcxx) == "libc++":
                extra += " stdlib=libc++"

            if str(self.settings.compiler) == "intel":
                extra += " compiler=icc"
            elif str(self.settings.compiler) in ("clang", "apple-clang"):
                extra += " compiler=clang"
            else:
                extra += " compiler=gcc"

            if self.settings.os == "Linux":
                # runtime is supposed to track the version of the c++ stdlib,
                # the version of glibc, and the version of the linux kernel.
                # However, it isn't actually used anywhere other than for
                # logging and build directory names.
                # TBB computes the value of this variable using gcc, which we
                # don't necessarily want to require when building this recipe.
                # Setting it to a dummy value prevents TBB from calling gcc.
                extra += " runtime=gnu"
        elif str(self._base_compiler) in ["Visual Studio", "msvc"]:
            if is_msvc_static_runtime(self):
                runtime = "vc_mt"
            else:
                if is_msvc(self):
                    runtime = {
                        "8": "vc8",
                        "9": "vc9",
                        "10": "vc10",
                        "11": "vc11",
                        "12": "vc12",
                        "14": "vc14",
                        "15": "vc14.1",
                        "16": "vc14.2",
                    }.get(str(self._base_compiler.version), "vc14.2")
                else:
                    runtime = {
                        "190": "vc14",
                        "191": "vc14.1",
                        "192": "vc14.2",
                    }.get(str(self._base_compiler.version), "vc14.2")
            extra += f" runtime={runtime}"

            if self.settings.compiler == "intel":
                extra += " compiler=icl"
            else:
                extra += " compiler=cl"

        with chdir(self, self.source_folder):
            # intentionally not using AutoToolsBuildEnvironment for now - it's broken for clang-cl
            if self._is_clanglc:
                add_flag("CFLAGS", "-mrtm")
                add_flag("CXXFLAGS", "-mrtm")

            targets = ["tbb", "tbbmalloc", "tbbproxy"]
            context = nullcontext()
            if self.settings.compiler == "intel":
                context = intel_compilervars(self)
            elif is_msvc(self):
                # intentionally not using vcvars for clang-cl yet
                context = vcvars(self)
            with context:
                self.run(f"{make} {extra} {' '.join(targets)}")

    def package(self):
        copy(self, "LICENSE", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder)
        copy(
            self,
            pattern="*.h",
            dst=os.path.join(self.package_folder, "include"),
            src=os.path.join(self.source_folder, "include"),
        )
        copy(
            self,
            pattern="*",
            dst=os.path.join(self.package_folder, "include/tbb/compat"),
            src=os.path.join(self.source_folder, "include/tbb/compat"),
        )
        build_folder = os.path.join(self.source_folder, "build")
        build_type = "debug" if self.settings.build_type == "Debug" else "release"
        copy(
            self,
            pattern=f"*{build_type}*.lib",
            dst=os.path.join(self.package_folder, "lib"),
            src=build_folder,
            keep_path=False,
        )
        copy(
            self,
            pattern=f"*{build_type}*.a",
            dst=os.path.join(self.package_folder, "lib"),
            src=build_folder,
            keep_path=False,
        )
        copy(
            self,
            pattern=f"*{build_type}*.dll",
            dst=os.path.join(self.package_folder, "bin"),
            src=build_folder,
            keep_path=False,
        )
        copy(
            self,
            pattern=f"*{build_type}*.dylib",
            dst=os.path.join(self.package_folder, "lib"),
            src=build_folder,
            keep_path=False,
        )
        # Copy also .dlls to lib folder so consumers can link against them directly when using MinGW
        if self.settings.os == "Windows" and self.settings.compiler == "gcc":
            copy(
                self,
                f"*{build_type}*.dll",
                dst=os.path.join(self.package_folder, "lib"),
                src=build_folder,
                keep_path=False,
            )

        if self.settings.os == "Linux":
            extension = "so"
            if self.options.shared:
                copy(self, f"*{build_type}*.{extension}.*", "lib", build_folder, keep_path=False)
                outputlibdir = os.path.join(self.package_folder, "lib")
                os.chdir(outputlibdir)
                for fpath in os.listdir(outputlibdir):
                    self.run(
                        'ln -s "{}" "{}"'.format(
                            fpath, fpath[0 : fpath.rfind("." + extension) + len(extension) + 1]
                        )
                    )

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "TBB")

        suffix = "_debug" if self.settings.build_type == "Debug" else ""

        # tbb
        self.cpp_info.components["libtbb"].set_property("cmake_target_name", "TBB::tbb")
        self.cpp_info.components["libtbb"].libs = [f"tbb{suffix}"]
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.components["libtbb"].system_libs = ["dl", "rt", "pthread"]

        # tbbmalloc
        if self.options.tbbmalloc:
            self.cpp_info.components["tbbmalloc"].set_property("cmake_target_name", "TBB::tbbmalloc")
            self.cpp_info.components["tbbmalloc"].libs = [f"tbbmalloc{suffix}"]
            if self.settings.os in ["Linux", "FreeBSD"]:
                self.cpp_info.components["tbbmalloc"].system_libs = ["dl", "pthread"]

            # tbbmalloc_proxy
            if self.options.tbbproxy:
                self.cpp_info.components["tbbmalloc_proxy"].set_property(
                    "cmake_target_name", "TBB::tbbmalloc_proxy"
                )
                self.cpp_info.components["tbbmalloc_proxy"].libs = [f"tbbmalloc_proxy{suffix}"]
                self.cpp_info.components["tbbmalloc_proxy"].requires = ["tbbmalloc"]

        # TODO: to remove in conan v2 once cmake_find_package* generators removed
        self.cpp_info.names["cmake_find_package"] = "TBB"
        self.cpp_info.names["cmake_find_package_multi"] = "TBB"
        self.cpp_info.components["libtbb"].names["cmake_find_package"] = "tbb"
        self.cpp_info.components["libtbb"].names["cmake_find_package_multi"] = "tbb"
