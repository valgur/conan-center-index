import fnmatch
import os
import re
import textwrap

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration, ConanException
from conan.tools.apple import is_apple_os, fix_apple_shared_install_name
from conan.tools.build import can_run
from conan.tools.env import VirtualRunEnv
from conan.tools.files import *
from conan.tools.gnu import Autotools, AutotoolsToolchain, AutotoolsDeps, PkgConfigDeps
from conan.tools.layout import basic_layout
from conan.tools.microsoft import *
from conan.tools.scm import Version

required_conan_version = ">=2.4"


class CPythonConan(ConanFile):
    name = "cpython"
    description = "Python is a programming language that lets you work quickly and integrate systems more effectively."
    license = "Python-2.0"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://www.python.org"
    topics = ("python", "cpython", "language", "script")

    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "optimizations": [True, False],
        "lto": [True, False],
        "docstrings": [True, False],
        "pymalloc": [True, False],
        "with_bz2": [True, False],
        "with_curses": [True, False],
        "with_gdbm": [True, False],
        "with_lzma": [True, False],
        "with_sqlite3": [True, False],
        "with_tkinter": [True, False],
        "with_zstd": [True, False],

        # options that don't change package id
        "env_vars": [True, False],  # set environment variables
    }
    default_options = {
        "shared": True,
        "fPIC": True,
        "optimizations": False,
        "lto": False,
        "docstrings": True,
        "pymalloc": True,
        "with_bz2": True,
        "with_curses": True,
        "with_gdbm": True,
        "with_lzma": True,
        "with_sqlite3": True,
        "with_tkinter": True,
        "with_zstd": True,

        # options that don't change package id
        "env_vars": True,
    }
    languages = ["C"]

    @property
    def _supports_modules(self):
        return self.options.shared or not is_msvc(self)

    @property
    def _version_suffix(self):
        v = Version(self.version)
        joiner = "" if is_msvc(self) else "."
        return f"{v.major}{joiner}{v.minor}"

    def export_sources(self):
        export_conandata_patches(self)

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC
        if is_msvc(self):
            del self.options.lto
            del self.options.docstrings
            del self.options.pymalloc
            del self.options.with_curses
            del self.options.with_gdbm
        if Version(self.version) <= "3.13":
            del self.options.with_zstd

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")
        if not self._supports_modules:
            self.options.rm_safe("with_bz2")
            self.options.rm_safe("with_sqlite3")
            self.options.rm_safe("with_tkinter")
            self.options.rm_safe("with_lzma")
            self.options.rm_safe("with_zstd")

    def layout(self):
        basic_layout(self, src_folder="src")

    def build_requirements(self):
        if Version(self.version) >= "3.11" and not is_msvc(self) and not self.conf.get("tools.gnu:pkg_config", check_type=str):
            self.tool_requires("pkgconf/[>=2.2 <3]")
        if not can_run(self) and not is_msvc(self):
            self.tool_requires(f"cpython/{self.version}")

    def requirements(self):
        self.requires("zlib-ng/[^2.0]")
        if self._supports_modules:
            # We only actually need this limitation when openssl is shared, but otherwise we get errors when trying to use openssl.
            # For some extra context, openssl was only updated to 3.0 in cpython 3.11.5
            openssl_upper_bound = 3 if is_msvc(self) and Version(self.version) < "3.12" else 4
            self.requires(f"openssl/[>=1.1 <{openssl_upper_bound}]")
            self.requires("expat/[>=2.6.2 <3]")
            self.requires("libffi/[^3.4.4]")
            if Version(self.version) < "3.10" or is_apple_os(self):
                # FIXME: mpdecimal > 2.5.0 on MacOS causes the _decimal module to not be importable
                self.requires("mpdecimal/2.5.0")
            elif Version(self.version) < "3.13":
                self.requires("mpdecimal/2.5.1")
            else:
                self.requires("mpdecimal/[^4.0.0]")
        if self.settings.os != "Windows":
            if not is_apple_os(self):
                self.requires("util-linux-libuuid/2.41")
            if Version(self.version) < "3.13":
                self.requires("libxcrypt/4.4.36")
        if self.options.get_safe("with_bz2"):
            self.requires("bzip2/[^1.0.8]")
        if self.options.get_safe("with_gdbm", False):
            self.requires("gdbm/1.23")
        if self.options.get_safe("with_sqlite3"):
            self.requires("sqlite3/[>=3.45.0 <4]")
        if self.options.get_safe("with_tkinter"):
            self.requires("tk/8.6.16")
        if self.options.get_safe("with_curses", False):
            # Used in a public header
            # https://github.com/python/cpython/blob/v3.10.13/Include/py_curses.h#L34
            self.requires("ncurses/[^6.4]", transitive_headers=True, transitive_libs=True)
        if self.options.get_safe("with_lzma", False):
            self.requires("xz_utils/[^5.4.5]")
        if self.options.get_safe("with_zstd", False):
            self.requires("zstd/[~1.5]")

    def package_id(self):
        del self.info.options.env_vars

    def validate(self):
        if is_msvc(self):
            if str(self.settings.arch) not in self._msvc_archs:
                raise ConanInvalidConfiguration("Visual Studio does not support this architecture")
            if self.options.shared and is_msvc_static_runtime(self):
                raise ConanInvalidConfiguration("MT(d) runtime is not supported when building a shared cpython library")
            if self.options.optimizations:
                raise ConanInvalidConfiguration("This recipe does not support optimized MSVC cpython builds (yet)")
                # FIXME: should probably throw when cross building
                # FIXME: optimizations for Visual Studio, before building the final `build_type`:
                # 1. build the MSVC PGInstrument build_type,
                # 2. run the instrumented binaries, (PGInstrument should have created a `python.bat` file in the PCbuild folder)
                # 3. build the MSVC PGUpdate build_type
            if self.settings.build_type == "Debug" and "d" not in msvc_runtime_flag(self):
                raise ConanInvalidConfiguration(
                    "Building debug cpython requires a debug runtime (Debug cpython requires _CrtReportMode"
                    " symbol, which only debug runtimes define)"
                )
            if not self.options.shared and Version(self.version) >= "3.10":
                # Static CPython on Windows is only loosely supported, see https://github.com/python/cpython/issues/110234
                # 3.10 fails during the test, 3.11 fails during the build (missing symbol that seems to be DLL specific: PyWin_DLLhModule)
                raise ConanInvalidConfiguration("Static msvc build disabled (>=3.10) due to \"AttributeError: module 'sys' has no attribute 'winver'\"")

        if self.options.get_safe("with_curses", False) and not self.dependencies["ncurses"].options.with_widec:
            raise ConanInvalidConfiguration("cpython requires ncurses with wide character support")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        apply_conandata_patches(self)

    def _generate_autotools(self):
        tc = AutotoolsToolchain(self, prefix=self.package_folder)
        # Not necessary, just cleans up the output
        tc.update_configure_args({"--enable-static": None, "--disable-static": None})
        yes_no = lambda v: "yes" if v else "no"
        tc.configure_args += [
            f"--with-doc-strings={yes_no(self.options.docstrings)}",
            f"--with-pymalloc={yes_no(self.options.pymalloc)}",
            "--with-system-expat",
            f"--enable-optimizations={yes_no(self.options.optimizations)}",
            f"--with-lto={yes_no(self.options.lto)}",
            f"--with-pydebug={yes_no(self.settings.build_type == 'Debug')}",
            "--with-system-libmpdec",
            f"--with-openssl={self.dependencies['openssl'].package_folder}",
        ]
        if Version(self.version) < "3.12":
            tc.configure_args.append("--with-system-ffi")
        if Version(self.version) >= "3.10":
            tc.configure_args.append("--disable-test-modules")
        if self.options.get_safe("with_sqlite3"):
            sqlite3_has_extensions = not self.dependencies["sqlite3"].options.omit_load_extension
            tc.configure_args.append(f"--enable-loadable-sqlite-extensions={yes_no(sqlite3_has_extensions)}")
        if self.options.with_tkinter and Version(self.version) < "3.11":
            tcltk_includes = []
            tcltk_libs = []
            # FIXME: collect using some conan util (https://github.com/conan-io/conan/issues/7656)
            for dep in ("tcl", "tk", "zlib"):
                cpp_info = self.dependencies[dep].cpp_info.aggregated_components()
                tcltk_includes += [f"-I{d}" for d in cpp_info.includedirs]
                tcltk_libs += [f"-L{lib}" for lib in cpp_info.libdirs]
                tcltk_libs += [f"-l{lib}" for lib in cpp_info.libs]
            if self.settings.os in ["Linux", "FreeBSD"] and not self.dependencies["tk"].options.shared:
                # FIXME: use info from xorg.components (x11, xscrnsaver)
                tcltk_libs.extend([f"-l{lib}" for lib in ("X11", "Xss")])
            tc.configure_args += [
                f"--with-tcltk-includes={' '.join(tcltk_includes)}",
                f"--with-tcltk-libs={' '.join(tcltk_libs)}",
            ]
        if not is_apple_os(self):
            tc.extra_ldflags.append('-Wl,--as-needed')

        if self.settings.os in ["Linux", "FreeBSD"]:
            # Add -lrt to fix _posixshmem.cpython-312-x86_64-linux-gnu.so: undefined symbol: shm_unlink
            tc.configure_args.append("POSIXSHMEM_LIBS=-lrt")

        if not can_run(self):
            build_python = unix_path(self, os.path.join(self.dependencies.build["cpython"].package_folder, "bin", "python"))
            tc.configure_args.append(f"--with-build-python={build_python}")
        # The following are required only when cross-building, but set for all cases for consistency
        tc.configure_args.append("--enable-ipv6")  # enabled by default, but skip the check
        dev_ptmx_exists = os.path.exists("/dev/ptmx")
        dev_ptc_exists = os.path.exists("/dev/ptc")
        tc.configure_args.append(f"ac_cv_file__dev_ptmx={yes_no(dev_ptmx_exists)}")
        tc.configure_args.append(f"ac_cv_file__dev_ptc={yes_no(dev_ptc_exists)}")

        tc.generate()

        deps = AutotoolsDeps(self)
        deps.generate()
        if Version(self.version) >= "3.11":
            pkgdeps = PkgConfigDeps(self)
            pkgdeps.generate()

    def generate(self):
        VirtualRunEnv(self).generate(scope="build")

        if is_msvc(self):
            # The msbuild generator only works with Visual Studio
            deps = MSBuildDeps(self)
            deps.generate()
            # The toolchain.props is not injected yet, but it also generates VCVars
            toolchain = MSBuildToolchain(self)
            toolchain.properties["IncludeExternals"] = "true"
            toolchain.generate()
        else:
            self._generate_autotools()

    def _patch_setup_py(self):
        setup_py = os.path.join(self.source_folder, "setup.py")
        if Version(self.version) < "3.10":
            replace_in_file(self, setup_py, ":libmpdec.so.2", "mpdec")

        if self.options.get_safe("with_curses"):
            libcurses = self.dependencies["ncurses"].cpp_info.components["libcurses"]
            tinfo = self.dependencies["ncurses"].cpp_info.components["tinfo"]
            libs = libcurses.libs + libcurses.system_libs + tinfo.libs + tinfo.system_libs
            replace_in_file(self, setup_py,
                            "curses_libs = ",
                            f"curses_libs = {repr(libs)} #")
        else:
            replace_in_file(self, setup_py,
                            "curses_libs = ",
                            "curses_libs = [] #")

        if self._supports_modules:
            openssl = self.dependencies["openssl"].cpp_info.aggregated_components()
            zlib = self.dependencies["zlib-ng"].cpp_info.aggregated_components()
            if Version(self.version) < "3.11":
                replace_in_file(self, setup_py,
                                "openssl_includes = ",
                                f"openssl_includes = {openssl.includedirs + zlib.includedirs} #")
                replace_in_file(self, setup_py,
                                "openssl_libdirs = ",
                                f"openssl_libdirs = {openssl.libdirs + zlib.libdirs} #")
                replace_in_file(self, setup_py,
                                "openssl_libs = ",
                                f"openssl_libs = {openssl.libs + zlib.libs} #")

            if Version(self.version) < "3.11":
                replace_in_file(self, setup_py, "if (MACOS and self.detect_tkinter_darwin())", "if (False)")

    def replace_in_vcxproj(self, path, search, replace, strict=True):
        return replace_in_file(self, f"{path}.vcxproj", search, replace, strict=strict)

    def _inject_conan_props_file(self, path, dep_name, condition=True):
        if condition:
            search = '<Import Project="python.props" />'
            inject = f'<Import Project="{self.generators_folder}/conan_{dep_name}.props" />'
            self.replace_in_vcxproj(path, search, search + inject)

    def _disable_vcxproj_element(self, path, elem_pattern):
        if "Condition" in elem_pattern:
            disabled_element, n = re.subn('Condition=".+?"', 'Condition="False"', elem_pattern)
            assert n == 1
        else:
            disabled_element = elem_pattern.replace('>', ' Condition="False">')
        self.replace_in_vcxproj(path, elem_pattern, disabled_element)

    def _remove_vcxproj_include_dir(self, path, include_pattern):
        self.replace_in_vcxproj(path,
                                f"<AdditionalIncludeDirectories>{include_pattern}",
                                "</AdditionalIncludeDirectories>")

    def _remove_vcxproj_dependency(self, path, dir_pattern):
        self.replace_in_vcxproj(path,
                                f"<AdditionalDependencies>{dir_pattern}",
                                "</AdditionalDependencies>")

    def _inject_vcxproj_element(self, path, elem_pattern, inject, prepend=False):
        self.replace_in_vcxproj(path, elem_pattern, inject + elem_pattern if prepend else elem_pattern + inject)

    def _regex_replace_in_file(self, filename, pattern, replacement, strict = True) -> None:
        content = load(self, filename)
        content, n = re.subn(pattern, replacement, content)
        if strict and n == 0:
            raise ConanException(f"Pattern '{pattern}' not found in '{filename}'")
        save(self, filename, content)

    def _remove_vcxproj_source_files(self, path, glob_pattern):
        glob_regex = fnmatch.translate(glob_pattern)
        pattern = f'<(CLCompile|ClInclude) .*?Include="{glob_regex}".*?/>'
        self._regex_replace_in_file(f"{path}.vcxproj", pattern, "")

    def _patch_msvc(self):
        runtime_library = {
            "MT": "MultiThreaded",
            "MTd": "MultiThreadedDebug",
            "MD": "MultiThreadedDLL",
            "MDd": "MultiThreadedDebugDLL",
        }[msvc_runtime_flag(self)]
        self.output.info("Patching runtime")
        replace_in_file(self, "pyproject.props", "MultiThreadedDLL", runtime_library)
        replace_in_file(self, "pyproject.props", "MultiThreadedDebugDLL", runtime_library)

        # Enable static MSVC cpython
        if not self.options.shared:
            self.replace_in_vcxproj("pythoncore", "DynamicLibrary", "StaticLibrary")
            self._inject_vcxproj_element("python", "<Link>", "<AdditionalDependencies>shlwapi.lib;ws2_32.lib;pathcch.lib;version.lib;%(AdditionalDependencies)</AdditionalDependencies>")
            self._inject_vcxproj_element("pythonw", "<Link>", "<AdditionalDependencies>shlwapi.lib;ws2_32.lib;pathcch.lib;version.lib;%(AdditionalDependencies)</AdditionalDependencies>")
            self.replace_in_vcxproj("pythoncore", "Py_ENABLE_SHARED", "Py_NO_ENABLE_SHARED")
            self._inject_vcxproj_element("pythoncore", "<PreprocessorDefinitions>", "Py_NO_BUILD_SHARED;")
            self._inject_vcxproj_element("python", "<PreprocessorDefinitions>", "Py_NO_ENABLE_SHARED;")
            self._inject_vcxproj_element("pythonw", "<ItemDefinitionGroup>", "<ClCompile><PreprocessorDefinitions>Py_NO_ENABLE_SHARED;%(PreprocessorDefinitions)</PreprocessorDefinitions></ClCompile>")

        # Disable "ValidateUcrtbase" target (TODO: Why?)
        self._disable_vcxproj_element("python", '<Target Name="ValidateUcrtbase" AfterTargets="AfterBuild" Condition="$(Configuration) != \'PGInstrument\' and $(Platform) != \'ARM\' and $(Platform) != \'ARM64\'">')

        if Version(self.version) < "3.11":
            # TODO: Why?
            self._disable_vcxproj_element("_freeze_importlib", '<Target Name="RebuildImportLib" AfterTargets="AfterBuild" Condition="$(Configuration) == \'Debug\' or $(Configuration) == \'Release\'"')

        # bz2
        self._remove_vcxproj_source_files("_bz2", "$(bz2Dir)*")

        # openssl
        if Version(self.version) < "3.12":
            self._remove_vcxproj_source_files("_ssl", r"$(opensslIncludeDir)\applink.c")

        # libffi
        if Version(self.version) < "3.11":
            # Don't add this define, it should be added conditionally by the libffi package
            # Instead, add this define to fix duplicate symbols (goes along with the ffi patches)
            # See https://github.com/python/cpython/commit/38f331d4656394ae0f425568e26790ace778e076#diff-6f6b7f83e2fb49775efdfa41b4aa4f8fadcf71f43c4f3bcf9f37743acafd3fdfR97
            self.replace_in_vcxproj("_ctypes", "FFI_BUILDING;", "USING_MALLOC_CLOSURE_DOT_C=1;")

        # mpdecimal
        # We need to remove all headers and all c files *except* the main module file, _decimal.c
        if Version(self.version) >= "3.13":
            self._remove_vcxproj_source_files("_decimal", r"..\Modules\_decimal\windows\*.h")
            self._remove_vcxproj_source_files("_decimal", r"$(mpdecimalDir)\libmpdec\*")
            self.replace_in_vcxproj("_decimal", r"..\Modules\_decimal\windows;$(mpdecimalDir)\libmpdec;", "")
        else:
            self._remove_vcxproj_source_files("_decimal", r"..\Modules\_decimal\*.h")
            self._remove_vcxproj_source_files("_decimal", r"..\Modules\_decimal\libmpdec\*.c")
            self.replace_in_vcxproj("_decimal", r"..\Modules\_decimal\libmpdec;", "")
        # There is also an assembly file with a complicated build step as part of the mpdecimal build
        self.replace_in_vcxproj("_decimal", "<CustomBuild", "<!--<CustomBuild")
        self.replace_in_vcxproj("_decimal", "</CustomBuild>", "</CustomBuild>-->")

        # sqlite3
        self._disable_vcxproj_element("_sqlite3", '<ProjectReference Include="sqlite3.vcxproj">')

        # lzma
        self._remove_vcxproj_dependency("_lzma", "$(OutDir)liblzma$(PyDebugExt).lib;")
        self._disable_vcxproj_element("_lzma", '<ProjectReference Include="liblzma.vcxproj">')

        # expat
        self._remove_vcxproj_include_dir("pyexpat", "$(PySourcePath)Modules\expat;")
        self._remove_vcxproj_include_dir("_elementtree", r"..\Modules\expat;")
        # Let Conan handle XML_STATIC
        self.replace_in_vcxproj("pyexpat", "XML_STATIC;", "")
        self.replace_in_vcxproj("_elementtree", "XML_STATIC;", "")
        self._remove_vcxproj_source_files("pyexpat", r"..\Modules\expat\*")
        self._remove_vcxproj_source_files("_elementtree", r"..\Modules\expat\*")

        # zlib
        if Version(self.version) <= "3.13":
            self._remove_vcxproj_source_files("pythoncore", r"$(zlibDir)\*")

        # tcl/tk
        self._remove_vcxproj_include_dir("_tkinter", "$(tcltkDir)include;")
        self._remove_vcxproj_dependency("_tkinter", "$(tcltkLib);")
        self._disable_vcxproj_element("_tkinter", '<PreprocessorDefinitions Condition="\'$(BuildForRelease)\' != \'true\'">Py_TCLTK_DIR')
        self._remove_vcxproj_source_files("_tkinter", r"$(tcltkdir)\*")

        # Inject Conan toolchain
        conantoolchain_props = os.path.join(self.generators_folder, MSBuildToolchain.filename)
        self._inject_vcxproj_element("pythoncore",
                                     '<Import Project="python.props" />',
                                     f'<Import Project="{conantoolchain_props}" />', prepend=True)

        # Don't import vendored libs
        self.replace_in_vcxproj("_ctypes", '<Import Project="libffi.props" />', "")
        self.replace_in_vcxproj("_hashlib", '<Import Project="openssl.props" />', "")
        self.replace_in_vcxproj("_ssl", '<Import Project="openssl.props" />', "")

        # Inject Conan deps
        self._inject_conan_props_file("_bz2", "bzip2", self.options.get_safe("with_bz2"))
        self._inject_conan_props_file("_elementtree", "expat", self._supports_modules)
        self._inject_conan_props_file("pyexpat", "expat", self._supports_modules)
        self._inject_conan_props_file("_hashlib", "openssl", self._supports_modules)
        self._inject_conan_props_file("_ssl", "openssl", self._supports_modules)
        self._inject_conan_props_file("_sqlite3", "sqlite3", self.options.get_safe("with_sqlite3"))
        self._inject_conan_props_file("_tkinter", "tk", self.options.get_safe("with_tkinter"))
        self._inject_conan_props_file("pythoncore", "zlib-ng")
        self._inject_conan_props_file("python", "zlib-ng")
        self._inject_conan_props_file("pythonw", "zlib-ng")
        self._inject_conan_props_file("_ctypes", "libffi", self._supports_modules)
        self._inject_conan_props_file("_decimal", "mpdecimal", self._supports_modules)
        self._inject_conan_props_file("_lzma", "xz_utils", self.options.get_safe("with_lzma"))
        self._inject_conan_props_file("_bsddb", "libdb", self.options.get_safe("with_bsddb"))

    def _patch_sources(self):
        # <=3.10 requires a lot of manual injection of dependencies through setup.py
        # 3.12 removes setup.py completely, and uses pkgconfig dependencies
        # 3.11 is an in awkward transition state where some dependencies use pkgconfig, and others use setup.py
        if Version(self.version) < "3.12":
            self._patch_setup_py()

        # Remove vendored packages
        rmdir(self, os.path.join(self.source_folder, "Modules", "_decimal", "libmpdec"))
        rmdir(self, os.path.join(self.source_folder, "Modules", "expat"))
        if Version(self.version) > "3.13":
            rmdir(self, os.path.join(self.source_folder, "Modules", "_zstd"))

        if Version(self.version) >= "3.11":
            replace_in_file(self, os.path.join(self.source_folder, "configure"),
                            'OPENSSL_LIBS="-lssl -lcrypto"',
                            'OPENSSL_LIBS="-lssl -lcrypto -lz"')

        if Version(self.version) < "3.12":
            replace_in_file(self, os.path.join(self.source_folder, "Makefile.pre.in"),
                            "$(RUNSHARED) CC='$(CC)' LDSHARED='$(BLDSHARED)' OPT='$(OPT)'",
                            "$(RUNSHARED) CC='$(CC) $(CONFIGURE_CFLAGS) $(CONFIGURE_CPPFLAGS)' LDSHARED='$(BLDSHARED)' OPT='$(OPT)'")

        if is_msvc(self):
            with chdir(self, os.path.join(self.source_folder, "PCBuild")):
                self._patch_msvc()

    @property
    def _solution_projects(self):
        if self.options.shared:
            solution_path = os.path.join(self.source_folder, "PCbuild", "pcbuild.sln")
            projects = set(re.findall('"([^"]+)\\.vcxproj"', open(solution_path).read()))

            def project_build(name):
                if os.path.basename(name) in self._msvc_discarded_projects:
                    return False
                if "test" in name:
                    return False
                return True

            projects = list(filter(project_build, projects))
            return projects
        else:
            return ["pythoncore", "python", "pythonw"]

    @property
    def _msvc_discarded_projects(self):
        discarded = {
            "python_uwp",
            "pythonw_uwp",
            "_freeze_importlib",
            "sqlite3",
            "bdist_wininst",
            "liblzma",
            "openssl",
            "xxlimited",
        }
        if not self.options.with_bz2:
            discarded.add("bz2")
        if not self.options.with_sqlite3:
            discarded.add("_sqlite3")
        if not self.options.with_tkinter:
            discarded.add("_tkinter")
        if not self.options.with_lzma:
            discarded.add("_lzma")
        return discarded

    @property
    def _msvc_archs(self):
        archs = {
            "x86": "Win32",
            "x86_64": "x64",
            "armv7": "ARM",
            "armv8_32": "ARM",
            "armv8": "ARM64",
        }
        return archs

    def _msvc_build(self):
        msbuild = MSBuild(self)
        msbuild.platform = self._msvc_archs[str(self.settings.arch)]

        projects = self._solution_projects
        self.output.info(f"Building {len(projects)} Visual Studio projects: {projects}")

        sln = os.path.join(self.source_folder, "PCbuild", "pcbuild.sln")
        # FIXME: Solution files do not pick up the toolset automatically.
        cmd = msbuild.command(sln, targets=projects)
        self.run(f"{cmd} /p:PlatformToolset={msvs_toolset(self)}")

    def build(self):
        self._patch_sources()
        if is_msvc(self):
            self._msvc_build()
        else:
            autotools = Autotools(self)
            autotools.configure()
            autotools.make()

    @property
    def _msvc_artifacts_path(self):
        build_subdir_lut = {
            "x86_64": "amd64",
            "x86": "win32",
            "armv7": "arm32",
            "armv8_32": "arm32",
            "armv8": "arm64",
        }
        return os.path.join(self.source_folder, "PCbuild", build_subdir_lut[str(self.settings.arch)])

    @property
    def _msvc_install_subprefix(self):
        return "bin"

    def _copy_essential_dlls(self):
        if is_msvc(self):
            # Until MSVC builds support cross building, copy dll's of essential (shared) dependencies to python binary location.
            # These dll's are required when running the layout tool using the newly built python executable.
            dest_path = os.path.join(self.build_folder, self._msvc_artifacts_path)
            for bin_path in self.dependencies["libffi"].cpp_info.bindirs:
                copy(self, "*.dll", src=bin_path, dst=dest_path)
            for bin_path in self.dependencies["expat"].cpp_info.bindirs:
                copy(self, "*.dll", src=bin_path, dst=dest_path)
            for bin_path in self.dependencies["zlib-ng"].cpp_info.bindirs:
                copy(self, "*.dll", src=bin_path, dst=dest_path)
            for bin_path in self.dependencies["openssl"].cpp_info.bindirs:
                copy(self, "*.dll", src=bin_path, dst=dest_path)

    def _msvc_package_layout(self):
        self._copy_essential_dlls()
        install_prefix = os.path.join(self.package_folder, self._msvc_install_subprefix)
        mkdir(self, install_prefix)
        build_path = self._msvc_artifacts_path
        infix = "_d" if self.settings.build_type == "Debug" else ""
        # FIXME: if cross building, use a build python executable here
        python_built = os.path.join(build_path, f"python{infix}.exe")
        layout_args = [
            os.path.join(self.source_folder, "PC", "layout", "main.py"),
            "-v",
            "-s", self.source_folder,
            "-b", build_path,
            "--copy", install_prefix,
            "-p",
            "--include-pip",
            "--include-venv",
            "--include-dev",
        ]
        if self.options.with_tkinter:
            layout_args.append("--include-tcltk")
        if self.settings.build_type == "Debug":
            layout_args.append("-d")
        python_args = " ".join(f'"{a}"' for a in layout_args)
        self.run(f"{python_built} {python_args}")

        rmdir(self, os.path.join(self.package_folder, "bin", "tcl"))

        rm(self, "LICENSE.txt", install_prefix)
        for file in os.listdir(os.path.join(install_prefix, "libs")):
            if not re.match("python.*", file):
                os.unlink(os.path.join(install_prefix, "libs", file))

    def _msvc_package_copy(self):
        build_path = self._msvc_artifacts_path
        infix = "_d" if self.settings.build_type == "Debug" else ""
        copy(self, "*.exe",
             src=build_path,
             dst=os.path.join(self.package_folder, self._msvc_install_subprefix))
        copy(self, "*.dll",
             src=build_path,
             dst=os.path.join(self.package_folder, self._msvc_install_subprefix))
        copy(self, "*.pyd",
             src=build_path,
             dst=os.path.join(self.package_folder, self._msvc_install_subprefix, "DLLs"))
        copy(self, f"python{self._version_suffix}{infix}.lib",
             src=build_path,
             dst=os.path.join(self.package_folder, self._msvc_install_subprefix, "libs"))
        copy(self, "*",
             src=os.path.join(self.source_folder, "Include"),
             dst=os.path.join(self.package_folder, self._msvc_install_subprefix, "include"))
        copy(self, "pyconfig.h",
             src=os.path.join(self.source_folder, "PC"),
             dst=os.path.join(self.package_folder, self._msvc_install_subprefix, "include"))
        copy(self, "*.py",
             src=os.path.join(self.source_folder, "lib"),
             dst=os.path.join(self.package_folder, self._msvc_install_subprefix, "Lib"))
        rmdir(self, os.path.join(self.package_folder, self._msvc_install_subprefix, "Lib", "test"))

        packages = {}
        get_name_version = lambda fn: fn.split(".", 2)[:2]
        whldir = os.path.join(self.source_folder, "Lib", "ensurepip", "_bundled")
        for fn in filter(lambda n: n.endswith(".whl"), os.listdir(whldir)):
            name, version = get_name_version(fn)
            add = True
            if name in packages:
                pname, pversion = get_name_version(packages[name])
                add = Version(version) > Version(pversion)
            if add:
                packages[name] = fn
        for fname in packages.values():
            unzip(self, filename=os.path.join(whldir, fname),
                  destination=os.path.join(self.package_folder, "bin", "Lib", "site-packages"))

        interpreter_path = os.path.join(build_path, self._cpython_interpreter_name)
        lib_dir_path = os.path.join(self.package_folder, self._msvc_install_subprefix, "Lib").replace("\\", "/")
        self.run(f"{interpreter_path} -c \"import compileall; compileall.compile_dir('{lib_dir_path}')\"")

    @property
    def _exact_lib_name(self):
        prefix = "" if self.settings.os == "Windows" else "lib"
        if self.settings.os == "Windows":
            extension = "lib"
        elif not self.options.shared:
            extension = "a"
        elif is_apple_os(self):
            extension = "dylib"
        else:
            extension = "so"
        return f"{prefix}{self._lib_name}.{extension}"

    @property
    def _cmake_module_path(self):
        if is_msvc(self):
            # On Windows, `lib` is for Python modules, `libs` is for compiled objects.
            # Usually CMake modules are packaged with the latter.
            return os.path.join(self._msvc_install_subprefix, "libs", "cmake")
        else:
            return os.path.join("lib", "cmake")

    def _write_cmake_findpython_wrapper_file(self):
        template = textwrap.dedent("""
        if (DEFINED Python3_VERSION_STRING)
            set(_CONAN_PYTHON_SUFFIX "3")
        else()
            set(_CONAN_PYTHON_SUFFIX "")
        endif()
        get_filename_component(_PREFIX_PATH "@PREFIX_PATH@" ABSOLUTE)
        # Allow Python_EXECUTABLE to be overridden for cross-compilation support
        if(NOT DEFINED Python_EXECUTABLE)
            set(Python${_CONAN_PYTHON_SUFFIX}_EXECUTABLE @PYTHON_EXECUTABLE@)
        endif()
        set(Python${_CONAN_PYTHON_SUFFIX}_LIBRARY @PYTHON_LIBRARY@)

        # Fails if these are set beforehand
        unset(Python${_CONAN_PYTHON_SUFFIX}_INCLUDE_DIRS)
        unset(Python${_CONAN_PYTHON_SUFFIX}_INCLUDE_DIR)

        include(${CMAKE_ROOT}/Modules/FindPython${_CONAN_PYTHON_SUFFIX}.cmake)

        # Sanity check: The former comes from FindPython(3), the latter comes from the injected find module
        if(NOT Python${_CONAN_PYTHON_SUFFIX}_VERSION VERSION_EQUAL Python${_CONAN_PYTHON_SUFFIX}_VERSION_STRING)
            message(FATAL_ERROR "CMake detected wrong cpython version - this is likely a bug with the cpython Conan package")
        endif()

        if (TARGET Python${_CONAN_PYTHON_SUFFIX}::Module)
            set_target_properties(Python${_CONAN_PYTHON_SUFFIX}::Module PROPERTIES INTERFACE_LINK_LIBRARIES cpython::python)
        endif()
        if (TARGET Python${_CONAN_PYTHON_SUFFIX}::SABIModule)
            set_target_properties(Python${_CONAN_PYTHON_SUFFIX}::SABIModule PROPERTIES INTERFACE_LINK_LIBRARIES cpython::python)
        endif()
        if (TARGET Python${_CONAN_PYTHON_SUFFIX}::Python)
            set_target_properties(Python${_CONAN_PYTHON_SUFFIX}::Python PROPERTIES INTERFACE_LINK_LIBRARIES cpython::embed)
        endif()
        """)

        # In order for the package to be relocatable, these variables must be relative to the installed CMake file
        prefix_path = "${CMAKE_CURRENT_LIST_DIR}" + ("/../../.." if is_msvc(self) else "/../..")
        template = template.replace("@PREFIX_PATH@", prefix_path)
        python_exe = "${_PREFIX_PATH}/bin/" + self._cpython_interpreter_name
        if is_msvc(self):
            python_library = "${_PREFIX_PATH}/bin/libs/" + self._exact_lib_name
        else:
            python_library = "${_PREFIX_PATH}/lib/" + self._exact_lib_name

        cmake_file = os.path.join(self.package_folder, self._cmake_module_path, "use_conan_python.cmake")
        content = template.replace("@PYTHON_EXECUTABLE@", python_exe).replace("@PYTHON_LIBRARY@", python_library)
        save(self, cmake_file, content)

    def package(self):
        copy(self, "LICENSE", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        if is_msvc(self):
            if self.options.shared:
                self._msvc_package_layout()
            else:
                self._msvc_package_copy()
            rm(self, "vcruntime*", os.path.join(self.package_folder, "bin"), recursive=True)
        else:
            autotools = Autotools(self)
            if is_apple_os(self):
                # FIXME: See https://github.com/python/cpython/issues/109796, this workaround is mentioned there
                autotools.make(target="sharedinstall", args=["DESTDIR="])
            autotools.install(args=["DESTDIR="])
            rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))
            rmdir(self, os.path.join(self.package_folder, "share"))

            # Rewrite shebangs of python scripts
            for filename in os.listdir(os.path.join(self.package_folder, "bin")):
                filepath = os.path.join(self.package_folder, "bin", filename)
                if not os.path.isfile(filepath):
                    continue
                if os.path.islink(filepath):
                    continue
                with open(filepath, "rb") as fn:
                    firstline = fn.readline(1024)
                    if not(firstline.startswith(b"#!") and b"/python" in firstline and b"/bin/sh" not in firstline):
                        continue
                    text = fn.read()
                self.output.info(f"Rewriting shebang of {filename}")
                with open(filepath, "wb") as fn:
                    fn.write(textwrap.dedent(f"""\
                        #!/bin/sh
                        ''':'
                        __file__="$0"
                        while [ -L "$__file__" ]; do
                            __file__="$(dirname "$__file__")/$(readlink "$__file__")"
                        done
                        exec "$(dirname "$__file__")/python{self._version_suffix}" "$0" "$@"
                        '''
                        """).encode())
                    fn.write(text)

            if not os.path.exists(self._cpython_symlink):
                os.symlink(f"python{self._version_suffix}", self._cpython_symlink)
        fix_apple_shared_install_name(self)

        self._write_cmake_findpython_wrapper_file()

    @property
    def _cpython_symlink(self):
        symlink = os.path.join(self.package_folder, "bin", "python")
        if self.settings.os == "Windows":
            symlink += ".exe"
        return symlink

    @property
    def _cpython_interpreter_name(self):
        python = "python"
        if is_msvc(self):
            if self.settings.build_type == "Debug":
                python += "_d"
        else:
            python += self._version_suffix
        if self.settings.os == "Windows":
            python += ".exe"
        return python

    @property
    def _cpython_interpreter_path(self):
        return os.path.join(self.package_folder, "bin", self._cpython_interpreter_name)

    @property
    def _abi_suffix(self):
        res = ""
        if self.settings.build_type == "Debug":
            res += "d"
        return res

    @property
    def _lib_name(self):
        if is_msvc(self):
            if self.settings.build_type == "Debug":
                lib_ext = "_d"
            else:
                lib_ext = ""
        else:
            lib_ext = self._abi_suffix
        return f"python{self._version_suffix}{lib_ext}"

    def package_info(self):
        py_version = Version(self.version)
        # python component: "Build a C extension for Python"
        if is_msvc(self):
            self.cpp_info.components["python"].includedirs = [os.path.join(self._msvc_install_subprefix, "include")]
            libdir = os.path.join(self._msvc_install_subprefix, "libs")
        else:
            self.cpp_info.components["python"].includedirs.append(
                os.path.join("include", f"python{self._version_suffix}{self._abi_suffix}")
            )
            libdir = "lib"
        if self.options.shared:
            self.cpp_info.components["python"].defines.append("Py_ENABLE_SHARED")
        else:
            self.cpp_info.components["python"].defines.append("Py_NO_ENABLE_SHARED")
            if self.settings.os in ["Linux", "FreeBSD"]:
                self.cpp_info.components["python"].system_libs.extend(["dl", "m", "pthread", "util"])
            elif self.settings.os == "Windows":
                self.cpp_info.components["python"].system_libs.extend(
                    ["pathcch", "shlwapi", "version", "ws2_32"]
                )
        self.cpp_info.components["python"].requires = ["zlib-ng::zlib-ng"]
        if self.settings.os != "Windows" and Version(self.version) < "3.13":
            self.cpp_info.components["python"].requires.append("libxcrypt::libxcrypt")
        self.cpp_info.components["python"].set_property(
            "pkg_config_name", f"python-{py_version.major}.{py_version.minor}"
        )
        self.cpp_info.components["python"].set_property(
            "pkg_config_aliases", [f"python{py_version.major}"]
        )
        self.cpp_info.components["python"].libdirs = []

        # embed component: "Embed Python into an application"
        self.cpp_info.components["embed"].libs = [self._lib_name]
        self.cpp_info.components["embed"].libdirs = [libdir]
        self.cpp_info.components["embed"].includedirs = []
        self.cpp_info.components["embed"].set_property(
            "pkg_config_name", f"python-{py_version.major}.{py_version.minor}-embed"
        )
        self.cpp_info.components["embed"].set_property(
            "pkg_config_aliases", [f"python{py_version.major}-embed"]
        )
        self.cpp_info.components["embed"].requires = ["python"]

        # Transparent integration with CMake's FindPython(3)
        self.cpp_info.set_property("cmake_file_name", "Python3")
        self.cpp_info.set_property("cmake_module_file_name", "Python")
        self.cpp_info.set_property("cmake_find_mode", "both")
        self.cpp_info.set_property("cmake_build_modules", [os.path.join(self._cmake_module_path, "use_conan_python.cmake")])
        self.cpp_info.set_property("system_package_version", self.version.split("-")[0])
        self.cpp_info.builddirs = [self._cmake_module_path]

        if self._supports_modules:
            # hidden components: the C extensions of python are built as dynamically loaded shared libraries.
            # C extensions or applications with an embedded Python should not need to link to them..
            self.cpp_info.components["_hidden"].requires = [
                "openssl::openssl",
                "expat::expat",
                "mpdecimal::mpdecimal",
                "libffi::libffi",
            ]
            if self.settings.os != "Windows":
                if not is_apple_os(self):
                    self.cpp_info.components["_hidden"].requires.append("util-linux-libuuid::util-linux-libuuid")
                if Version(self.version) < "3.13":
                    self.cpp_info.components["_hidden"].requires.append("libxcrypt::libxcrypt")
            if self.options.with_bz2:
                self.cpp_info.components["_hidden"].requires.append("bzip2::bzip2")
            if self.options.get_safe("with_gdbm", False):
                self.cpp_info.components["_hidden"].requires.append("gdbm::gdbm")
            if self.options.with_sqlite3:
                self.cpp_info.components["_hidden"].requires.append("sqlite3::sqlite3")
            if self.options.get_safe("with_curses", False):
                self.cpp_info.components["_hidden"].requires.append("ncurses::ncurses")
            if self.options.get_safe("with_lzma"):
                self.cpp_info.components["_hidden"].requires.append("xz_utils::xz_utils")
            if self.options.get_safe("with_tkinter"):
                self.cpp_info.components["_hidden"].requires.append("tk::tk")
            self.cpp_info.components["_hidden"].includedirs = []
            self.cpp_info.components["_hidden"].libdirs = []

        if self.options.env_vars:
            bindir = os.path.join(self.package_folder, "bin")
            self.runenv_info.append_path("PATH", bindir)
            self.buildenv_info.append_path("PATH", bindir)

        python = self._cpython_interpreter_path
        self.conf_info.define("user.cpython:python", python)
        if self.options.env_vars:
            self.runenv_info.append_path("PYTHON", python)
            self.buildenv_info.append_path("PYTHON", python)

        if is_msvc(self):
            pythonhome = os.path.join(self.package_folder, "bin")
        else:
            pythonhome = self.package_folder
        self.conf_info.define("user.cpython:pythonhome", pythonhome)

        pythonhome_required = is_msvc(self) or is_apple_os(self)
        self.conf_info.define("user.cpython:module_requires_pythonhome", pythonhome_required)

        python_root = self.package_folder
        if self.options.env_vars:
            self.runenv_info.append_path("PYTHON_ROOT", python_root)
            self.buildenv_info.append_path("PYTHON_ROOT", python_root)
        self.conf_info.define("user.cpython:python_root", python_root)
