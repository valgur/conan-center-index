import os
from pathlib import Path

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.apple import XCRun
from conan.tools.build import cross_building
from conan.tools.files import *
from conan.tools.gnu import Autotools, AutotoolsToolchain
from conan.tools.layout import basic_layout
from conan.tools.microsoft import is_msvc
from conan.tools.scm import Version

required_conan_version = ">=2.1"


class GccConan(ConanFile):
    name = "gcc"
    description = (
        "The GNU Compiler Collection includes front ends for C, "
        "C++, Objective-C, Fortran, Ada, Go, and D, as well as "
        "libraries for these languages (libstdc++,...). "
    )
    topics = ("gcc", "gnu", "compiler", "c", "c++")
    homepage = "https://gcc.gnu.org"
    url = "https://github.com/conan-io/conan-center-index"
    license = "GPL-3.0-only"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "i18n": [True, False],
    }
    default_options = {
        "i18n": False,
    }

    def configure(self):
        if self.settings.compiler in ["clang", "apple-clang"]:
            # Can't remove this from cxxflags with autotools - so get rid of it
            del self.settings.compiler.libcxx
        # https://github.com/gcc-mirror/gcc/blob/6b5248d15c6d10325c6cbb92a0e0a9eb04e3f122/libcody/configure#L2505C11-L2505C25
        del self.settings.compiler.cppstd

    def package_id(self):
        del self.info.settings.compiler
        del self.info.settings.build_type

    def layout(self):
        basic_layout(self, src_folder="src")

    def requirements(self):
        self.requires("mpc/[^1.2.0]")
        self.requires("mpfr/[^4.2.0]")
        self.requires("gmp/[^6.3.0]")
        self.requires("zlib-ng/[^2.0]")
        self.requires("isl/0.27")

    def validate(self):
        if self.settings.os == "Windows":
            raise ConanInvalidConfiguration("Windows builds are not currently supported. Contributions are welcome.")
        if cross_building(self):
            raise ConanInvalidConfiguration("Cross builds are not currently supported. Contributions are welcome")

    def build_requirements(self):
        if self.settings.os == "Linux":
            # binutils recipe is broken for Macos, and Windows uses tools
            # distributed with msys/mingw
            self.tool_requires("binutils/[^2.42]")
        self.tool_requires("flex/[^2.6.4]")
        if self.options.i18n:
            self.tool_requires("gettext/[>=0.21 <1]", options={"tools": True})

    def validate_build(self):
        if is_msvc(self):
            raise ConanInvalidConfiguration("GCC can't be built with MSVC")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = AutotoolsToolchain(self)
        tc.configure_args.append("--enable-languages=c,c++,fortran")
        tc.configure_args.append("--enable-nls" if self.options.i18n else "--disable-nls")
        tc.configure_args.append("--disable-multilib")
        tc.configure_args.append("--disable-bootstrap")
        tc.configure_args.append(f"--with-zlib={self.dependencies['zlib-ng'].package_folder}")
        tc.configure_args.append(f"--with-isl={self.dependencies['isl'].package_folder}")
        tc.configure_args.append(f"--with-gmp={self.dependencies['gmp'].package_folder}")
        tc.configure_args.append(f"--with-mpc={self.dependencies['mpc'].package_folder}")
        tc.configure_args.append(f"--with-mpfr={self.dependencies['mpfr'].package_folder}")
        tc.configure_args.append(f"--program-suffix=-{self.version}")

        if self.settings.os == "Macos":
            xcrun = XCRun(self)
            tc.configure_args.append(f"--with-sysroot={xcrun.sdk_path}")
            # Set native system header dir to ${{sysroot}}/usr/include to
            # isolate installation from the system as much as possible
            tc.configure_args.append("--with-native-system-header-dir=/usr/include")
            tc.make_args.append("BOOT_LDFLAGS=-Wl,-headerpad_max_install_names")
        tc.generate()

        # Don't use AutotoolsDeps here - deps are passed directly in configure_args.
        # Using AutotoolsDeps causes the compiler tests to fail by erroneously adding
        # additional $LIBS to the test compilation

    def build(self):
        autotools = Autotools(self)
        autotools.configure()
        autotools.make()

    def package(self):
        autotools = Autotools(self)
        autotools.install(target="install-strip")
        rmdir(self, os.path.join(self.package_folder, "share", "info"))
        rmdir(self, os.path.join(self.package_folder, "share", "man"))
        rm(self, "*.la", self.package_folder, recursive=True)
        copy(self, "COPYING*", self.source_folder, os.path.join(self.package_folder, "licenses"), keep_path=False)

        # Add major version symlinks for all executables
        major = Version(self.version).major
        suffix = ".exe" if self.settings.os == "Windows" else ""
        for exe_path in Path(self.package_folder, "bin").glob(f"*-{self.version}{suffix}"):
            symlink_path = exe_path.with_name(exe_path.name.replace(f"-{self.version}{suffix}", f"-{major}{suffix}"))
            os.symlink(exe_path.name, symlink_path)

    def package_info(self):
        def _tool_path(tool_name):
            suffix = ".exe" if self.settings.os == "Windows" else ""
            return os.path.join(self.package_folder, "bin", f"{tool_name}-{self.version}{suffix}")

        def _add_env_var(var, tool_name):
            self.buildenv_info.define_path(var, _tool_path(tool_name))

        _add_env_var("CC", "gcc")
        _add_env_var("CXX", "g++")
        _add_env_var("CPP", "cpp")
        _add_env_var("CXXCPP", "cpp")
        _add_env_var("FC", "gfortran")
        _add_env_var("AS", "as")

        _add_env_var("ADDR2LINE", "addr2line")
        _add_env_var("AR", "ar")
        _add_env_var("DWP", "dwp")
        _add_env_var("GDB", "gdb")
        _add_env_var("GPROF", "gprof")
        _add_env_var("LD", "ld")
        _add_env_var("NM", "nm")
        _add_env_var("OBJCOPY", "objcopy")
        _add_env_var("OBJDUMP", "objdump")
        _add_env_var("RANLIB", "ranlib")
        _add_env_var("READLINK", "readlink")
        _add_env_var("SIZE", "size")
        _add_env_var("STRINGS", "strings")
        _add_env_var("STRIP", "strip")

        self.conf_info.update("tools.build:compiler_executables", {
            "c": _tool_path("gcc"),
            "cpp": _tool_path("g++"),
            "fortran": _tool_path("gfortran"),
            "asm": _tool_path("as"),
            "ar": _tool_path("ar"),
            "ld": _tool_path("ld"),
            "nm": _tool_path("nm"),
            "objcopy": _tool_path("objcopy"),
            "objdump": _tool_path("objdump"),
            "ranlib": _tool_path("ranlib"),
            "strip": _tool_path("strip"),
        })
