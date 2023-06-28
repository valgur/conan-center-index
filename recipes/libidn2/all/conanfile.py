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


class LibIdn(ConanFile):
    name = "libidn2"
    description = (
        "GNU Libidn is a fully documented implementation of the Stringprep, Punycode and IDNA 2003"
        " specifications."
    )
    license = "GPL-3.0-or-later"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://www.gnu.org/software/libidn/"
    topics = ("libidn", "encode", "decode", "internationalized", "domain", "name")

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

    def requirements(self):
        self.requires("libiconv/1.16")

    def validate(self):
        if self.settings.os == "Windows" and self.options.shared:
            raise ConanInvalidConfiguration(
                "Shared libraries are not supported on Windows due to libtool limitation"
            )

    def build_requirements(self):
        if self._settings_build.os == "Windows" and not get_env(self, "CONAN_BASH_PATH"):
            self.build_requires("msys2/cci.latest")
        if is_msvc(self):
            self.build_requires("automake/1.16.4")

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
                    "CC": "{} cl -nologo".format(
                        unix_path(self, self.conf_info.get("user.automake:compile"))
                    ),
                    "CXX": "{} cl -nologo".format(
                        unix_path(self, self.conf_info.get("user.automake:compile"))
                    ),
                    "LD": "{} link -nologo".format(
                        unix_path(self, self.conf_info.get("user.automake:compile"))
                    ),
                    "AR": "{} lib".format(unix_path(self, self.conf_info.get("user.automake:ar_lib"))),
                }
                with environment_append(self, env):
                    yield
        else:
            yield

    def _configure_autotools(self):
        tc = AutotoolsToolchain(self)
        if not self.options.shared:
            tc.defines.append("IDN2_STATIC")
        if is_msvc(self):
            if Version(self.settings.compiler.version) >= "12":
                tc.cxxflags.append("-FS")
            for dep in self.dependencies.values():
                tc.ldflags.extend(
                    "-L{}".format(p.replace("\\", "/")) for p in dep.cpp_info.aggregated_components().libdirs
                )
        yes_no = lambda v: "yes" if v else "no"
        tc.configure_args = [
            "--with-libiconv-prefix={}".format(
                unix_path(self, self.dependencies["libiconv"].cpp_info.rootpath)
            ),
            "--disable-nls",
            "--disable-rpath",
        ]
        tc.generate()

    def build(self):
        apply_conandata_patches(self)
        with self._build_context():
            autotools = Autotools(self)
            autotools.configure()
            autotools.make()

    def package(self):
        copy(self, "COPYING", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        with self._build_context():
            autotools = Autotools(self)
            autotools.install()

        os.unlink(os.path.join(self.package_folder, "lib", "libidn2.la"))

        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))
        rmdir(self, os.path.join(self.package_folder, "share"))

    def package_info(self):
        self.cpp_info.libs = ["idn2"]
        self.cpp_info.names["pkg_config"] = "libidn2"
        if self.settings.os == "Windows":
            if not self.options.shared:
                self.cpp_info.defines = ["IDN2_STATIC"]

        bin_path = os.path.join(self.package_folder, "bin")
        self.output.info(f"Appending PATH environment variable: {bin_path}")
        self.env_info.PATH.append(bin_path)
