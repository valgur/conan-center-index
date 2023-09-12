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
import glob

required_conan_version = ">=1.53.0"


class NSSConan(ConanFile):
    name = "nss"
    description = "Network Security Services"
    license = "MPL-2.0"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://developer.mozilla.org/en-US/docs/Mozilla/Projects/NSS"
    topics = ("network", "security", "crypto", "ssl")

    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
    }
    default_options = {
        "shared": True,
        "fPIC": True,
    }

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        self.options["nspr"].shared = True
        self.options["sqlite3"].shared = True

        if self.options.shared:
            self.options.rm_safe("fPIC")
        self.settings.rm_safe("compiler.libcxx")
        self.settings.rm_safe("compiler.cppstd")

    def layout(self):
        basic_layout(self, src_folder="src")

    def requirements(self):
        self.requires("nspr/4.35")
        self.requires("sqlite3/3.43.1")
        self.requires("zlib/1.3")

    def validate(self):
        if not self.options.shared:
            raise ConanInvalidConfiguration(
                "NSS recipe cannot yet build static library. Contributions are welcome."
            )
        if not self.dependencies["nspr"].options.shared:
            raise ConanInvalidConfiguration(
                "NSS cannot link to static NSPR. Please use option nspr:shared=True"
            )
        if msvc_runtime_flag(self) == "MTd":
            raise ConanInvalidConfiguration(
                "NSS recipes does not support MTd runtime. Contributions are welcome."
            )
        if not self.dependencies["sqlite3"].options.shared:
            raise ConanInvalidConfiguration(
                "NSS cannot link to static sqlite. Please use option sqlite3:shared=True"
            )
        if self.settings.arch in ["armv8", "armv8.3"] and is_apple_os(self):
            raise ConanInvalidConfiguration(
                "Macos ARM64 builds not yet supported. Contributions are welcome."
            )
        if Version(self.version) < "3.74":
            if self.settings.compiler == "clang" and Version(self.settings.compiler.version) >= 13:
                raise ConanInvalidConfiguration("nss < 3.74 requires clang < 13 .")

    def build_requirements(self):
        if self._settings_build.os == "Windows":
            self.win_bash = True
            if not self.conf.get("tools.microsoft.bash:path", check_type=str):
                self.tool_requires("msys2/cci.latest")
        if self.settings.os == "Windows":
            self.tool_requires("mozilla-build/3.3")
        if hasattr(self, "settings_build"):
            self.tool_requires("sqlite3/3.43.1")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        # TODO: fill in generate()
        pass

    @property
    def _make_args(self):
        args = []
        if self.settings.arch in ["x86_64"]:
            args.append("USE_64=1")
            if is_apple_os(self):
                args.append("CPU_ARCH=i386")
            else:
                args.append("CPU_ARCH=x86_64")
        if self.settings.arch in ["armv8", "armv8.3"]:
            args.append("USE_64=1")
            args.append("CPU_ARCH=aarch64")
        if self.settings.compiler == "gcc":
            args.append("XCFLAGS=-Wno-array-parameter")
        args.append("NSPR_INCLUDE_DIR=%s" % self.dependencies["nspr"].cpp_info.includedirs[1])
        args.append("NSPR_LIB_DIR=%s" % self.dependencies["nspr"].cpp_info.libdirs[0])

        os_map = {
            "Linux": "Linux",
            "Macos": "Darwin",
            "Windows": "WINNT",
            "FreeBSD": "FreeBSD",
        }

        args.append("OS_TARGET=%s" % os_map.get(str(self.settings.os), "UNSUPPORTED_OS"))
        args.append("OS_ARCH=%s" % os_map.get(str(self.settings.os), "UNSUPPORTED_OS"))
        if self.settings.build_type != "Debug":
            args.append("BUILD_OPT=1")
        if is_msvc(self):
            args.append("NSPR31_LIB_PREFIX=$(NULL)")

        args.append("USE_SYSTEM_ZLIB=1")
        args.append("ZLIB_INCLUDE_DIR=%s" % self.dependencies["zlib"].cpp_info.includedirs[0])

        def adjust_path(path, settings):
            """
            adjusts path to be safely passed to the compiler command line
            for Windows bash, ensures path is in format according to the subsystem
            for path with spaces, places double quotes around it
            converts slashes to backslashes, or vice versa
            """
            compiler = _base_compiler(settings)
            if str(compiler) == "Visual Studio":
                path = path.replace("/", "\\")
            else:
                path = path.replace("\\", "/")
            return '"%s"' % path if " " in path else path

        def _base_compiler(settings):
            return settings.get_safe("compiler.base") or settings.get_safe("compiler")

        def _format_library_paths(library_paths, settings):
            compiler = _base_compiler(settings)
            pattern = "-LIBPATH:%s" if str(compiler) == "Visual Studio" else "-L%s"
            return [
                pattern % adjust_path(library_path, settings)
                for library_path in library_paths
                if library_path
            ]

        def _format_libraries(libraries, settings):
            result = []
            compiler = settings.get_safe("compiler")
            compiler_base = settings.get_safe("compiler.base")
            for library in libraries:
                if str(compiler) == "Visual Studio" or str(compiler_base) == "Visual Studio":
                    if not library.endswith(".lib"):
                        library += ".lib"
                    result.append(library)
                else:
                    result.append(f"-l{library}")
            return result

        args.append(
            '"ZLIB_LIBS=%s"'
            % " ".join(
                _format_libraries(self.dependencies["zlib"].cpp_info.libs, self.settings)
                + _format_library_paths(self.dependencies["zlib"].cpp_info.libdirs, self.settings)
            )
        )
        args.append("NSS_DISABLE_GTESTS=1")
        args.append("NSS_USE_SYSTEM_SQLITE=1")
        args.append("SQLITE_INCLUDE_DIR=%s" % self.dependencies["sqlite3"].cpp_info.includedirs[0])
        args.append("SQLITE_LIB_DIR=%s" % self.dependencies["sqlite3"].cpp_info.libdirs[0])
        args.append("NSDISTMODE=copy")
        if cross_building(self):
            args.append("CROSS_COMPILE=1")
        return args

    def build(self):
        apply_conandata_patches(self)
        with chdir(self, os.path.join(self.source_folder, "nss")):
            with vcvars(self) if is_msvc(self) else nullcontext():
                self.run(f"make {' '.join(self._make_args)}", run_environment=True)

    def package(self):
        copy(self, "COPYING",
             src=os.path.join(self.source_folder, "nss"),
             dst=os.path.join(self.package_folder, "licenses"))
        with chdir(self, os.path.join(self.source_folder, "nss")):
            self.run("make install %s" % " ".join(self._make_args))
        copy(self, "*",
             src=os.path.join(self.source_folder, "dist", "public", "nss"),
             dst=os.path.join(self.package_folder, "include"))
        for d in os.listdir(os.path.join(self.source_folder, "dist")):
            if d in ["private", "public"]:
                continue
            f = os.path.join(self.source_folder, "dist", d)
            if not os.path.isdir(f):
                continue
            copy(self, "*", src=f)

        for dll_file in glob.glob(os.path.join(self.package_folder, "lib", "*.dll")):
            rename(self, dll_file, os.path.join(self.package_folder, "bin", os.path.basename(dll_file)))

        if self.options.shared:
            rm(self, "*.a", os.path.join(self.package_folder, "lib"))
        else:
            rm(self, "*.so", os.path.join(self.package_folder, "lib"))
            rm(self, "*.dll", os.path.join(self.package_folder, "bin"))

    def package_info(self):
        def _library_name(lib, vers):
            return f"{lib}{vers}" if self.options.shared else lib

        self.cpp_info.components["libnss"].libs.append(_library_name("nss", 3))
        self.cpp_info.components["libnss"].requires = ["nssutil", "nspr::nspr"]

        self.cpp_info.components["nssutil"].libs = [_library_name("nssutil", 3)]
        self.cpp_info.components["nssutil"].requires = ["nspr::nspr"]
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.components["nssutil"].system_libs = ["pthread"]

        self.cpp_info.components["softokn"].libs = [_library_name("softokn", 3)]
        self.cpp_info.components["softokn"].requires = ["sqlite3::sqlite3", "nssutil", "nspr::nspr"]
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.components["softokn"].system_libs = ["pthread"]

        self.cpp_info.components["nssdbm"].libs = [_library_name("nssdbm", 3)]
        self.cpp_info.components["nssdbm"].requires = ["nspr::nspr", "nssutil"]
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.components["nssdbm"].system_libs = ["pthread"]

        self.cpp_info.components["smime"].libs = [_library_name("smime", 3)]
        self.cpp_info.components["smime"].requires = ["nspr::nspr", "libnss", "nssutil"]

        self.cpp_info.components["ssl"].libs = [_library_name("ssl", 3)]
        self.cpp_info.components["ssl"].requires = ["nspr::nspr", "libnss", "nssutil"]
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.components["ssl"].system_libs = ["pthread"]

        self.cpp_info.components["nss_executables"].requires = ["zlib::zlib"]

        self.cpp_info.set_property("pkg_config_name", "nss")
