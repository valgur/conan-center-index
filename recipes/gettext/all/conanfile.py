import os
import shutil
from pathlib import Path

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.apple import is_apple_os
from conan.tools.build import cross_building
from conan.tools.env import VirtualRunEnv
from conan.tools.files import *
from conan.tools.gnu import Autotools, AutotoolsDeps, AutotoolsToolchain
from conan.tools.layout import basic_layout
from conan.tools.microsoft import is_msvc, unix_path

required_conan_version = ">=2.4"


class GettextConan(ConanFile):
    name = "gettext"
    description = "An internationalization and localization system for multilingual programs"
    topics = ("intl", "libintl", "i18n")
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://www.gnu.org/software/gettext"
    # The libintl library is LGPL, while the tools are GPL.
    # Marking the package as LGPL overall, since the tools won't be linked against.
    # https://www.gnu.org/software/gettext/manual/gettext.html#Licenses
    license = "LGPL-2.1-or-later"

    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "libintl": [True, False],
        "tools": [True, False],
        "threads": ["posix", "solaris", "pth", "windows", "disabled"],
        "with_openmp": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "with_openmp": True,
        # Handle default values for `threads`, `libintl` and `tools` in `config_options` method
    }
    languages = ["C"]

    @property
    def _is_clang_cl(self):
        return self.settings.os == "Windows" and self.settings.compiler == "clang" and \
               self.settings.compiler.get_safe("runtime")

    def export_sources(self):
        export_conandata_patches(self)

    def config_options(self):
        if self.settings.os == "Windows":
            self.options.rm_safe("fPIC")
        self.options.threads = {"Solaris": "solaris", "Windows": "windows"}.get(str(self.settings.os), "posix")
        # Build only the library when building for host context and vice versa.
        # This will cause the package to be built twice if both are used,
        # but it's still better than always building the tools, which is significantly slower.
        is_build_context = self.settings_target is not None
        self.options.libintl = True
        self.options.tools = is_build_context

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")

    def layout(self):
        basic_layout(self, src_folder="src")

    def requirements(self):
        self.requires("libiconv/1.17")
        if self.options.with_openmp:
            self.requires("openmp/system")

    def validate(self):
        if not self.options.libintl and not self.options.tools:
            raise ConanInvalidConfiguration("At least one of 'libintl' or 'tools' options must be enabled")

    def package_id(self):
        # Building only tools
        if not self.info.options.libintl:
            del self.info.settings.compiler

    def build_requirements(self):
        if self.settings_build.os == "Windows":
            self.win_bash = True
            if not self.conf.get("tools.microsoft.bash:path", default=False, check_type=str):
                self.tool_requires("msys2/cci.latest")
        if is_msvc(self) or self._is_clang_cl:
            self.tool_requires("automake/1.16.5")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        apply_conandata_patches(self)

    def generate(self):
        if not cross_building(self):
            VirtualRunEnv(self).generate(scope="build")

        tc = AutotoolsToolchain(self)
        libiconv_root = unix_path(self, self.dependencies["libiconv"].package_folder)
        tc.configure_args += [
            "HELP2MAN=/bin/true",
            "EMACS=no",
            "--disable-nls",
            "--disable-dependency-tracking",
            "--enable-relocatable",
            "--disable-c++",
            "--disable-java",
            "--disable-csharp",
            "--disable-libasprintf",
            "--disable-curses",
            "--disable-rpath",
            "--enable-openmp" if self.options.with_openmp else "--disable-openmp",
            f"--enable-threads={self.options.threads}" if self.options.threads != "disabled" else "--disable-threads",
            f"--with-libiconv-prefix={libiconv_root}",
        ]

        env = tc.environment()
        if is_msvc(self) or self._is_clang_cl:
            target = None
            if self.settings.arch == "x86_64":
                target = "x86_64-w64-mingw32"
            elif self.settings.arch == "x86":
                target = "i686-w64-mingw32"

            if target is not None:
                tc.configure_args += [f"--host={target}", f"--build={target}"]

            # prevent redefining compiler instrinsic functions
            tc.configure_args.extend([
                'ac_cv_func_memmove=yes',
                'ac_cv_func_memset=yes'
            ])

            if self.settings.build_type == "Debug":
                # Skip checking for the 'n' printf format directly
                # in msvc, as it is known to not be available due to security concerns.
                # Skipping it avoids a GUI prompt during ./configure for a debug build
                # See https://github.com/conan-io/conan-center-index/issues/23698
                tc.configure_args.append('gl_cv_func_printf_directive_n=no')

            def programs():
                rc = None
                if self.settings.arch == "x86_64":
                    rc = "windres --target=pe-x86-64"
                elif self.settings.arch == "x86":
                    rc = "windres --target=pe-i386"
                if self._is_clang_cl:
                    return os.environ.get("CC", "clang-cl"), os.environ.get("AR", "llvm-lib"), os.environ.get("LD", "lld-link"), rc
                if is_msvc(self):
                    return "cl -nologo", "lib", "link", rc

            cc, ar, link, rc = programs()

            compile_wrapper = unix_path(self, self.conf.get("user.automake:compile-wrapper", check_type=str))
            ar_wrapper = unix_path(self, self.conf.get("user.automake:lib-wrapper", check_type=str))
            env.define("CC", f"{compile_wrapper} {cc}")
            env.define("CXX", f"{compile_wrapper} {cc}")
            env.define("LD", link)
            env.define("AR", f"{ar_wrapper} {ar}")
            env.define("NM", "dumpbin -symbols")
            env.define("RANLIB", ":")
            env.define("STRIP", ":")
            if rc is not None:
                env.define("RC", rc)
                env.define("WINDRES", rc)

            # The flag above `--with-libiconv-prefix` fails to correctly detect libiconv on windows+msvc
            # so it needs an extra nudge. We could use `AutotoolsDeps` but it's currently affected by the
            # following outstanding issue: https://github.com/conan-io/conan/issues/12784
            libiconv_info = self.dependencies["libiconv"].cpp_info.aggregated_components()
            iconv_includedir = unix_path(self, libiconv_info.includedir)
            iconv_libdir = unix_path(self, libiconv_info.libdir)
            tc.extra_cflags.append(f"-I{iconv_includedir}")
            tc.extra_ldflags.append(f"-L{iconv_libdir}")
            # One of the checks performed by the configure script requires this as a preprocessor flag
            # rather than a C compiler flag
            env.prepend("CPPFLAGS", f"-I{iconv_includedir}")
        tc.generate(env)

        if not is_msvc(self) and not self._is_clang_cl:
            deps = AutotoolsDeps(self)
            deps.generate()

    def build(self):
        autotools = Autotools(self)
        if not self.options.tools:
            autotools.configure(build_script_folder="gettext-runtime")
            autotools.make(args=["-C", "intl"])
        else:
            autotools.configure()
            autotools.make()

    def package(self):
        copy(self, "COPYING", self.source_folder, os.path.join(self.package_folder, "licenses"))
        autotools = Autotools(self)
        autotools.install()

        if self.options.libintl:
            dest_lib_dir = os.path.join(self.package_folder, "lib")
            dest_runtime_dir = os.path.join(self.package_folder, "bin")
            dest_include_dir = os.path.join(self.package_folder, "include")
            copy(self, "*gnuintl*.dll", self.build_folder, dest_runtime_dir, keep_path=False)
            copy(self, "*gnuintl*.lib", self.build_folder, dest_lib_dir, keep_path=False)
            copy(self, "*gnuintl*.a", self.build_folder, dest_lib_dir, keep_path=False)
            copy(self, "*gnuintl*.so*", self.build_folder, dest_lib_dir, keep_path=False)
            copy(self, "*gnuintl*.dylib", self.build_folder, dest_lib_dir, keep_path=False)
            copy(self, "*libgnuintl.h", self.build_folder, dest_include_dir, keep_path=False)
            shutil.copy(os.path.join(dest_include_dir, "libgnuintl.h"),
                        os.path.join(dest_include_dir, "libintl.h"))

        rmdir(self, os.path.join(self.package_folder, "share", "doc"))
        rmdir(self, os.path.join(self.package_folder, "share", "info"))
        rmdir(self, os.path.join(self.package_folder, "share", "man"))
        fix_msvc_libname(self)

    def package_info(self):
        if self.options.libintl:
            self.cpp_info.set_property("cmake_find_mode", "both")
            self.cpp_info.set_property("cmake_file_name", "Intl")
            self.cpp_info.set_property("cmake_target_name", "Intl::Intl")
            self.cpp_info.libs = ["gnuintl"]
            if is_apple_os(self):
                self.cpp_info.frameworks.append("CoreFoundation")
        else:
            self.cpp_info.includedirs = []
            self.cpp_info.libdirs = []

        if self.options.tools:
            aclocal = os.path.join(self.package_folder, "share", "aclocal")
            autopoint = os.path.join(self.package_folder, "bin", "autopoint")
            self.buildenv_info.append_path("ACLOCAL_PATH", aclocal)
            self.buildenv_info.define_path("AUTOPOINT", autopoint)


def fix_msvc_libname(conanfile, remove_lib_prefix=True):
    """remove lib prefix & change extension to .lib in case of cl-like compiler"""
    if not conanfile.settings.get_safe("compiler.runtime"):
        return
    libdirs = getattr(conanfile.cpp.package, "libdirs")
    for libdir in libdirs:
        folder = Path(conanfile.package_folder, libdir)
        for ext in [".dll.a", ".dll.lib", ".a"]:
            for path in folder.glob(f"*{ext}"):
                libname = path.name[:-len(ext)]
                if remove_lib_prefix and libname.startswith("lib"):
                    libname = libname[3:]
                rename(conanfile, path, folder / f"{libname}.lib")
