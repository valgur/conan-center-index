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


class TkConan(ConanFile):
    name = "tk"
    description = (
        "Tk is a graphical user interface toolkit that takes developing desktop applications to a higher"
        " level than conventional approaches."
    )
    license = "TCL"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://tcl.tk"
    topics = ("gui", "tcl", "scripting", "programming")

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
        self.requires("tcl/{}".format(self.version))
        if self.settings.os == "Linux":
            self.requires("fontconfig/2.13.93")
            self.requires("xorg/system")

    def validate(self):
        if self.options["tcl"].shared != self.options.shared:
            raise ConanInvalidConfiguration("The shared option of tcl and tk must have the same value")

    def build_requirements(self):
        if not is_msvc(self):
            if self.settings.os == "Windows" and not get_env(self, "CONAN_BASH_PATH"):
                self.build_requires("msys2/cci.latest")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def _patch_sources(self):
        for build_system in ("unix", "win"):
            config_dir = self._get_configure_folder(build_system)

            if build_system != "win":
                # When disabling 64-bit support (in 32-bit), this test must be 0 in order to use "long long" for 64-bit ints
                # (${tcl_type_64bit} can be either "__int64" or "long long")
                replace_in_file(
                    self,
                    os.path.join(config_dir, "configure"),
                    "(sizeof(${tcl_type_64bit})==sizeof(long))",
                    "(sizeof(${tcl_type_64bit})!=sizeof(long))",
                )

            makefile_in = os.path.join(config_dir, "Makefile.in")
            # Avoid clearing CFLAGS and LDFLAGS in the makefile
            # replace_in_file(self, makefile_in, "\nCFLAGS{}".format(" " if (build_system == "win" and name == "tcl") else "\t"), "\n#CFLAGS\t")
            replace_in_file(self, makefile_in, "\nLDFLAGS\t", "\n#LDFLAGS\t")
            replace_in_file(self, makefile_in, "${CFLAGS}", "${CFLAGS} ${CPPFLAGS}")

        rules_ext_vc = os.path.join(self.source_folder, "win", "rules-ext.vc")
        replace_in_file(self, rules_ext_vc, "\n_RULESDIR = ", "\n_RULESDIR = .\n#_RULESDIR = ")
        rules_vc = os.path.join(self.source_folder, "win", "rules.vc")
        replace_in_file(self, rules_vc, r"$(_TCLDIR)\generic", r"$(_TCLDIR)\include")
        replace_in_file(self, rules_vc, "\nTCLSTUBLIB", "\n#TCLSTUBLIB")
        replace_in_file(self, rules_vc, "\nTCLIMPLIB", "\n#TCLIMPLIB")

        win_makefile_in = os.path.join(self._get_configure_folder("win"), "Makefile.in")
        replace_in_file(self, win_makefile_in, "\nTCL_GENERIC_DIR", "\n#TCL_GENERIC_DIR")

        win_rules_vc = os.path.join(self.source_folder, "win", "rules.vc")
        replace_in_file(self, win_rules_vc, "\ncwarn = $(cwarn) -WX", "\n# cwarn = $(cwarn) -WX")
        # disable whole program optimization to be portable across different MSVC versions.
        # See conan-io/conan-center-index#4811 conan-io/conan-center-index#4094
        replace_in_file(
            self,
            win_rules_vc,
            "OPTIMIZATIONS  = $(OPTIMIZATIONS) -GL",
            "# OPTIMIZATIONS  = $(OPTIMIZATIONS) -GL",
        )

    def _get_default_build_system(self):
        if is_apple_os(self.settings.os):
            return "macosx"
        elif self.settings.os in ("Linux", "FreeBSD"):
            return "unix"
        elif self.settings.os == "Windows":
            return "win"
        else:
            raise ValueError("tk recipe does not recognize os")

    def _get_configure_folder(self, build_system=None):
        if build_system is None:
            build_system = self._get_default_build_system()
        if build_system not in ["win", "unix", "macosx"]:
            raise ConanExceptionInUserConanfileMethod("Invalid build system: {}".format(build_system))
        return os.path.join(self.source_folder, build_system)

    def _build_nmake(self, target="release"):
        # https://core.tcl.tk/tips/doc/trunk/tip/477.md
        opts = []
        if not self.options.shared:
            opts.append("static")
        if self.settings.build_type == "Debug":
            opts.append("symbols")
        if "MD" in str(self.settings.compiler.runtime):
            opts.append("msvcrt")
        else:
            opts.append("nomsvcrt")
        if "d" not in str(self.settings.compiler.runtime):
            opts.append("unchecked")
        # https://core.tcl.tk/tk/tktview?name=3d34589aa0
        # https://wiki.tcl-lang.org/page/Building+with+Visual+Studio+2017
        tcl_lib_path = os.path.join(self.dependencies["tcl"].package_folder, "lib")
        tclimplib, tclstublib = None, None
        for lib in os.listdir(tcl_lib_path):
            if not lib.endswith(".lib"):
                continue
            if lib.startswith("tcl{}".format("".join(self.version.split(".")[:2]))):
                tclimplib = os.path.join(tcl_lib_path, lib)
            elif lib.startswith("tclstub{}".format("".join(self.version.split(".")[:2]))):
                tclstublib = os.path.join(tcl_lib_path, lib)

        if tclimplib is None or tclstublib is None:
            raise ConanException("tcl dependency misses tcl and/or tclstub library")
        with vcvars(self.settings):
            tcldir = self.dependencies["tcl"].package_folder.replace("/", "\\\\")
            self.run(
                """nmake -nologo -f "{cfgdir}/makefile.vc" INSTALLDIR="{pkgdir}" OPTS={opts} TCLDIR="{tcldir}" TCL_LIBRARY="{tcl_library}" TCLIMPLIB="{tclimplib}" TCLSTUBLIB="{tclstublib}" {target}""".format(
                    cfgdir=self._get_configure_folder("win"),
                    pkgdir=self.package_folder,
                    opts=",".join(opts),
                    tcldir=tcldir,
                    tclstublib=tclstublib,
                    tclimplib=tclimplib,
                    tcl_library=self.dependencies["tcl"].buildenv_info.TCL_LIBRARY.replace("\\", "/"),
                    target=target,
                ),
                cwd=self._get_configure_folder("win"),
            )

    def generate(self):
        tc = AutotoolsToolchain(self)
        tcl_root = self.dependencies["tcl"].package_folder
        tc.make_args = ["TCL_GENERIC_DIR={}".format(os.path.join(tcl_root, "include")).replace("\\", "/")]

        tclConfigShFolder = os.path.join(tcl_root, "lib").replace("\\", "/")

        yes_no = lambda v: "yes" if v else "no"
        tc.configure_args = [
            "--with-tcl={}".format(unix_path(self, tclConfigShFolder)),
            "--enable-threads",
            "--enable-symbols={}".format(yes_no(self.settings.build_type == "Debug")),
            "--enable-64bit={}".format(yes_no(self.settings.arch == "x86_64")),
            "--with-x={}".format(yes_no(self.settings.os == "Linux")),
            "--enable-aqua={}".format(yes_no(is_apple_os(self.settings.os))),
        ]

        if self.settings.os == "Windows":
            tc.defines.extend(["UNICODE", "_UNICODE", "_ATL_XP_TARGETING"])
        tc.generate()

    def build(self):
        self._patch_sources()

        if is_msvc(self):
            self._build_nmake()
        else:
            autotools = Autotools(self)
            autotools.configure()
            autotools.make()

    def package(self):
        copy(
            self,
            pattern="license.terms",
            src=self.source_folder,
            dst=os.path.join(self.package_folder, "licenses"),
        )
        if is_msvc(self):
            self._build_nmake("install")
        else:
            with chdir(self, self.build_folder):
                autotools = Autotools(self)
                autotools.install()
                autotools.make(target="install-private-headers")
                rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))
        rmdir(self, os.path.join(self.package_folder, "man"))
        rmdir(self, os.path.join(self.package_folder, "share"))

        # FIXME: move to patch
        tkConfigShPath = os.path.join(self.package_folder, "lib", "tkConfig.sh")
        if os.path.exists(tkConfigShPath):
            pkg_path = os.path.join(self.package_folder).replace("\\", "/")
            replace_in_file(self, tkConfigShPath, pkg_path, "${TK_ROOT}")
            replace_in_file(self, tkConfigShPath, "\nTK_BUILD_", "\n#TK_BUILD_")
            replace_in_file(self, tkConfigShPath, "\nTK_SRC_DIR", "\n#TK_SRC_DIR")

    def package_info(self):
        if is_msvc(self):
            tk_version = Version(self.version)
            lib_infix = f"{tk_version.major}{tk_version.minor}"
            tk_suffix = "t{}{}{}".format(
                "" if self.options.shared else "s",
                "g" if self.settings.build_type == "Debug" else "",
                "x" if "MD" in str(self.settings.compiler.runtime) and not self.options.shared else "",
            )
        else:
            tk_version = Version(self.version)
            lib_infix = f"{tk_version.major}.{tk_version.minor}"
            tk_suffix = ""
        self.cpp_info.libs = ["tk{}{}".format(lib_infix, tk_suffix), "tkstub{}".format(lib_infix)]
        if self.settings.os == "Macos":
            self.cpp_info.frameworks = ["CoreFoundation", "Cocoa", "Carbon", "IOKit"]
        elif self.settings.os == "Windows":
            self.cpp_info.system_libs = [
                "netapi32",
                "kernel32",
                "user32",
                "advapi32",
                "userenv",
                "ws2_32",
                "gdi32",
                "comdlg32",
                "imm32",
                "comctl32",
                "shell32",
                "uuid",
                "ole32",
                "oleaut32",
            ]

        tk_library = os.path.join(
            self.package_folder, "lib", "{}{}".format(self.name, ".".join(self.version.split(".")[:2]))
        ).replace("\\", "/")
        self.output.info("Setting TK_LIBRARY environment variable: {}".format(tk_library))
        self.env_info.TK_LIBRARY = tk_library

        tcl_root = self.package_folder.replace("\\", "/")
        self.output.info("Setting TCL_ROOT environment variable: {}".format(tcl_root))
        self.env_info.TCL_ROOT = tcl_root
