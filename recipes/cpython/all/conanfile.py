import os

from conan.errors import ConanInvalidConfiguration
from conan.tools.apple import is_apple_os
from conan.tools.files import *
from conan.tools.layout import basic_layout
from conan.tools.microsoft import *
from conan.tools.scm import Version

from cpython_autotools import CPythonAutotools
from cpython_msvc import CPythonMSVC

required_conan_version = ">=2.4"


class CPythonConan(CPythonAutotools, CPythonMSVC):
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
        "gil": [True, False],
        "optimizations": [True, False],
        "lto": [True, False],
        "docstrings": [True, False],
        "pymalloc": [True, False],
        "with_bz2": [True, False],
        "with_curses": [True, False],
        "with_gdbm": [True, False],
        "with_lzma": [True, False],
        "with_readline": ["editline", "readline", False],
        "with_sqlite3": [True, False],
        "with_tkinter": [True, False],
        "with_zstd": [True, False],

        # options that don't change package id
        "env_vars": [True, False],  # set environment variables
    }
    default_options = {
        "shared": True,
        "fPIC": True,
        "gil": True,
        "optimizations": False,
        "lto": False,
        "docstrings": True,
        "pymalloc": True,
        "with_bz2": True,
        "with_curses": True,
        "with_gdbm": True,
        "with_lzma": True,
        "with_readline": "editline",
        "with_sqlite3": True,
        "with_tkinter": True,
        "with_zstd": True,

        # options that don't change package id
        "env_vars": True,
    }
    languages = ["C"]

    exports = ["cpython_autotools.py", "cpython_msvc.py"]

    @property
    def _supports_modules(self):
        return self.options.shared or not is_msvc(self)

    @property
    def _version_suffix(self):
        v = Version(self.version)
        joiner = "" if is_msvc(self) else "."
        return f"{v.major}{joiner}{v.minor}"

    def export_sources(self):
        copy(self, "use_conan_python.cmake", self.recipe_folder, self.export_sources_folder)
        export_conandata_patches(self)

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC
        if is_msvc(self):
            del self.options.gil
            del self.options.lto
            del self.options.docstrings
            del self.options.pymalloc
            del self.options.with_curses
            del self.options.with_gdbm
            del self.options.with_readline
        if Version(self.version) < "3.13":
            self.options.rm_safe("gil")
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
        if self.options.get_safe("with_gdbm"):
            self.requires("gdbm/1.23")
        if self.options.get_safe("with_readline") == "readline":
            self.requires("readline/[^8.2]")
        elif self.options.get_safe("with_readline") == "editline":
            self.requires("editline/[^3.1]")
        if self.options.get_safe("with_sqlite3"):
            self.requires("sqlite3/[>=3.45.0 <4]")
        if self.options.get_safe("with_tkinter"):
            self.requires("tk/8.6.16")
        if self.options.get_safe("with_curses"):
            # Used in a public header
            # https://github.com/python/cpython/blob/v3.10.13/Include/py_curses.h#L34
            self.requires("ncurses/[^6.4]", transitive_headers=True, transitive_libs=True)
        if self.options.get_safe("with_lzma"):
            self.requires("xz_utils/[^5.4.5]")
        if self.options.get_safe("with_zstd"):
            self.requires("zstd/[~1.5]")

    def package_id(self):
        del self.info.options.env_vars

    def validate(self):
        if is_msvc(self):
            self._msvc_validate()
        else:
            self._autotools_validate()
        if self.options.get_safe("with_curses") and not self.dependencies["ncurses"].options.with_widec:
            raise ConanInvalidConfiguration("cpython requires ncurses with wide character support")

    def build_requirements(self):
        if is_msvc(self):
            self._msvc_build_requirements()
        else:
            self._autotools_build_requirements()

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        apply_conandata_patches(self)

    def generate(self):
        if is_msvc(self):
            self._msvc_generate()
        else:
            self._autotools_generate()

    def _patch_sources(self):
        # Remove vendored packages
        rmdir(self, os.path.join(self.source_folder, "Modules", "_decimal", "libmpdec"))
        rmdir(self, os.path.join(self.source_folder, "Modules", "expat"))

        if is_msvc(self):
            self._msvc_patch_sources()
        else:
            self._autotools_patch_sources()

    def build(self):
        self._patch_sources()
        if is_msvc(self):
            self._msvc_build()
        else:
            self._autotools_build()

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
        # In order for the package to be relocatable, these variables must be relative to the installed CMake file
        prefix_path = "${CMAKE_CURRENT_LIST_DIR}" + ("/../../.." if is_msvc(self) else "/../..")
        python_exe = "${_PREFIX_PATH}/bin/" + self._cpython_interpreter_name
        if is_msvc(self):
            python_library = "${_PREFIX_PATH}/bin/libs/" + self._exact_lib_name
        else:
            python_library = "${_PREFIX_PATH}/lib/" + self._exact_lib_name
        content = load(self, os.path.join(self.export_sources_folder, "use_conan_python.cmake"))
        content = content.replace("@PREFIX_PATH@", prefix_path)
        content = content.replace("@PYTHON_EXECUTABLE@", python_exe)
        content = content.replace("@PYTHON_LIBRARY@", python_library)
        cmake_file = os.path.join(self.package_folder, self._cmake_module_path, "use_conan_python.cmake")
        save(self, cmake_file, content)

    def package(self):
        copy(self, "LICENSE", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        if is_msvc(self):
            self._msvc_package()
        else:
            self._autotools_package()
        self._write_cmake_findpython_wrapper_file()

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

    @property
    def _libdir(self):
        if is_msvc(self):
            return os.path.join(self._msvc_install_subprefix, "libs")
        else:
            return "lib"

    def package_info(self):
        # Transparent integration with CMake's FindPython(3)
        self.cpp_info.set_property("cmake_file_name", "Python3")
        self.cpp_info.set_property("cmake_module_file_name", "Python")
        self.cpp_info.set_property("cmake_find_mode", "both")
        self.cpp_info.set_property("cmake_build_modules", [os.path.join(self._cmake_module_path, "use_conan_python.cmake")])
        self.cpp_info.set_property("system_package_version", self.version.split("-")[0])
        self.cpp_info.builddirs = [self._cmake_module_path]

        py_version = Version(self.version)

        # python component: "Build a C extension for Python"
        comp_python = self.cpp_info.components["python"]
        comp_python.set_property("pkg_config_name", f"python-{py_version.major}.{py_version.minor}")
        comp_python.set_property("pkg_config_aliases", [f"python{py_version.major}"])
        if is_msvc(self):
            comp_python.includedirs = [os.path.join(self._msvc_install_subprefix, "include")]
        else:
            comp_python.includedirs = ["include", os.path.join("include", f"python{self._version_suffix}{self._abi_suffix}")]
        comp_python.libdirs = []
        if self.options.shared:
            comp_python.defines.append("Py_ENABLE_SHARED")
        else:
            comp_python.defines.append("Py_NO_ENABLE_SHARED")
            if self.settings.os in ["Linux", "FreeBSD"]:
                comp_python.system_libs = ["dl", "m", "pthread", "util"]
            elif self.settings.os == "Windows":
                comp_python.system_libs = ["pathcch", "shlwapi", "version", "ws2_32"]
        comp_python.requires = ["zlib-ng::zlib-ng"]
        if self.settings.os != "Windows" and Version(self.version) < "3.13":
            comp_python.requires.append("libxcrypt::libxcrypt")

        # embed component: "Embed Python into an application"
        comp_embed = self.cpp_info.components["embed"]
        comp_embed.set_property("pkg_config_name", f"python-{py_version.major}.{py_version.minor}-embed")
        comp_embed.set_property("pkg_config_aliases", [f"python{py_version.major}-embed"])
        comp_embed.libs = [self._lib_name]
        comp_embed.libdirs = [self._libdir]
        comp_embed.includedirs = []
        comp_embed.requires = ["python"]

        if self._supports_modules:
            # hidden components: the C extensions of python are built as dynamically loaded shared libraries.
            # C extensions or applications with an embedded Python should not need to link to them..
            hidden_requires = [
                "openssl::openssl",
                "expat::expat",
                "mpdecimal::mpdecimal",
                "libffi::libffi",
            ]
            if self.settings.os != "Windows":
                if not is_apple_os(self):
                    hidden_requires.append("util-linux-libuuid::util-linux-libuuid")
                if Version(self.version) < "3.13":
                    hidden_requires.append("libxcrypt::libxcrypt")
            if self.options.with_bz2:
                hidden_requires.append("bzip2::bzip2")
            if self.options.get_safe("with_gdbm"):
                hidden_requires.append("gdbm::gdbm")
            if self.options.with_readline == "readline":
                hidden_requires.append("readline::readline")
            elif self.options.with_readline == "editline":
                hidden_requires.append("editline::editline")
            if self.options.with_sqlite3:
                hidden_requires.append("sqlite3::sqlite3")
            if self.options.get_safe("with_curses"):
                hidden_requires.append("ncurses::ncurses")
            if self.options.get_safe("with_lzma"):
                hidden_requires.append("xz_utils::xz_utils")
            if self.options.get_safe("with_tkinter"):
                hidden_requires.append("tk::tk")
            if self.options.get_safe("with_zstd"):
                hidden_requires.append("zstd::zstd")
            self.cpp_info.components["_hidden"].requires = hidden_requires
            self.cpp_info.components["_hidden"].includedirs = []
            self.cpp_info.components["_hidden"].libdirs = []

        python_path = self._cpython_interpreter_path
        self.conf_info.define("user.cpython:python", python_path)
        pythonhome = os.path.join(self.package_folder, "bin") if is_msvc(self) else self.package_folder
        self.conf_info.define("user.cpython:pythonhome", pythonhome)
        pythonhome_required = is_msvc(self) or is_apple_os(self)
        self.conf_info.define("user.cpython:module_requires_pythonhome", pythonhome_required)
        python_root = self.package_folder
        self.conf_info.define("user.cpython:python_root", python_root)
        if self.options.env_vars:
            self.runenv_info.append_path("PYTHON", python_path)
            self.buildenv_info.append_path("PYTHON", python_path)
            self.runenv_info.append_path("PYTHON_ROOT", python_root)
            self.buildenv_info.append_path("PYTHON_ROOT", python_root)
