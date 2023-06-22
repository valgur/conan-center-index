# TODO: verify the Conan v2 migration

import functools
import os
import stat

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


class NetSnmpConan(ConanFile):
    name = "net-snmp"
    description = (
        "Simple Network Management Protocol (SNMP) is a widely used protocol "
        "for monitoring the health and welfare of network equipment "
        "(eg. routers), computer equipment and even devices like UPSs."
    )
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "http://www.net-snmp.org/"
    topics = "snmp"
    license = "BSD-3-Clause"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "with_ipv6": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "with_ipv6": True,
    }

    def requirements(self):
        self.requires("openssl/1.1.1m")

    @property
    def _is_msvc(self):
        return self.settings.compiler in ("Visual Studio", "msvc")

    def export_sources(self):
        export_conandata_patches(self)

    def validate(self):
        if self.settings.os == "Windows" and not is_msvc(self):
            raise ConanInvalidConfiguration("net-snmp is setup to build only with MSVC on Windows")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")
        self.settings.rm_safe("compiler.libcxx")
        self.settings.rm_safe("compiler.cppstd")

    def build_requirements(self):
        if is_msvc(self):
            self.build_requires("strawberryperl/5.30.0.1")

    @property
    def _is_debug(self):
        return self.settings.build_type == "Debug"

    def _patch_msvc(self):
        ssl_info = self.deps_cpp_info["openssl"]
        openssl_root = ssl_info.rootpath.replace("\\", "/")
        search_replace = [
            (r'$default_openssldir . "\\include"', f"'{openssl_root}/include'"),
            (r'$default_openssldir . "\\lib\\VC"', f"'{openssl_root}/lib'"),
            ("$openssl = false", "$openssl = true"),
        ]
        if self._is_debug:
            search_replace.append(("$debug = false", "$debug = true"))
        if self.options.shared:
            search_replace.append(("$link_dynamic = false", "$link_dynamic = true"))
        if self.options.with_ipv6:
            search_replace.append(("$b_ipv6 = false", "$b_ipv6 = true"))
        for search, replace in search_replace:
            replace_in_file(self, "win32\\build.pl", search, replace)
        runtime = self.settings.compiler.runtime
        replace_in_file(self, "win32\\Configure", '"/runtime', f'"/{runtime}')
        link_lines = "\n".join(
            f'#    pragma comment(lib, "{lib}.lib")' for lib in ssl_info.libs + ssl_info.system_libs
        )
        config = r"win32\net-snmp\net-snmp-config.h.in"
        replace_in_file(self, config, "/* Conan: system_libs */", link_lines)

    def _build_msvc(self):
        if self.should_configure:
            self._patch_msvc()
            self.run("perl build.pl", cwd="win32")
        if self.should_build:
            with vcvars(self):
                self.run("nmake /nologo libsnmp", cwd="win32")

    @functools.lru_cache(1)
    def _configure_autotools(self):
        disabled_link_type = "static" if self.options.shared else "shared"
        debug_flag = "enable" if self._is_debug else "disable"
        ipv6_flag = "enable" if self.options.with_ipv6 else "disable"
        ssl_path = self.deps_cpp_info["openssl"].rootpath
        args = [
            "--with-defaults",
            "--without-rpm",
            "--without-pcre",
            "--disable-agent",
            "--disable-applications",
            "--disable-manuals",
            "--disable-scripts",
            "--disable-mibs",
            "--disable-embedded-perl",
            f"--disable-{disabled_link_type}",
            f"--{debug_flag}-debugging",
            f"--{ipv6_flag}-ipv6",
            f"--with-openssl={ssl_path}",
        ]
        autotools = AutoToolsBuildEnvironment(self)
        autotools.libs = []
        autotools.configure(args=args)
        return autotools

    def _patch_unix(self):
        replace_in_file(self, "configure", "-install_name \\$rpath/", "-install_name @rpath/")
        crypto_libs = self.deps_cpp_info["openssl"].system_libs
        if len(crypto_libs) != 0:
            crypto_link_flags = " -l".join(crypto_libs)
            replace_in_file(
                self,
                "configure",
                'LIBCRYPTO="-l${CRYPTO}"',
                'LIBCRYPTO="-l${CRYPTO} -l%s"' % (crypto_link_flags,),
            )
            replace_in_file(
                self, "configure", 'LIBS="-lcrypto  $LIBS"', f'LIBS="-lcrypto -l{crypto_link_flags} $LIBS"'
            )

    def build(self):
        apply_conandata_patches(self)
        if is_msvc(self):
            self._build_msvc()
        else:
            self._patch_unix()
            os.chmod("configure", os.stat("configure").st_mode | stat.S_IEXEC)
            self._configure_autotools().make(target="snmplib", args=["NOAUTODEPS=1"])

    def _package_msvc(self):
        cfg = "debug" if self._is_debug else "release"
        copy(self, "netsnmp.dll", "bin", rf"win32\bin\{cfg}")
        copy(self, "netsnmp.lib", "lib", rf"win32\lib\{cfg}")
        copy(self, "include/net-snmp/*.h")
        for directory in ["", "agent/", "library/"]:
            copy(self, f"net-snmp/{directory}*.h", "include", "win32")
        copy(self, "COPYING", "licenses")

    def _remove(self, path):
        if os.path.isdir(path):
            rmdir(self, path)
        else:
            os.remove(path)

    def _package_unix(self):
        self._configure_autotools().install(args=["NOAUTODEPS=1"])
        remove_files_by_mask(self.package_folder, "README")
        rmdir(self, os.path.join(self.package_folder, "bin"))
        lib_dir = os.path.join(self.package_folder, "lib")
        for entry in os.listdir(lib_dir):
            if not entry.startswith("libnetsnmp.") or entry.endswith(".la"):
                self._remove(os.path.join(lib_dir, entry))
        copy(self, "COPYING", "licenses")

    def package(self):
        if is_msvc(self):
            self._package_msvc()
        else:
            self._package_unix()

    def package_info(self):
        self.cpp_info.libs = ["netsnmp"]
        self.cpp_info.requires = ["openssl::openssl"]
