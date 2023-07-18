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

required_conan_version = ">=1.53.0"


class LibTomMathConan(ConanFile):
    name = "libtommath"
    description = (
        "LibTomMath is a free open source portable number theoretic "
        "multiple-precision integer library written entirely in C."
    )
    license = "Unlicense"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://www.libtom.net/"
    topics = ("libtommath", "math", "multiple", "precision")

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

    @property
    def _settings_build(self):
        return getattr(self, "settings_build", self.settings)

    def export_sources(self):
        export_conandata_patches(self)

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")
        self.settings.rm_safe("compiler.libcxx")
        self.settings.rm_safe("compiler.cppstd")

    def layout(self):
        basic_layout(self, src_folder="src")

    def build_requirements(self):
        if self._settings_build.os == "Windows" and not is_msvc(self):
            self.build_requires("make/4.3")
        if not is_msvc(self) and self.settings.os != "Windows" and self.options.shared:
            self.tool_requires("libtool/2.4.7")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        # TODO: fill in generate()
        pass

    def _run_makefile(self, target=None):
        target = target or ""
        autotools = AutoToolsBuildEnvironment(self)
        autotools.libs = []
        if self.settings.os == "Windows" and not is_msvc(self):
            autotools.link_flags.append("-lcrypt32")
        if self.settings.os == "Macos" and self.settings.arch == "armv8":
            # FIXME: should be handled by helper
            autotools.link_flags.append("-arch arm64")
        args = autotools.vars
        args.update({"PREFIX": self.package_folder})
        if not is_msvc(self):
            if os.environ.get("CC"):
                args["CC"] = os.environ.get("CC")
            if os.environ.get("LD"):
                args["LD"] = os.environ.get("LD")
            if os.environ.get("AR"):
                args["AR"] = os.environ.get("AR")

            args["LIBTOOL"] = "libtool"
        arg_str = " ".join(f'{k}="{v}"' for k, v in args.items())

        with environment_append(self, args):
            with chdir(self, self.source_folder):
                if is_msvc(self):
                    if self.options.shared:
                        target = "tommath.dll"
                    else:
                        target = "tommath.lib"
                    with vcvars(self):
                        self.run("nmake -f makefile.msvc {} {}".format(target, arg_str), run_environment=True)
                else:
                    if self.settings.os == "Windows":
                        makefile = "makefile.mingw"
                        if self.options.shared:
                            target = "libtommath.dll"
                        else:
                            target = "libtommath.a"
                    else:
                        if self.options.shared:
                            makefile = "makefile.shared"
                        else:
                            makefile = "makefile.unix"
                    self.run(
                        (
                            f"{get_env(self, 'CONAN_MAKE_PROGRAM', 'make')} "
                            f"-f {makefile} {target} {arg_str} "
                            f"-j{cpu_count(self)}"
                        ),
                        run_environment=True,
                    )

    def build(self):
        apply_conandata_patches(self)
        self._run_makefile()

    def package(self):
        copy(self, "LICENSE", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        if self.settings.os == "Windows":
            # The mingw makefile uses `cmd`, which is only available on Windows
            copy(self, "*.a", src=self.source_folder, dst=os.path.join(self.package_folder, "lib"))
            copy(self, "*.lib", src=self.source_folder, dst=os.path.join(self.package_folder, "lib"))
            copy(self, "*.dll", src=self.source_folder, dst=os.path.join(self.package_folder, "bin"))
            copy(self, "tommath.h", src=self.source_folder, dst=os.path.join(self.package_folder, "include"))
        else:
            self._run_makefile("install")

        rm(self, "*.la", self.package_folder, recursive=True)
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))

        if is_msvc(self) and self.options.shared:
            os.rename(
                os.path.join(self.package_folder, "lib", "tommath.dll.lib"),
                os.path.join(self.package_folder, "lib", "tommath.lib"),
            )

    def package_info(self):
        self.cpp_info.libs = ["tommath"]
        if not self.options.shared:
            if self.settings.os == "Windows":
                self.cpp_info.system_libs = ["advapi32", "crypt32"]

        self.cpp_info.set_property("pkg_config_name", "libtommath")
