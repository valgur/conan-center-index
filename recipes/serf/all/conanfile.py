# Warnings:
#   Unexpected method '_cc'
#   Unexpected method '_lib_path_arg'
#   Unexpected method '_build_context'
#   Unexpected method '_static_ext'
#   Unexpected method '_shared_ext'
#   Unexpected method '_version_major'
#   Missing required method 'generate'

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
from contextlib import contextmanager, nullcontext
import glob
import os
import re

required_conan_version = ">=1.53.0"


class SerfConan(ConanFile):
    name = "serf"
    description = (
        "The serf library is a high performance C-based HTTP client library built upon the Apache Portable"
        " Runtime (APR) library."
    )
    license = "Apache-2.0"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://serf.apache.org/"
    topics = ("apache", "http", "library")

    package_type = "library"
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
        export_conandata_patches(self)

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")
        self.settings.rm_safe("compiler.cppstd")
        self.settings.rm_safe("compiler.libcxx")

    def layout(self):
        pass

    def requirements(self):
        self.requires("apr-util/1.6.1")
        self.requires("zlib/1.2.12")
        self.requires("openssl/3.0.3")

    def build_requirements(self):
        self.build_requires("scons/4.3.0")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        # TODO: fill in generate()
        pass

    def _patch_sources(self):
        apply_conandata_patches(self)
        pc_in = os.path.join(self.source_folder, "build", "serf.pc.in")
        save(self, pc_in, load(self, pc_in))

    @property
    def _cc(self):
        if get_env(self, "CC"):
            return get_env(self, "CC")
        if is_apple_os(self.settings.os):
            return "clang"
        return {
            "Visual Studio": "cl",
        }.get(str(self.settings.compiler), str(self.settings.compiler))

    def _lib_path_arg(self, path):
        argname = "LIBPATH:" if is_msvc(self) else "L"
        return "-{}'{}'".format(argname, path.replace("\\", "/"))

    @contextmanager
    def _build_context(self):
        extra_env = {}
        if is_msvc(self):
            extra_env["OPENSSL_LIBS"] = ";".join(
                "{}.lib".format(lib) for lib in self.dependencies["openssl"].cpp_info.libs
            )
        with environment_append(self, extra_env):
            with vcvars(self.settings) if is_msvc(self) else nullcontext():
                yield

    def build(self):
        self._patch_sources()
        autotools = AutoToolsBuildEnvironment(self)
        args = ["-Y", self.source_folder]
        kwargs = {
            "APR": self.dependencies["apr"].cpp_info.rootpath.replace("\\", "/"),
            "APU": self.dependencies["apr-util"].cpp_info.rootpath.replace("\\", "/"),
            "OPENSSL": self.dependencies["openssl"].cpp_info.rootpath.replace("\\", "/"),
            "PREFIX": self.package_folder.replace("\\", "/"),
            "LIBDIR": os.path.join(self.package_folder, "lib").replace("\\", "/"),
            "ZLIB": self.dependencies["zlib"].cpp_info.rootpath.replace("\\", "/"),
            "DEBUG": self.settings.build_type == "Debug",
            "APR_STATIC": not self.options["apr"].shared,
            "CFLAGS": " ".join(
                self.deps_cpp_info.cflags
                + (["-fPIC"] if self.options.get_safe("fPIC") else [])
                + autotools.flags
            ),
            "LINKFLAGS": (
                " ".join(self.deps_cpp_info.sharedlinkflags)
                + " "
                + " ".join(self._lib_path_arg(l) for l in self.deps_cpp_info.libdirs)
            ),
            "CPPFLAGS": (
                " ".join("-D{}".format(d) for d in autotools.defines)
                + " "
                + " ".join("-I'{}'".format(inc.replace("\\", "/")) for inc in self.deps_cpp_info.includedirs)
            ),
            "CC": self._cc,
            "SOURCE_LAYOUT": "False",
        }

        if is_msvc(self):
            kwargs.update(
                {
                    "TARGET_ARCH": str(self.settings.arch),
                    "MSVC_VERSION": "{:.1f}".format(float(msvs_toolset(self.settings).lstrip("v")) / 10),
                }
            )

        escape_str = lambda x: '"{}"'.format(x)
        with chdir(self, self.source_folder):
            with self._build_context():
                self.run(
                    "scons {} {}".format(
                        " ".join(escape_str(s) for s in args),
                        " ".join("{}={}".format(k, escape_str(v)) for k, v in kwargs.items()),
                    ),
                    run_environment=True,
                )

    @property
    def _static_ext(self):
        return "a"

    @property
    def _shared_ext(self):
        if is_apple_os(self.settings.os):
            return "dylib"
        return {
            "Windows": "dll",
        }.get(str(self.settings.os), "so")

    def package(self):
        copy(self, "LICENSE", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        with chdir(self, self.source_folder):
            with self._build_context():
                self.run('scons install -Y "{}"'.format(self.source_folder), run_environment=True)

        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))
        if self.settings.os == "Windows":
            for file in glob.glob(os.path.join(self.package_folder, "lib", "*.exp")):
                os.unlink(file)
            for file in glob.glob(os.path.join(self.package_folder, "lib", "*.pdb")):
                os.unlink(file)
            if self.options.shared:
                for file in glob.glob(
                    os.path.join(self.package_folder, "lib", "serf-{}.*".format(self._version_major))
                ):
                    os.unlink(file)
                mkdir(self, os.path.join(self.package_folder, "bin"))
                os.rename(
                    os.path.join(self.package_folder, "lib", "libserf-{}.dll".format(self._version_major)),
                    os.path.join(self.package_folder, "bin", "libserf-{}.dll".format(self._version_major)),
                )
            else:
                for file in glob.glob(
                    os.path.join(self.package_folder, "lib", "libserf-{}.*".format(self._version_major))
                ):
                    os.unlink(file)
        else:
            ext_to_remove = self._static_ext if self.options.shared else self._shared_ext
            for fn in os.listdir(os.path.join(self.package_folder, "lib")):
                if any(re.finditer("\\.{}(\.?|$)".format(ext_to_remove), fn)):
                    os.unlink(os.path.join(self.package_folder, "lib", fn))

    @property
    def _version_major(self):
        return self.version.split(".", 1)[0]

    def package_info(self):
        libprefix = ""
        if self.settings.os == "Windows" and self.options.shared:
            libprefix = "lib"
        libname = "{}serf-{}".format(libprefix, self._version_major)
        self.cpp_info.libs = [libname]
        self.cpp_info.includedirs.append(os.path.join("include", "serf-{}".format(self._version_major)))
        self.cpp_info.names["pkg_config"] = libname
        if self.settings.os == "Windows":
            self.cpp_info.system_libs = [
                "user32",
                "advapi32",
                "gdi32",
                "ws2_32",
                "crypt32",
                "mswsock",
                "rpcrt4",
                "secur32",
            ]
