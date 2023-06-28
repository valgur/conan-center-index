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
import contextlib
import functools
import os

required_conan_version = ">=1.53.0"


class SwigConan(ConanFile):
    name = "swig"
    description = (
        "SWIG is a software development tool that connects programs written in C and C++ with a variety of"
        " high-level programming languages."
    )
    license = "GPL-3.0-or-later"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "http://www.swig.org"
    topics = ("python", "java", "wrapper")

    package_type = "application"
    settings = "os", "arch", "compiler", "build_type"

    @property
    def _settings_build(self):
        return getattr(self, "settings_build", self.settings)

    @property
    def _use_pcre2(self):
        return self.version not in ["4.0.1", "4.0.2"]

    def export_sources(self):
        copy(self, "cmake", src=self.recipe_folder, dst=self.export_sources_folder)
        export_conandata_patches(self)

    def layout(self):
        basic_layout(self, src_folder="src")

    def requirements(self):
        if self._use_pcre2:
            self.requires("pcre2/10.40")
        else:
            self.requires("pcre/8.45")

    def package_id(self):
        del self.info.settings.compiler

    def build_requirements(self):
        if self._settings_build.os == "Windows" and not get_env(self, "CONAN_BASH_PATH"):
            self.build_requires("msys2/cci.latest")
        if is_msvc(self):
            self.build_requires("winflexbison/2.5.24")
        else:
            self.build_requires("bison/3.8.2")
        self.build_requires("automake/1.16.5")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    @contextlib.contextmanager
    def _build_context(self):
        env = {}
        if not is_msvc(self):
            env["YACC"] = self.conf_info.get("user.bison:yacc")
        if is_msvc(self):
            with vcvars(self):
                env.update(
                    {
                        "CC": "{} cl -nologo".format(
                            unix_path(self, self.conf_info.get("user.automake:compile-wrapper"))
                        ),
                        "CXX": "{} cl -nologo".format(
                            unix_path(self, self.conf_info.get("user.automake:compile-wrapper"))
                        ),
                        "AR": "{} link".format(self.conf_info.get("user.automake:lib-wrapper")),
                        "LD": "link",
                    }
                )
                with environment_append(self, env):
                    yield
        else:
            with environment_append(self, env):
                yield

    def generate(self):
        autotools = AutoToolsBuildEnvironment(self)
        deps_libpaths = autotools.library_paths
        deps_libs = autotools.libs
        deps_defines = autotools.defines
        if self.settings.os == "Windows" and not is_msvc(self):
            autotools.link_flags.append("-static")

        libargs = list(f'-L"{p}"' for p in deps_libpaths) + list(f'-l"{l}"' for l in deps_libs)
        args = [
            "{}_LIBS={}".format("PCRE2" if self._use_pcre2 else "PCRE", " ".join(libargs)),
            "{}_CPPFLAGS={}".format(
                "PCRE2" if self._use_pcre2 else "PCRE",
                " ".join(f"-D{define}" for define in deps_defines),
            ),
            f"--host={self.settings.arch}",
            f"--with-swiglibdir={self._swiglibdir}",
        ]
        if self.settings.os == "Linux":
            args.append("LIBS=-ldl")

        host, build = None, None

        if is_msvc(self):
            self.output.warning("Visual Studio compiler cannot create ccache-swig. Disabling ccache-swig.")
            args.append("--disable-ccache")
            autotools.flags.append("-FS")
            # MSVC canonical names aren't understood
            host, build = False, False

        if self.settings.os == "Macos" and self.settings.arch == "armv8":
            # FIXME: Apple ARM should be handled by build helpers
            autotools.flags.append("-arch arm64")
            autotools.link_flags.append("-arch arm64")

        autotools.libs = []
        autotools.library_paths = []

        if self.settings.os == "Windows" and not is_msvc(self):
            autotools.libs.extend(["mingwex", "ssp"])

        autotools.configure(args=args, configure_dir=self.source_folder, host=host, build=build)
        return autotools

    def _patch_sources(self):
        apply_conandata_patches(self)

    def build(self):
        self._patch_sources()
        with self._build_context():
            autotools = Autotools(self)
            autotools.configure()
            autotools.make()

    def package(self):
        copy(
            self,
            pattern="LICENSE*",
            dst=os.path.join(self.package_folder, "licenses"),
            src=self.source_folder,
        )
        copy(
            self,
            pattern="COPYRIGHT",
            dst=os.path.join(self.package_folder, "licenses"),
            src=self.source_folder,
        )
        copy(self, "*", src="cmake", dst=self._module_subfolder)
        with self._build_context():
            autotools = Autotools(self)
            autotools.install()

    @property
    def _swiglibdir(self):
        return os.path.join(self.package_folder, "bin", "swiglib").replace("\\", "/")

    @property
    def _module_subfolder(self):
        return os.path.join("lib", "cmake")

    @property
    def _module_file(self):
        return f"conan-official-{self.name}-targets.cmake"

    def package_info(self):
        self.cpp_info.includedirs = []
        self.cpp_info.set_property("cmake_file_name", "SWIG")
        self.cpp_info.set_property("cmake_target_name", "SWIG")
        self.cpp_info.builddirs = [self._module_subfolder]
        self.cpp_info.build_modules["cmake_find_package"] = [
            os.path.join(self._module_subfolder, self._module_file)
        ]
        self.cpp_info.build_modules["cmake_find_package_multi"] = [
            os.path.join(self._module_subfolder, self._module_file)
        ]

        bindir = os.path.join(self.package_folder, "bin")
        self.output.info("Appending PATH environment variable: {}".format(bindir))
        self.env_info.PATH.append(bindir)

        # TODO: to remove in conan v2 once cmake_find_package_* generators removed
        self.cpp_info.names["cmake_find_package"] = "SWIG"
        self.cpp_info.names["cmake_find_package_multi"] = "SWIG"
