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
from contextlib import contextmanager
import os

required_conan_version = ">=1.53.0"


class IslConan(ConanFile):
    name = "isl"
    description = (
        "isl is a library for manipulating sets and relations of integer points bounded by linear"
        " constraints."
    )
    license = "MIT"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://libisl.sourceforge.io"
    topics = ("integer", "set", "library")

    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "with_int": ["gmp", "imath", "imath-32"],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "with_int": "gmp",
    }

    @property
    def _settings_build(self):
        return getattr(self, "settings_build", self.settings)

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

    def requirements(self):
        if self.options.with_int == "gmp":
            self.requires("gmp/6.2.1")

    def validate(self):
        if self.settings.os == "Windows" and self.options.shared:
            raise ConanInvalidConfiguration(
                "Cannot build shared isl library on Windows (due to libtool refusing to link to static/import"
                " libraries)"
            )
        if self.settings.os == "Macos" and self.settings.arch == "armv8":
            raise ConanInvalidConfiguration("Apple M1 is not yet supported. Contributions are welcome")
        if self.options.with_int != "gmp":
            # FIXME: missing imath recipe
            raise ConanInvalidConfiguration("imath is not (yet) available on cci")
        if (
            is_msvc(self)
            and Version(self.settings.compiler.version) < 16
            and self.settings.compiler.runtime == "MDd"
        ):
            # gmp.lib(bdiv_dbm1c.obj) : fatal error LNK1318: Unexpected PDB error; OK (0)
            raise ConanInvalidConfiguration(
                "isl fails to link with this version of visual studio and MDd runtime"
            )

    def build_requirements(self):
        if self._settings_build.os == "Windows":
            self.win_bash = True
            if not self.conf.get("tools.microsoft.bash:path", check_type=str):
                self.tool_requires("msys2/cci.latest")
        if is_msvc(self):
            self.build_requires("automake/1.16.5")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        # TODO: fill in generate()
        pass

    @contextmanager
    def _build_context(self):
        if is_msvc(self):
            with vcvars(self.settings):
                env = {
                    "AR": "{} lib".format(unix_path(self, self.conf_info.get("user.automake:ar_lib"))),
                    "CC": "{} cl -nologo -{}".format(
                        unix_path(self, self.conf_info.get("user.automake:compile")),
                        self.settings.compiler.runtime,
                    ),
                    "CXX": "{} cl -nologo -{}".format(
                        unix_path(self, self.conf_info.get("user.automake:compile")),
                        self.settings.compiler.runtime,
                    ),
                    "NM": "dumpbin -symbols",
                    "OBJDUMP": ":",
                    "RANLIB": ":",
                    "STRIP": ":",
                }
                with environment_append(self, env):
                    yield
        else:
            yield

    def _configure_autotools(self):
        tc = AutotoolsToolchain(self)
        yes_no = lambda v: "yes" if v else "no"
        tc.configure_args += [
            "--with-int={}".format(self.options.with_int),
            "--enable-portable-binary",
        ]
        if self.options.with_int == "gmp":
            tc.configure_args.extend(
                [
                    "--with-gmp=system",
                    "--with-gmp-prefix={}".format(self.dependencies["gmp"].package_folder.replace("\\", "/")),
                ]
            )
        if is_msvc(self):
            if Version(self.settings.compiler.version) >= 15:
                tc.cxxflags.append("-Zf")
            if Version(self.settings.compiler.version) >= 12:
                tc.cxxflags.append("-FS")
        tc.generate()

    def build(self):
        with self._build_context():
            autotools = Autotools(self)
            autotools.configure()
            autotools.make()

    def package(self):
        copy(self, "LICENSE", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        with self._build_context():
            autotools = Autotools(self)
            autotools.install()

        os.unlink(os.path.join(os.path.join(self.package_folder, "lib", "libisl.la")))
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))

    def package_info(self):
        self.cpp_info.set_property("pkg_config_name", "isl")
        self.cpp_info.libs = ["isl"]
