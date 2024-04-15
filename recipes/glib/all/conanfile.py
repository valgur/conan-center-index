from conan import ConanFile
from conan.tools.apple import fix_apple_shared_install_name, is_apple_os
from conan.tools.env import VirtualBuildEnv, Environment
from conan.tools.files import apply_conandata_patches, copy, export_conandata_patches, get, replace_in_file, rm, rmdir, load, save
from conan.tools.gnu import PkgConfigDeps
from conan.tools.layout import basic_layout
from conan.tools.meson import Meson, MesonToolchain
from conan.tools.microsoft import is_msvc
from conan.tools.scm import Version
import os
import shutil


required_conan_version = ">=1.53.0"


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
    # The latter half of the AND in the license is for the vendored pypa/packaging components
    license = "LGPL-2.1-or-later AND (Apache-2.0 OR BSD-2-Clause)"
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
    short_paths = True

    def export_sources(self):
        export_conandata_patches(self)

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC
        if self.settings.os != "Linux":
            del self.options.with_mount
            del self.options.with_selinux
        if is_msvc(self):
            del self.options.with_elf

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")
        self.settings.rm_safe("compiler.cppstd")
        self.settings.rm_safe("compiler.libcxx")
        if Version(self.version) < "2.79":
            self.license = "LGPL-2.1-or-later"

    def layout(self):
        basic_layout(self, src_folder="src")

    def requirements(self):
        self.requires("zlib/[>=1.2.11 <2]")
        self.requires("libffi/3.4.4")
        self.requires("pcre2/10.42")
        if self.options.get_safe("with_elf"):
            self.requires("libelf/0.8.13")
        if self.options.get_safe("with_mount"):
            self.requires("libmount/2.39")
        if self.options.get_safe("with_selinux"):
            self.requires("libselinux/3.5")
        if self.settings.os != "Linux":
            # for Linux, gettext is provided by libc
            self.requires("libgettext/0.22", transitive_headers=True, transitive_libs=True)

        if is_apple_os(self):
            self.requires("libiconv/1.17")

    def build_requirements(self):
        self.tool_requires("meson/1.4.0")
        if not self.conf.get("tools.gnu:pkg_config", check_type=str):
            self.tool_requires("pkgconf/2.1.0")

    @property
    def _vendor_pypa_packaging(self):
        return Version(self.version) >= "2.79"

    @property
    def _pypa_packaging_dir(self):
        return os.path.join(self.source_folder, "pypa-packaging")

    @property
    def _codegen_dir(self):
        return os.path.join(self.source_folder, "gio", "gdbus-2.0", "codegen")

    def source(self):
        if self._vendor_pypa_packaging:
            get(self, **self.conan_data["sources"][self.version]["source"], strip_root=True)
            # Vendor https://github.com/pypa/packaging/blob/24.0/src/packaging/version.py
            get(self, **self.conan_data["sources"][self.version]["pypa-packaging"], strip_root=True,
                destination=self._pypa_packaging_dir)
        else:
            get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        virtual_build_env = VirtualBuildEnv(self)
        virtual_build_env.generate()
        tc = PkgConfigDeps(self)
        tc.generate()
        tc = MesonToolchain(self)

        tc.project_options["selinux"] = "enabled" if self.options.get_safe("with_selinux") else "disabled"
        tc.project_options["libmount"] = "enabled" if self.options.get_safe("with_mount") else "disabled"
        if self.settings.os == "FreeBSD":
            tc.project_options["xattr"] = "false"
        tc.project_options["tests"] = "false"
        tc.project_options["libelf"] = "enabled" if self.options.get_safe("with_elf") else "disabled"
        if Version(self.version) >= "2.79.0":
            # https://gitlab.gnome.org/GNOME/glib/-/commit/fe32c3f5c5155eab5cd4838867b0c95beefa2239
            tc.project_options["introspection"] = "disabled"
        tc.generate()

    def _patch_sources(self):
        apply_conandata_patches(self)
        replace_in_file(self,
            os.path.join(self.source_folder, "meson.build"),
            "subdir('fuzzing')",
            "#subdir('fuzzing')",
        )  # https://gitlab.gnome.org/GNOME/glib/-/issues/2152
        if self.settings.os != "Linux":
            # allow to find gettext
            replace_in_file(self,
                os.path.join(self.source_folder, "meson.build"),
                "libintl = dependency('intl', required: false",
                "libintl = dependency('libgettext', method : 'pkg-config', required : false",
            )

        replace_in_file(self,
            os.path.join(
                self.source_folder,
                "gio",
                "gdbus-2.0",
                "codegen",
                "gdbus-codegen.in",
            ),
            "'share'",
            "'res'",
        )

        if self._vendor_pypa_packaging:
            # Use the vendored packaging.version.Version
            copy(self, "version.py", os.path.join(self._pypa_packaging_dir, "src", "packaging"), self._codegen_dir)
            copy(self, "_structures.py", os.path.join(self._pypa_packaging_dir, "src", "packaging"), self._codegen_dir)
            replace_in_file(self, os.path.join(self._codegen_dir, "utils.py"),
                            "import packaging.version",
                            "from .version import Version")
            replace_in_file(self, os.path.join(self._codegen_dir, "utils.py"),
                            "packaging.version.Version",
                            "Version")
            replace_in_file(self, os.path.join(self._codegen_dir, "meson.build"),
                            "'utils.py',",
                            "'utils.py', 'version.py', '_structures.py',")
            replace_in_file(self, os.path.join(self.source_folder, "meson.build"),
                            ".find_installation(modules: ['packaging'])",
                            ".find_installation()")

    def build(self):
        self._patch_sources()
        meson = Meson(self)
        meson.configure()
        meson.build()

    def package(self):
        copy(self, "LGPL-2.1-or-later.txt", os.path.join(self.source_folder, "LICENSES"), os.path.join(self.package_folder, "licenses"))
        if self._vendor_pypa_packaging:
            # pypa/packaging license files
            copy(self, "LICENSE*", os.path.join(self.source_folder, "pypa-packaging"), os.path.join(self.package_folder, "licenses"))
            os.rename(os.path.join(self.package_folder, "licenses", "LICENSE"),
                      os.path.join(self.package_folder, "licenses", "LICENSE.pypa-packaging"))
        meson = Meson(self)
        meson.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))
        rmdir(self, os.path.join(self.package_folder, "libexec"))
        shutil.move(
            os.path.join(self.package_folder, "share"),
            os.path.join(self.package_folder, "res"),
        )
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
        self.cpp_info.components["glib-2.0"].resdirs = ["res"]

        self.cpp_info.components["gmodule-no-export-2.0"].set_property("pkg_config_name", "gmodule-no-export-2.0")
        self.cpp_info.components["gmodule-no-export-2.0"].libs = ["gmodule-2.0"]
        self.cpp_info.components["gmodule-no-export-2.0"].resdirs = ["res"]
        self.cpp_info.components["gmodule-no-export-2.0"].requires.append("glib-2.0")

        self.cpp_info.components["gmodule-export-2.0"].set_property("pkg_config_name", "gmodule-export-2.0")
        self.cpp_info.components["gmodule-export-2.0"].requires += ["gmodule-no-export-2.0", "glib-2.0"]

        self.cpp_info.components["gmodule-2.0"].set_property("pkg_config_name", "gmodule-2.0")
        self.cpp_info.components["gmodule-2.0"].requires += ["gmodule-no-export-2.0", "glib-2.0"]

        self.cpp_info.components["gobject-2.0"].set_property("pkg_config_name", "gobject-2.0")
        self.cpp_info.components["gobject-2.0"].libs = ["gobject-2.0"]
        self.cpp_info.components["gobject-2.0"].resdirs = ["res"]
        self.cpp_info.components["gobject-2.0"].requires += ["glib-2.0", "libffi::libffi"]

        self.cpp_info.components["gthread-2.0"].set_property("pkg_config_name", "gthread-2.0")
        self.cpp_info.components["gthread-2.0"].libs = ["gthread-2.0"]
        self.cpp_info.components["gthread-2.0"].resdirs = ["res"]
        self.cpp_info.components["gthread-2.0"].requires.append("glib-2.0")

        self.cpp_info.components["gio-2.0"].set_property("pkg_config_name", "gio-2.0")
        self.cpp_info.components["gio-2.0"].libs = ["gio-2.0"]
        self.cpp_info.components["gio-2.0"].resdirs = ["res"]
        self.cpp_info.components["gio-2.0"].requires += ["glib-2.0", "gobject-2.0", "gmodule-2.0", "zlib::zlib"]

        self.cpp_info.components["gresource"].set_property("pkg_config_name", "gresource")
        self.cpp_info.components["gresource"].libs = []  # this is actually an executable

        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.components["glib-2.0"].system_libs.append("pthread")
            self.cpp_info.components["gmodule-no-export-2.0"].system_libs.append("pthread")
            self.cpp_info.components["gmodule-no-export-2.0"].system_libs.append("dl")
            self.cpp_info.components["gmodule-export-2.0"].sharedlinkflags.append("-Wl,--export-dynamic")
            self.cpp_info.components["gmodule-2.0"].sharedlinkflags.append("-Wl,--export-dynamic")
            self.cpp_info.components["gthread-2.0"].system_libs.append("pthread")
            self.cpp_info.components["gio-2.0"].system_libs.append("dl")

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
            self.cpp_info.components["glib-2.0"].requires.append("libgettext::libgettext")

        if self.options.get_safe("with_mount"):
            self.cpp_info.components["gio-2.0"].requires.append("libmount::libmount")

        if self.options.get_safe("with_selinux"):
            self.cpp_info.components["gio-2.0"].requires.append("libselinux::libselinux")

        if self.options.get_safe("with_elf"):
            self.cpp_info.components["gresource"].requires.append("libelf::libelf")  # this is actually an executable

        self.env_info.GLIB_COMPILE_SCHEMAS = os.path.join(self.package_folder, "bin", "glib-compile-schemas")
        self.env_info.PATH.append(os.path.join(self.package_folder, "bin"))

        pkgconfig_variables = {
            'datadir': '${prefix}/res',
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
    from conan.tools.files import rename
    import glob
    if not conanfile.settings.get_safe("compiler.runtime"):
        return
    libdirs = getattr(conanfile.cpp.package, "libdirs")
    for libdir in libdirs:
        for ext in [".dll.a", ".dll.lib", ".a"]:
            full_folder = os.path.join(conanfile.package_folder, libdir)
            for filepath in glob.glob(os.path.join(full_folder, f"*{ext}")):
                libname = os.path.basename(filepath)[0:-len(ext)]
                if remove_lib_prefix and libname[0:3] == "lib":
                    libname = libname[3:]
                rename(conanfile, filepath, os.path.join(os.path.dirname(filepath), f"{libname}.lib"))
