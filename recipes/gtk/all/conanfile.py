# TODO: verify the Conan v2 migration

import os

from conan import ConanFile, conan_version
from conan.errors import ConanInvalidConfiguration, ConanException
from conan.tools.android import android_abi
from conan.tools.apple import XCRun, fix_apple_shared_install_name, is_apple_os, to_apple_arch
from conan.tools.build import build_jobs, can_run, check_min_cppstd, cross_building, default_cppstd, stdcpp_library, valid_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.env import Environment, VirtualBuildEnv, VirtualRunEnv
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
from conan.tools.gnu import Autotools, AutotoolsDeps, AutotoolsToolchain, PkgConfig, PkgConfigDeps
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


class GtkConan(ConanFile):
    name = "gtk"
    description = "libraries used for creating graphical user interfaces for applications."
    license = "LGPL-2.1-or-later"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://www.gtk.org"
    topics = "widgets"
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "with_wayland": [True, False],
        "with_x11": [True, False],
        "with_pango": [True, False],
        "with_ffmpeg": [True, False],
        "with_gstreamer": [True, False],
        "with_cups": [True, False],
        "with_cloudprint": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "with_wayland": False,
        "with_x11": True,
        "with_pango": True,
        "with_ffmpeg": False,
        "with_gstreamer": False,
        "with_cups": False,
        "with_cloudprint": False,
    }

    @property
    def _gtk4(self):
        return Version(self.version).major == 4

    @property
    def _gtk3(self):
        return Version(self.version).major == 3

    def export_sources(self):
        export_conandata_patches(self)

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC
            # Fix duplicate definitions of DllMain
            self.options["gdk-pixbuf"].shared = True
            # Fix segmentation fault
            self.options["cairo"].shared = True
        if Version(self.version) >= "4.1.0":
            # The upstream meson file does not create a static library
            # See https://github.com/GNOME/gtk/commit/14f0a0addb9a195bad2f8651f93b95450b186bd6
            self.options.shared = True
        if self.settings.os not in ["Linux", "FreeBSD"]:
            self.options.rm_safe("with_wayland")
            self.options.rm_safe("with_x11")

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")
        self.settings.rm_safe("compiler.libcxx")
        self.settings.rm_safe("compiler.cppstd")
        if self.settings.os in ["Linux", "FreeBSD"]:
            if self.options.with_wayland or self.options.with_x11:
                if not self.options.with_pango:
                    raise ConanInvalidConfiguration("with_pango option is mandatory when with_wayland or with_x11 is used")

    def layout(self):
        basic_layout(self, src_folder="src")

    def requirements(self):
        self.requires("gdk-pixbuf/2.42.10")
        self.requires("glib/2.77.1", force=True)
        if self._gtk4 or not is_msvc(self):
            self.requires("cairo/1.17.6")
            self.requires("libpng/1.6.40", force=True)
        if self._gtk4:
            self.requires("graphene/1.10.8")
            self.requires("fribidi/1.0.12")
            self.requires("libtiff/4.5.1")
            self.requires("libjpeg/9e")
        if self.settings.os in ["Linux", "FreeBSD"]:
            if self._gtk4:
                self.requires("xkbcommon/1.5.0")
            if self._gtk3:
                self.requires("at-spi2-atk/2.38.0")
            if self.options.with_wayland:
                if self._gtk3:
                    self.requires("xkbcommon/1.5.0")
                self.requires("wayland/1.22.0")
            if self.options.with_x11:
                self.requires("xorg/system")
        if self._gtk3:
            self.requires("atk/2.38.0")
        self.requires("libepoxy/1.5.10")
        if self.options.with_pango:
            self.requires("pango/1.50.14")
        if self.options.with_ffmpeg:
            self.requires("ffmpeg/6.0")
        if self.options.with_gstreamer:
            self.requires("gstreamer/1.22.3")

    def validate(self):
        if self.settings.compiler == "gcc" and Version(self.settings.compiler.version) < "5":
            raise ConanInvalidConfiguration("this recipes does not support GCC before version 5. contributions are welcome")
        if is_msvc(self):
            if Version(self.version) < "4.2":
                raise ConanInvalidConfiguration("MSVC support of this recipe requires at least gtk/4.2")
            if not self.dependencies["gdk-pixbuf"].options.shared:
                raise ConanInvalidConfiguration("MSVC build requires shared gdk-pixbuf")
            if not self.dependencies["cairo"].options.shared:
                raise ConanInvalidConfiguration("MSVC build requires shared cairo")
        if Version(self.version) >= "4.1.0":
            if not self.options.shared:
                raise ConanInvalidConfiguration("gtk supports only shared since 4.1.0")

    def build_requirements(self):
        self.tool_requires("meson/1.2.0")
        if self._gtk4:
            self.tool_requires("libxml2/2.11.4")  # for xmllint
        if not self.conf.get("tools.gnu:pkg_config", default=False, check_type=str):
            self.tool_requires("pkgconf/1.9.5")
        if self._gtk4:
            self.tool_requires("sassc/3.6.2")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = MesonToolchain(self)
        if self.settings.os in ["Linux", "FreeBSD"]:
            tc.project_options["wayland_backend" if self._gtk3 else "wayland-backend"] = "true" if self.options.with_wayland else "false"
            tc.project_options["x11_backend" if self._gtk3 else "x11-backend"] = "true" if self.options.with_x11 else "false"
        tc.project_options["introspection"] = "false" if self._gtk3 else "disabled"
        tc.project_options["gtk_doc"] = "false"
        tc.project_options["man-pages" if self._gtk4 else "man"] = "false"
        tc.project_options["tests" if self._gtk3 else "build-tests"] = "false"
        tc.project_options["examples" if self._gtk3 else "build-examples"] = "false"
        tc.project_options["demos"] = "false"
        tc.project_options["datadir"] = os.path.join(self.package_folder, "res", "share")
        tc.project_options["localedir"] = os.path.join(self.package_folder, "res", "share", "locale")
        tc.project_options["sysconfdir"] = os.path.join(self.package_folder, "res", "etc")

        if self._gtk4:
            enabled_disabled = lambda opt: "enabled" if opt else "disabled"
            tc.project_options["media-ffmpeg"] = enabled_disabled(self.options.with_ffmpeg)
            tc.project_options["media-gstreamer"] = enabled_disabled(self.options.with_gstreamer)
            tc.project_options["print-cups"] = enabled_disabled(self.options.with_cups)
            if Version(self.version) < "4.3.2":
                tc.project_options["print-cloudprint"] = enabled_disabled(self.options.with_cloudprint)
        tc.args.append("--wrap-mode=nofallback")
        tc.generate()

        tc = PkgConfigDeps(self)
        tc.generate()

    def _patch_sources(self):
        apply_conandata_patches(self)
        if self._gtk3:
            replace_in_file(self, os.path.join(self.source_folder, "meson.build"), "\ntest(\n", "\nfalse and test(\n")
        if "4.2.0" <= Version(self.version) < "4.6.1":
            replace_in_file(self, os.path.join(self.source_folder, "meson.build"), "gtk_update_icon_cache: true", "gtk_update_icon_cache: false")
        if "4.6.2" <= Version(self.version):
            replace_in_file(self, os.path.join(self.source_folder, "meson.build"), "dependency(is_msvc_like ? ", "dependency(false ? ")

    def build(self):
        self._patch_sources()
        meson = Meson(self)
        meson.configure()
        meson.build()

    def package(self):
        copy(self, "LICENSE", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder)
        meson = self._configure_meson()
        with environment_append(self, {"PKG_CONFIG_PATH": self.install_folder, "PATH": [os.path.join(self.package_folder, "bin")]}):
            meson.install()

        copy(self, "COPYING", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))
        rm(self, "*.pdb", os.path.join(self.package_folder, "bin"), recursive=True)
        rm(self, "*.pdb", os.path.join(self.package_folder, "lib"), recursive=True)

    def package_info(self):
        if self._gtk3:
            self.cpp_info.components["gdk-3.0"].libs = ["gdk-3"]
            self.cpp_info.components["gdk-3.0"].includedirs = [os.path.join("include", "gtk-3.0")]
            self.cpp_info.components["gdk-3.0"].requires = []
            if self.options.with_pango:
                self.cpp_info.components["gdk-3.0"].requires.extend(["pango::pango_", "pango::pangocairo"])
            self.cpp_info.components["gdk-3.0"].requires.append("gdk-pixbuf::gdk-pixbuf")
            if not is_msvc(self):
                self.cpp_info.components["gdk-3.0"].requires.extend(["cairo::cairo", "cairo::cairo-gobject"])
            if self.settings.os in ["Linux", "FreeBSD"]:
                self.cpp_info.components["gdk-3.0"].requires.extend(["glib::gio-unix-2.0", "cairo::cairo-xlib"])
                if self.options.with_x11:
                    self.cpp_info.components["gdk-3.0"].requires.append("xorg::xorg")
            self.cpp_info.components["gdk-3.0"].requires.append("libepoxy::libepoxy")
            self.cpp_info.components["gdk-3.0"].set_property("pkg_config_name", "gdk-3.0")

            self.cpp_info.components["gtk+-3.0"].libs = ["gtk-3"]
            self.cpp_info.components["gtk+-3.0"].requires = ["gdk-3.0", "atk::atk"]
            if not is_msvc(self):
                self.cpp_info.components["gtk+-3.0"].requires.extend(["cairo::cairo", "cairo::cairo-gobject"])
            self.cpp_info.components["gtk+-3.0"].requires.extend(["gdk-pixbuf::gdk-pixbuf", "glib::gio-2.0"])
            if self.settings.os in ["Linux", "FreeBSD"]:
                self.cpp_info.components["gtk+-3.0"].requires.append("at-spi2-atk::at-spi2-atk")
            self.cpp_info.components["gtk+-3.0"].requires.append("libepoxy::libepoxy")
            if self.options.with_pango:
                self.cpp_info.components["gtk+-3.0"].requires.append("pango::pangoft2")
            if self.settings.os in ["Linux", "FreeBSD"]:
                self.cpp_info.components["gtk+-3.0"].requires.append("glib::gio-unix-2.0")
            self.cpp_info.components["gtk+-3.0"].includedirs = [os.path.join("include", "gtk-3.0")]
            self.cpp_info.components["gtk+-3.0"].set_property("pkg_config_name", "gtk+-3.0")

            self.cpp_info.components["gail-3.0"].libs = ["gailutil-3"]
            self.cpp_info.components["gail-3.0"].requires = ["gtk+-3.0", "atk::atk"]
            self.cpp_info.components["gail-3.0"].includedirs = [os.path.join("include", "gail-3.0")]
            self.cpp_info.components["gail-3.0"].set_property("pkg_config_name", "gail-3.0")
        elif self._gtk4:
            self.cpp_info.set_property("pkg_config_name", "gtk4")
            self.cpp_info.libs = ["gtk-4"]
            self.cpp_info.includedirs.append(os.path.join("include", "gtk-4.0"))
