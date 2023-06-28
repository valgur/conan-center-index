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
import functools
import os
import shutil

required_conan_version = ">=1.53.0"


class SqlcipherConan(ConanFile):
    name = "sqlcipher"
    description = "SQLite extension that provides 256 bit AES encryption of database files."
    license = "BSD-3-Clause"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://www.zetetic.net/sqlcipher/"
    topics = ("database", "encryption", "SQLite")

    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "crypto_library": ["openssl", "libressl", "commoncrypto"],
        "with_largefile": [True, False],
        "temporary_store": ["always_file", "default_file", "default_memory", "always_memory"],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "crypto_library": "openssl",
        "with_largefile": True,
        "temporary_store": "default_memory",
    }

    @property
    def _settings_build(self):
        return getattr(self, "settings_build", self.settings)

    @property
    def _user_info_build(self):
        return getattr(self, "user_info_build", self.deps_user_info)

    def export_sources(self):
        export_conandata_patches(self)

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC
        if self.settings.os != "Linux":
            self.options.rm_safe("with_largefile")

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")
        self.settings.rm_safe("compiler.libcxx")
        self.settings.rm_safe("compiler.cppstd")

    def layout(self):
        pass

    def requirements(self):
        if self.options.crypto_library == "openssl":
            self.requires("openssl/1.1.1n")
        elif self.options.crypto_library == "libressl":
            self.requires("libressl/3.4.3")

    def validate(self):
        if self.options.crypto_library == "commoncrypto" and not is_apple_os(self.settings.os):
            raise ConanInvalidConfiguration("commoncrypto is only supported on Macos")

    def build_requirements(self):
        self.build_requires("tcl/8.6.11")
        if not is_msvc(self):
            self.build_requires("gnu-config/cci.20201022")
            if self._settings_build.os == "Windows" and not get_env(self, "CONAN_BASH_PATH"):
                self.build_requires("msys2/cci.latest")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        if is_msvc(self):
            self._generate_msvc()
        else:
            self._generate_autotools()

    @property
    def _temp_store_nmake_value(self):
        return {
            "always_file": "0",
            "default_file": "1",
            "default_memory": "2",
            "always_memory": "3",
        }.get(str(self.options.temporary_store))

    @property
    def _temp_store_autotools_value(self):
        return {
            "always_file": "never",
            "default_file": "no",
            "default_memory": "yes",
            "always_memory": "always",
        }.get(str(self.options.temporary_store))

    def _build_visual(self):
        crypto_dep = self.dependencies[str(self.options.crypto_library)].cpp_info
        crypto_incdir = crypto_dep.includedirs[0]
        crypto_libdir = crypto_dep.libdirs[0]
        libs = map(lambda lib: lib + ".lib", crypto_dep.libs)
        system_libs = map(lambda lib: lib + ".lib", crypto_dep.system_libs)

        nmake_flags = [
            'TLIBS="%s %s"' % (" ".join(libs), " ".join(system_libs)),
            "LTLIBPATHS=/LIBPATH:%s" % crypto_libdir,
            'OPTS="-I%s -DSQLITE_HAS_CODEC"' % (crypto_incdir),
            "NO_TCL=1",
            "USE_AMALGAMATION=1",
            "OPT_FEATURE_FLAGS=-DSQLCIPHER_CRYPTO_OPENSSL",
            "SQLITE_TEMP_STORE=%s" % self._temp_store_nmake_value,
            "TCLSH_CMD=%s" % os.pathsep.join(dep.buildenv_info.TCLSH for dep in self.dependencies.values()),
        ]

        main_target = "dll" if self.options.shared else "sqlcipher.lib"

        if msvc_runtime_flag(self) in ["MD", "MDd"]:
            nmake_flags.append("USE_CRT_DLL=1")
        if self.settings.build_type == "Debug":
            nmake_flags.append("DEBUG=2")
        nmake_flags.append("FOR_WIN10=1")
        platforms = {
            "x86": "x86",
            "x86_64": "x64",
        }
        nmake_flags.append("PLATFORM=%s" % platforms[str(self.settings.arch)])
        vcvars = vcvars_command(self.settings)
        self.run(
            "%s && nmake /f Makefile.msc %s %s" % (vcvars, main_target, " ".join(nmake_flags)),
            cwd=self.source_folder,
        )

    @staticmethod
    def _chmod_plus_x(filename):
        if os.name == "posix":
            os.chmod(filename, os.stat(filename).st_mode | 0o111)

    def _build_autotools(self):
        shutil.copy(
            self._user_info_build["gnu-config"].CONFIG_SUB, os.path.join(self.source_folder, "config.sub")
        )
        shutil.copy(
            self._user_info_build["gnu-config"].CONFIG_GUESS, os.path.join(self.source_folder, "config.guess")
        )
        configure = os.path.join(self.source_folder, "configure")
        self._chmod_plus_x(configure)
        # relocatable shared libs on macOS
        replace_in_file(self, configure, "-install_name \\$rpath/", "-install_name @rpath/")
        # avoid SIP issues on macOS when dependencies are shared
        if is_apple_os(self.settings.os):
            libdirs = sum([dep.cpp_info.libdirs for dep in self.dependencies.values()], [])
            libpaths = ":".join(libdirs)
            replace_in_file(
                self,
                configure,
                "#! /bin/sh\n",
                "#! /bin/sh\nexport DYLD_LIBRARY_PATH={}:$DYLD_LIBRARY_PATH\n".format(libpaths),
            )
        autotools = Autotools(self)
        autotools.configure()
        autotools.make()

    def _generate_autotools(self):
        yes_no = lambda v: "yes" if v else "no"
        tc.configure_args = [
            "--enable-tempstore={}".format(self._temp_store_autotools_value),
            "--disable-tcl",
        ]
        if self.settings.os == "Windows":
            args.extend(["config_BUILD_EXEEXT='.exe'", "config_TARGET_EXEEXT='.exe'"])

        autotools = AutoToolsBuildEnvironment(self, win_bash=tools.os_info.is_windows)
        if self.settings.os == "Linux":
            autotools.libs.append("dl")
            if not self.options.with_largefile:
                autotools.defines.append("SQLITE_DISABLE_LFS=1")
        autotools.defines.append("SQLITE_HAS_CODEC")

        env_vars = autotools.vars
        tclsh_cmd = self.deps_env_info.TCLSH
        env_vars["TCLSH_CMD"] = tclsh_cmd.replace("\\", "/")
        if self._use_commoncrypto():
            env_vars["LDFLAGS"] += " -framework Security -framework CoreFoundation "
            args.append("--with-crypto-lib=commoncrypto")
        else:
            autotools.defines.append("SQLCIPHER_CRYPTO_OPENSSL")

        autotools.configure(configure_dir=self.source_folder, args=args, vars=env_vars)
        if self.settings.os == "Windows":
            # sqlcipher will create .exe for the build machine, which we defined to Linux...
            replace_in_file(self, "Makefile", "BEXE = .exe", "BEXE = ")
        return autotools

    def _use_commoncrypto(self):
        return self.options.crypto_library == "commoncrypto" and is_apple_os(self.settings.os)

    def build(self):
        apply_conandata_patches(self)
        if is_msvc(self):
            self._build_visual()
        else:
            self._build_autotools()

    def _package_unix(self):
        autotools = Autotools(self)
        autotools.install()
        rm(self, "*.la", self.package_folder, recursive=True)
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))

    def _package_visual(self):
        copy(self, "*.dll", dst=os.path.join(self.package_folder, "bin"), keep_path=False)
        copy(self, "*.lib", dst=os.path.join(self.package_folder, "lib"), keep_path=False)
        copy(self, "sqlite3.h", src=self.source_folder, dst=os.path.join("include", "sqlcipher"))

    def package(self):
        copy(self, "LICENSE", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder)
        if is_msvc(self):
            self._package_visual()
        else:
            self._package_unix()

    def package_info(self):
        self.cpp_info.set_property("pkg_config_name", "sqlcipher")
        self.cpp_info.libs = ["sqlcipher"]
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs.extend(["pthread", "dl"])
            if Version(self.version) >= "4.5.0":
                self.cpp_info.system_libs.append("m")
        self.cpp_info.defines = [
            "SQLITE_HAS_CODEC",
            "SQLITE_TEMP_STORE={}".format(self._temp_store_nmake_value),
        ]
        if self._use_commoncrypto():
            self.cpp_info.frameworks = ["Security", "CoreFoundation"]
        else:
            self.cpp_info.defines.append("SQLCIPHER_CRYPTO_OPENSSL")
        # Allow using #include <sqlite3.h> even with sqlcipher (for libs like sqlpp11-connector-sqlite3)
        self.cpp_info.includedirs.append(os.path.join("include", "sqlcipher"))
