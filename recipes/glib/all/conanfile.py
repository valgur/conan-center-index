import os
import textwrap
from pathlib import Path

from conan import ConanFile
from conan.tools.apple import fix_apple_shared_install_name, is_apple_os
from conan.tools.files import *
from conan.tools.gnu import PkgConfigDeps
from conan.tools.layout import basic_layout
from conan.tools.meson import Meson, MesonToolchain
from conan.tools.microsoft import is_msvc
from conan.tools.scm import Version

required_conan_version = ">=2.4"


class GLibConan(ConanFile):
    name = "glib"
    description = (
        "Low-level core library that forms the basis for projects such as GTK+ and GNOME. "
        "It provides data structure handling for C, portability wrappers, and interfaces "
        "for such runtime functionality as an event loop, threads, dynamic loading, and an object system."
    )
    topics = "gio", "gmodule", "gnome", "gobject", "gtk"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://gitlab.gnome.org/GNOME/glib"
    license = "LGPL-2.1-or-later"
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "with_elf": [True, False],
        "with_selinux": [True, False],
        "with_mount": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "with_elf": True,
        "with_mount": True,
        "with_selinux": True,
    }
    implements = ["auto_shared_fpic"]
    languages = ["C"]

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC
        if self.settings.os != "Linux":
            del self.options.with_mount
            del self.options.with_selinux
        self.options.with_elf = self.settings.os == "Linux"
        if is_msvc(self):
            del self.options.with_elf
        if self.settings.os == "Neutrino":
            del self.options.with_elf

    def layout(self):
        basic_layout(self, src_folder="src")

    def requirements(self):
        self.requires("zlib/[>=1.2.11 <2]")
        self.requires("libffi/3.4.4")
        self.requires("pcre2/[^10.42]")
        if self.options.get_safe("with_elf"):
            self.requires("elfutils/0.191")
        if self.options.get_safe("with_mount"):
            self.requires("libmount/2.41")
        if self.options.get_safe("with_selinux"):
            self.requires("libselinux/3.6")
        if self.settings.os != "Linux":
            # for Linux, libintl is provided by libc
            self.requires("gettext/[>=0.21 <1]", transitive_headers=True, transitive_libs=True)
        if is_apple_os(self):
            self.requires("libiconv/[^1.17]")

    def build_requirements(self):
        self.tool_requires("meson/[>=1.2.3 <2]")
        if not self.conf.get("tools.gnu:pkg_config", check_type=str):
            self.tool_requires("pkgconf/[>=2.2 <3]")
        self.tool_requires("gettext/[>=0.21 <1]")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        # https://gitlab.gnome.org/GNOME/glib/-/issues/2152
        replace_in_file(self, os.path.join(self.source_folder, "meson.build"), "subdir('fuzzing')", "")

    def generate(self):
        tc = MesonToolchain(self)

        def feature(value):
            return "enabled" if value else "disabled"

        tc.project_options["selinux"] = feature(self.options.get_safe("with_selinux"))
        tc.project_options["libmount"] = feature(self.options.get_safe("with_mount"))
        if self.settings.os == "FreeBSD" or self.settings.os == "Neutrino":
            tc.project_options["xattr"] = "false"
        tc.project_options["tests"] = "false"
        tc.project_options["libelf"] = feature(self.options.get_safe("with_elf"))

        if self.settings.os == "Neutrino":
            tc.cross_build["host"]["system"] = "qnx"
            tc.c_link_args.append("-lm")
            tc.c_link_args.append("-lsocket")

        tc.generate()

        deps = PkgConfigDeps(self)
        deps.set_property("gettext", "pkg_config_name", "intl")
        deps.generate()

    def build(self):
        meson = Meson(self)
        meson.configure()
        meson.build()

    def package(self):
        copy(self, "LGPL-2.1-or-later.txt", os.path.join(self.source_folder, "LICENSES"), os.path.join(self.package_folder, "licenses"))
        meson = Meson(self)
        meson.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))
        rm(self, "*.pdb", os.path.join(self.package_folder, "bin"))
        fix_apple_shared_install_name(self)
        fix_msvc_libname(self)

    def package_info(self):
        self.cpp_info.components["glib-2.0"].set_property("pkg_config_name", "glib-2.0")
        self.cpp_info.components["glib-2.0"].libs = ["glib-2.0"]
        self.cpp_info.components["glib-2.0"].includedirs += [
            os.path.join("include", "glib-2.0"),
            os.path.join("lib", "glib-2.0", "include")
        ]
        self.cpp_info.components["glib-2.0"].resdirs = ["share"]
        if Version(self.version) >= "2.81.0":
            if not self.options.shared and self.settings.compiler in ["gcc", "clang"]:
                self.cpp_info.components["glib-2.0"].system_libs.append("atomic")

        self.cpp_info.components["gmodule-no-export-2.0"].set_property("pkg_config_name", "gmodule-no-export-2.0")
        self.cpp_info.components["gmodule-no-export-2.0"].libs = ["gmodule-2.0"]
        self.cpp_info.components["gmodule-no-export-2.0"].resdirs = ["share"]
        self.cpp_info.components["gmodule-no-export-2.0"].requires.append("glib-2.0")

        self.cpp_info.components["gmodule-export-2.0"].set_property("pkg_config_name", "gmodule-export-2.0")
        self.cpp_info.components["gmodule-export-2.0"].requires += ["gmodule-no-export-2.0", "glib-2.0"]
        if self.settings.os in ["Linux", "FreeBSD"] or self.settings.get_safe("os.subsystem") == "cygwin":
            # https://gitlab.gnome.org/GNOME/glib/-/blob/2.82.4/meson.build?ref_type=tags#L2488-2501
            self.cpp_info.components["gmodule-export-2.0"].sharedlinkflags.append("-Wl,--export-dynamic")
            self.cpp_info.components["gmodule-export-2.0"].exelinkflags.append("-Wl,--export-dynamic")

        self.cpp_info.components["gmodule-2.0"].set_property("pkg_config_name", "gmodule-2.0")
        self.cpp_info.components["gmodule-2.0"].requires = ["gmodule-export-2.0"]

        self.cpp_info.components["gobject-2.0"].set_property("pkg_config_name", "gobject-2.0")
        self.cpp_info.components["gobject-2.0"].libs = ["gobject-2.0"]
        self.cpp_info.components["gobject-2.0"].resdirs = ["share"]
        self.cpp_info.components["gobject-2.0"].requires += ["glib-2.0", "libffi::libffi"]

        self.cpp_info.components["gthread-2.0"].set_property("pkg_config_name", "gthread-2.0")
        self.cpp_info.components["gthread-2.0"].libs = ["gthread-2.0"]
        self.cpp_info.components["gthread-2.0"].resdirs = ["share"]
        self.cpp_info.components["gthread-2.0"].requires.append("glib-2.0")

        self.cpp_info.components["gio-2.0"].set_property("pkg_config_name", "gio-2.0")
        self.cpp_info.components["gio-2.0"].libs = ["gio-2.0"]
        self.cpp_info.components["gio-2.0"].resdirs = ["share"]
        self.cpp_info.components["gio-2.0"].requires += ["glib-2.0", "gobject-2.0", "gmodule-no-export-2.0", "zlib::zlib"]

        self.cpp_info.components["gresource"].set_property("pkg_config_name", "gresource")
        self.cpp_info.components["gresource"].libs = []  # this is actually an executable

        if Version(self.version) >= "2.79.0":
            self.cpp_info.components["girepository-2.0"].set_property("pkg_config_name", "girepository-2.0")
            self.cpp_info.components["girepository-2.0"].set_property("pkg_config_custom_content", textwrap.dedent("""\
                gidatadir=${datadir}/gobject-introspection-1.0
                girdir=${datadir}/gir-1.0
                typelibdir=${libdir}/girepository-1.0
            """))
            self.cpp_info.components["girepository-2.0"].libs = ["girepository-2.0"]
            self.cpp_info.components["girepository-2.0"].resdirs = ["share"]
            self.cpp_info.components["girepository-2.0"].requires += ["glib-2.0", "gobject-2.0", "gmodule-no-export-2.0", "gio-2.0", "libffi::libffi"]
            if self.settings.os in ["Linux", "FreeBSD"]:
                self.cpp_info.components["girepository-2.0"].system_libs.append("m")

        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.components["glib-2.0"].system_libs.append("pthread")
            self.cpp_info.components["gmodule-no-export-2.0"].system_libs.append("pthread")
            self.cpp_info.components["gmodule-no-export-2.0"].system_libs.append("dl")
            self.cpp_info.components["gmodule-export-2.0"].sharedlinkflags.append("-Wl,--export-dynamic")
            self.cpp_info.components["gmodule-2.0"].sharedlinkflags.append("-Wl,--export-dynamic")
            self.cpp_info.components["gthread-2.0"].system_libs.append("pthread")
            self.cpp_info.components["gio-2.0"].system_libs.append("dl")

        if self.settings.os == "Neutrino":
            self.cpp_info.components["gmodule-export-2.0"].sharedlinkflags.append("-Wl,--export-dynamic")
            self.cpp_info.components["gmodule-2.0"].sharedlinkflags.append("-Wl,--export-dynamic")
            self.cpp_info.components["glib-2.0"].system_libs.append("m")
            self.cpp_info.components["glib-2.0"].system_libs.append("socket")
            self.cpp_info.components["gmodule-no-export-2.0"].system_libs.append("c")
            self.cpp_info.components["gio-2.0"].system_libs.append("c")
            self.cpp_info.components["gio-2.0"].system_libs.append("socket")

        if self.settings.os == "Windows":
            self.cpp_info.components["glib-2.0"].system_libs += ["ws2_32", "ole32", "shell32", "user32", "advapi32"]
            self.cpp_info.components["gio-2.0"].system_libs.extend(["iphlpapi", "dnsapi", "shlwapi"])
            self.cpp_info.components["gio-windows-2.0"].set_property("pkg_config_name", "gio-windows-2.0")
            self.cpp_info.components["gio-windows-2.0"].requires = ["gobject-2.0", "gmodule-no-export-2.0", "gio-2.0"]
            self.cpp_info.components["gio-windows-2.0"].includedirs = [os.path.join("include", "gio-win32-2.0")]
        else:
            self.cpp_info.components["gio-unix-2.0"].set_property("pkg_config_name", "gio-unix-2.0")
            self.cpp_info.components["gio-unix-2.0"].requires += ["gobject-2.0", "gio-2.0"]
            self.cpp_info.components["gio-unix-2.0"].includedirs = [os.path.join("include", "gio-unix-2.0")]

        if self.settings.os == "Macos":
            self.cpp_info.components["glib-2.0"].system_libs.append("resolv")
            self.cpp_info.components["glib-2.0"].frameworks += ["Foundation", "CoreServices", "CoreFoundation"]
            self.cpp_info.components["gio-2.0"].frameworks.append("AppKit")

            if is_apple_os(self):
                self.cpp_info.components["glib-2.0"].requires.append("libiconv::libiconv")

        self.cpp_info.components["glib-2.0"].requires.append("pcre2::pcre2")

        if self.settings.os == "Linux":
            self.cpp_info.components["gio-2.0"].system_libs.append("resolv")
        else:
            self.cpp_info.components["glib-2.0"].requires.append("gettext::gettext")

        if self.options.get_safe("with_mount"):
            self.cpp_info.components["gio-2.0"].requires.append("libmount::libmount")

        if self.options.get_safe("with_selinux"):
            self.cpp_info.components["gio-2.0"].requires.append("libselinux::libselinux")

        if self.options.get_safe("with_elf"):
            self.cpp_info.components["gresource"].requires.append("elfutils::libelf")  # this is actually an executable

        self.buildenv_info.define_path("GLIB_COMPILE_SCHEMAS", os.path.join(self.package_folder, "bin", "glib-compile-schemas"))

        pkgconfig_variables = {
            'datadir': '${prefix}/share',
            'schemasdir': '${datadir}/glib-2.0/schemas',
            'bindir': '${prefix}/bin',
            # Can't use libdir here as it is libdir1 when using the PkgConfigDeps generator.
            'giomoduledir': '${prefix}/lib/gio/modules',
            'gio': '${bindir}/gio',
            'gio_querymodules': '${bindir}/gio-querymodules',
            'glib_compile_schemas': '${bindir}/glib-compile-schemas',
            'glib_compile_resources': '${bindir}/glib-compile-resources',
            'gdbus': '${bindir}/gdbus',
            'gdbus_codegen': '${bindir}/gdbus-codegen',
            'gresource': '${bindir}/gresource',
            'gsettings': '${bindir}/gsettings'
        }
        self.cpp_info.components["gio-2.0"].set_property(
            "pkg_config_custom_content",
            "\n".join(f"{key}={value}" for key,value in pkgconfig_variables.items()))

        pkgconfig_variables = {
            'bindir': '${prefix}/bin',
            'glib_genmarshal': '${bindir}/glib-genmarshal',
            'gobject_query': '${bindir}/gobject-query',
            'glib_mkenums': '${bindir}/glib-mkenums'
        }
        self.cpp_info.components["glib-2.0"].set_property(
            "pkg_config_custom_content",
            "\n".join(f"{key}={value}" for key, value in pkgconfig_variables.items()))

def fix_msvc_libname(conanfile, remove_lib_prefix=True):
    """remove lib prefix & change extension to .lib in case of cl like compiler"""
    if not conanfile.settings.get_safe("compiler.runtime"):
        return
    for libdir in getattr(conanfile.cpp.package, "libdirs"):
        libdir = Path(conanfile.package_folder, libdir)
        for ext in [".dll.a", ".dll.lib", ".a"]:
            for path in sorted(libdir.glob(f"*{ext}")):
                libname = path.name[0:-len(ext)]
                if remove_lib_prefix and libname.startswith("lib"):
                    libname = libname[3:]
                rename(conanfile, path, path.parent / f"{libname}.lib")
