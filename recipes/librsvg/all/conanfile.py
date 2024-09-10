import os
import textwrap

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.apple import fix_apple_shared_install_name
from conan.tools.env import VirtualBuildEnv, Environment
from conan.tools.files import copy, get, replace_in_file, export_conandata_patches, apply_conandata_patches
from conan.tools.gnu import PkgConfigDeps
from conan.tools.layout import basic_layout
from conan.tools.meson import Meson
from conan.tools.meson.toolchain import MesonToolchain
from conan.tools.microsoft import is_msvc

required_conan_version = ">=1.53.0"

class LibrsvgConan(ConanFile):
    name = "librsvg"
    description = "A library to render SVG images to Cairo surfaces."
    license = "LGPL-2.0-or-later"
    homepage = "https://gitlab.gnome.org/GNOME/librsvg"
    url = "https://github.com/conan-io/conan-center-index"
    topics = ("svg", "vector-graphics", "cairo", "gnome")

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

    @property
    def _settings_build(self):
        return getattr(self, "settings_build", self.settings)

    def export_sources(self):
        export_conandata_patches(self)

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC
        self.options["pango"].with_cairo = True
        self.options["pango"].with_freetype = True

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")
        self.settings.rm_safe("compiler.cppstd")
        self.settings.rm_safe("compiler.libcxx")

    def layout(self):
        basic_layout(self, src_folder="src")

    def requirements(self):
        # https://gitlab.gnome.org/GNOME/librsvg/-/blob/main/ci/build-dependencies.sh#L5-13
        # All public includes are located here:
        # https://gitlab.gnome.org/GNOME/librsvg/-/blob/2.57.0/include/librsvg/rsvg.h#L30-34
        self.requires("glib/2.78.3", transitive_headers=True, transitive_libs=True, force=True)
        # self.requires("gobject-introspection/1.78.1")
        self.requires("freetype/2.13.2")
        self.requires("cairo/1.18.0", transitive_headers=True, transitive_libs=True)
        self.requires("harfbuzz/8.3.0")
        self.requires("pango/1.54.0")
        self.requires("libxml2/[>=2.12.5 <3]")
        self.requires("gdk-pixbuf/2.42.10", transitive_headers=True, transitive_libs=True)

    def validate(self):
        if is_msvc(self):
            # Not impossible, but building with MSVC is very fragile
            # https://gitlab.gnome.org/GNOME/librsvg/-/blob/main/win32/MSVC-Builds.md
            raise ConanInvalidConfiguration("Building librsvg with MSVC is currently not supported")
        if not self.dependencies["pango"].options.with_cairo:
            raise ConanInvalidConfiguration("librsvg requires -o pango/*:with_cairo=True")
        if not self.dependencies["pango"].options.with_freetype:
            raise ConanInvalidConfiguration("librsvg requires -o pango/*:with_freetype=True")

    def build_requirements(self):
        self.tool_requires("meson/[>=1.2.3 <2]")
        if not self.conf.get("tools.gnu:pkg_config", check_type=str):
            self.tool_requires("pkgconf/[>=2.2 <3]")
        self.tool_requires("rust/1.81.0")
        self.tool_requires("cargo-cbuild/0.10.4")
        self.tool_requires("gdk-pixbuf/<host_version>")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        VirtualBuildEnv(self).generate()
        tc = MesonToolchain(self)
        tc.project_options["pixbuf"] = "enabled"
        tc.project_options["pixbuf-loader"] = "enabled"
        tc.project_options["introspection"] = "disabled"
        tc.project_options["avif"] = "disabled"
        tc.project_options["vala"] = "disabled"
        tc.project_options["docs"] = "disabled"
        tc.project_options["tests"] = "false"
        tc.generate()
        deps = PkgConfigDeps(self)
        deps.generate()
        env = Environment()
        env.define_path("CARGO_HOME", os.path.join(self.build_folder, "cargo"))
        env.vars(self).save_script("cargo_build_env")

    def _patch_sources(self):
        apply_conandata_patches(self)
        # Fix freetype version check, which uses a different versioning format
        replace_in_file(self, os.path.join(self.source_folder, "meson.build"), "20.0.14", "2.8")
        replace_in_file(self, os.path.join(self.source_folder, "rsvg", "Cargo.toml"), "20.0.14", "2.8")

    def build(self):
        self._patch_sources()
        meson = Meson(self)
        meson.configure()
        meson.build()

    def package(self):
        copy(self, "COPYING.LIB", self.source_folder, os.path.join(self.package_folder, "licenses"))
        meson = Meson(self)
        meson.install()
        # rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))
        # rmdir(self, os.path.join(self.package_folder, "share"))
        # rmdir(self, os.path.join(self.package_folder, "gdk-pixbuf-2.0"))
        fix_apple_shared_install_name(self)

    def package_info(self):
        self.cpp_info.set_property("pkg_config_name", "librsvg-2.0")
        self.cpp_info.includedirs.append(os.path.join("include", "librsvg-2.0"))
        self.cpp_info.libs = ["librsvg-2"]

        # https://gitlab.gnome.org/GNOME/librsvg/-/blob/2.57.0/configure.ac#L161-173
        self.cpp_info.requires = [
            "cairo::cairo_",
            "cairo::cairo-png",
            "cairo::cairo-gobject",
            "fontconfig::fontconfig",
            "freetype::freetype",
            "gdk-pixbuf::gdk-pixbuf",
            "glib::gio-2.0",
            "glib::glib-2.0",
            "harfbuzz::harfbuzz",
            "libxml2::libxml2",
            "pango::pangocairo",
            "pango::pangoft2",
        ]
