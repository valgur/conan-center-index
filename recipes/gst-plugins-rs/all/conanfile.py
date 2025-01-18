import os
import shutil
from pathlib import Path

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import cross_building
from conan.tools.env import Environment
from conan.tools.files import copy, get, rm, rmdir, replace_in_file
from conan.tools.gnu import PkgConfigDeps, GnuToolchain
from conan.tools.layout import basic_layout
from conan.tools.meson import MesonToolchain, Meson
from conan.tools.microsoft import is_msvc

required_conan_version = ">=2.4"


def _option_name(name):
    if name.startswith("rs"):
        name = name[2:]
    return {
        "flv": "flavors",
    }.get(name, name)


class GStPluginsRsConan(ConanFile):
    name = "gst-plugins-rs"
    description = "GStreamer plugins written in Rust"
    license = "LGPL-2.1-or-later"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://gitlab.freedesktop.org/gstreamer/gst-plugins-rs"
    topics = ("gstreamer", "multimedia", "video", "audio", "broadcasting", "framework", "media")

    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"

    _plugins = {
        "aws": [
            "gst-plugins-base::gstreamer-audio-1.0",
            "gst-plugins-base::gstreamer-video-1.0",
            "openssl::openssl",
        ],
        "cdg": [
            "gst-plugins-base::gstreamer-video-1.0",
        ],
        "claxon": [
            "gst-plugins-base::gstreamer-audio-1.0",
        ],
        "dav1d": [
            "gst-plugins-base::gstreamer-video-1.0",
            "dav1d::dav1d",
        ],
        "fallbackswitch": [
            "gst-plugins-base::gstreamer-audio-1.0",
            "gst-plugins-base::gstreamer-video-1.0",
        ],
        "ffv1": [
            "gst-plugins-base::gstreamer-video-1.0",
        ],
        "fmp4": [
            "gst-plugins-base::gstreamer-audio-1.0",
            "gst-plugins-base::gstreamer-video-1.0",
            "gst-plugins-base::gstreamer-pbutils-1.0",
        ],
        "gif": [
            "gst-plugins-base::gstreamer-video-1.0",
        ],
        "gopbuffer": [],
        "gtk4": [
            "gst-plugins-base::gstreamer-video-1.0",
            "gst-plugins-base::gstreamer-allocators-1.0",
            "gst-plugins-base::gstreamer-gl-1.0",
            "gtk::gtk4",
        ],
        "hlssink3": [
            "gst-plugins-base::gstreamer-app-1.0",
        ],
        "hsv": [
            "gst-plugins-base::gstreamer-video-1.0",
        ],
        "json": [],
        "lewton": [
            "gst-plugins-base::gstreamer-audio-1.0",
        ],
        "livesync": [
            "gst-plugins-base::gstreamer-audio-1.0",
        ],
        "mp4": [
            "gst-plugins-base::gstreamer-audio-1.0",
            "gst-plugins-base::gstreamer-video-1.0",
            "gst-plugins-base::gstreamer-pbutils-1.0",
        ],
        "mpegtslive": [],
        "ndi": [
            "gst-plugins-base::gstreamer-audio-1.0",
            "gst-plugins-base::gstreamer-video-1.0",
        ],
        "originalbuffer": [
            "gst-plugins-base::gstreamer-video-1.0",
        ],
        "quinn": [],
        "raptorq": [
            "gst-plugins-base::gstreamer-rtp-1.0",
        ],
        "rav1e": [
            "gst-plugins-base::gstreamer-video-1.0",
        ],
        "regex": [],
        "reqwest": [
            "openssl::openssl",
        ],
        "rsaudiofx": [
            "gst-plugins-base::gstreamer-audio-1.0",
        ],
        "rsclosedcaption": [
            "gst-plugins-base::gstreamer-video-1.0",
            "pango::pango-1.0",
            "pango::pangocairo-1.0",
            "cairo::cairo-gobject",
        ],
        "rsfile": [],
        "rsflv": [
            "gst-plugins-base::gstreamer-audio-1.0",
        ],
        "rsinter": [
            "gst-plugins-base::gstreamer-video-1.0",
            "gst-plugins-base::gstreamer-app-1.0",
        ],
        "rsonvif": [
            "gst-plugins-base::gstreamer-video-1.0",
            "gst-plugins-base::gstreamer-rtp-1.0",
            "pango::pango-1.0",
            "pango::pangocairo-1.0",
        ],
        "rspng": [
            "gst-plugins-base::gstreamer-video-1.0",
        ],
        "rsrelationmeta": [
            "gst-plugins-base::gstreamer-video-1.0",
            "gst-plugins-bad::gstreamer-analytics-1.0",
        ],
        "rsrtp": [
            "gst-plugins-base::gstreamer-video-1.0",
            "gst-plugins-base::gstreamer-rtp-1.0",
            "gstreamer::gstreamer-net-1.0",
        ],
        "rsrtsp": [
            "gst-plugins-base::gstreamer-app-1.0",
            "gst-plugins-base::gstreamer-pbutils-1.0",
            "gstreamer::gstreamer-net-1.0",
        ],
        "rstracers": [],
        "rsvideofx": [
            "gst-plugins-base::gstreamer-video-1.0",
            "cairo::cairo-gobject",
        ],
        "rswebp": [
            "gst-plugins-base::gstreamer-video-1.0",
            "libwebp::webpdemux",
        ],
        "rswebrtc": [
            "gst-plugins-bad::gstreamer-webrtc-1.0",
            "gst-plugins-base::gstreamer-audio-1.0",
            "gst-plugins-base::gstreamer-video-1.0",
            "gst-plugins-base::gstreamer-app-1.0",
            "gst-plugins-base::gstreamer-rtp-1.0",
            "gst-plugins-base::gstreamer-sdp-1.0",
            "gstreamer::gstreamer-net-1.0",
        ],
        "sodium": [
            "libsodium::libsodium",
        ],
        "speechmatics": [
            "gst-plugins-base::gstreamer-audio-1.0",
            "openssl::openssl",
        ],
        "spotify": [],
        "streamgrouper": [],
        "textahead": [],
        "textwrap": [],
        "threadshare": [
            "gst-plugins-base::gstreamer-audio-1.0",
            "gst-plugins-base::gstreamer-rtp-1.0",
            "gstreamer::gstreamer-net-1.0",
        ],
        "togglerecord": [
            "gst-plugins-base::gstreamer-audio-1.0",
            "gst-plugins-base::gstreamer-video-1.0",
        ],
        "uriplaylistbin": [],
        "webrtchttp": [
            "gst-plugins-bad::gstreamer-webrtc-1.0",
        ],
    }

    options = {
        "shared": [True, False],
        "fPIC": [True, False],

        **{_option_name(name): [True, False] for name in _plugins if _option_name(name)},
    }
    default_options = {
        "shared": False,
        "fPIC": True,

        **{_option_name(name): False for name in _plugins if _option_name(name)},
    }

    languages = ["C"]

    @property
    def _bad(self):
        return self.dependencies["gst-plugins-bad"].options

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC
        # Enable some more commonly useful plugins, so we have something to build by default
        self.options.rtp = True
        self.options.rtsp = True

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")
        self.options["gstreamer"].shared = self.options.shared
        if self.options.webrtc:
            self.options["gst-plugins-bad"].with_srtp = True
            self.options["gst-plugins-bad"].with_nice = True
            self.options["gst-plugins-bad"].with_sctp = True
            self.options["gst-plugins-bad"].with_ssl = "openssl"
            self.options.rtp = True

    def layout(self):
        basic_layout(self)

    def _is_enabled(self, plugin):
        return self.options.get_safe(_option_name(plugin), False)

    @property
    def _plugin_reqs(self):
        requires = set()
        for plugin, plugin_requires in self._plugins.items():
            if self._is_enabled(plugin):
                requires.update({req.split("::")[0] for req in plugin_requires})
        return requires

    def requirements(self):
        reqs = self._plugin_reqs
        self.requires("gstreamer/1.24.11", transitive_headers=True, transitive_libs=True)
        self.requires("glib/2.78.3", transitive_headers=True, transitive_libs=True)
        if "gst-plugins-base" in reqs:
            self.requires("gst-plugins-base/1.24.11", transitive_headers=True, transitive_libs=True)
        if "gst-plugins-bad" in reqs:
            self.requires("gst-plugins-bad/1.24.11", transitive_headers=True, transitive_libs=True)

        if "cairo" in reqs:
            self.requires("cairo/1.18.0")
        if "dav1d" in reqs:
            self.requires("dav1d/1.4.3")
        if "gtk" in reqs:
            self.requires("gtk/4.15.6")
        if "openssl" in reqs:
            self.requires("openssl/[>=1.1 <4]")
        if "pango" in reqs:
            self.requires("pango/1.54.0", options={"with_cairo": True})
        if "libsodium" in reqs:
            self.requires("libsodium/1.0.20")
        if "libwebp" in reqs:
            self.requires("libwebp/1.3.2")

    def validate(self):
        if not self.dependencies["glib"].options.shared and self.options.shared:
            # https://gitlab.freedesktop.org/gstreamer/gst-build/-/issues/133
            raise ConanInvalidConfiguration("shared GStreamer cannot link to static GLib")
        if self.options.shared != self.dependencies["gstreamer"].options.shared:
            # https://gitlab.freedesktop.org/gstreamer/gst-build/-/issues/133
            raise ConanInvalidConfiguration("GStreamer and GstPlugins must be either all shared, or all static")
        if self.options.webrtc and not self.options.rtp:
            raise ConanInvalidConfiguration("webrtc option requires rtp option to be enabled")

    def build_requirements(self):
        self.tool_requires("meson/[>=1.2.3 <2]")
        if not self.conf.get("tools.gnu:pkg_config", check_type=str):
            self.tool_requires("pkgconf/[>=2.2 <3]")
        self.tool_requires("glib/<host_version>")
        self.tool_requires("rust/1.84.0")
        self.tool_requires("cargo-c/[^0.10]")
        if self.options.rav1e:
            self.tool_requires("nasm/[^2]")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def _define_rust_env(self, env, scope="host", cflags=None):
        target = self.conf.get(f"user.rust:target_{scope}", check_type=str).replace("-", "_")
        cc = GnuToolchain(self).extra_env.vars(self)["CC" if scope == "host" else "CC_FOR_BUILD"]
        env.define_path(f"CARGO_TARGET_{target.upper()}_LINKER", cc)
        env.define_path(f"CC_{target}", cc)
        if cflags:
            env.append(f"CFLAGS_{target}", cflags)

    def generate(self):
        env = Environment()
        self._define_rust_env(env, "host")
        if cross_building(self):
            self._define_rust_env(env, "build")
        env.define_path("CARGO_HOME", os.path.join(self.build_folder, "cargo"))
        env.vars(self).save_script("cargo_paths")

        tc = MesonToolchain(self)
        for plugin in self._plugins:
            opt = _option_name(plugin)
            tc.project_options[opt] = "enabled" if self.options.get_safe(opt) else "disabled"
        tc.project_options["doc"] = "disabled"
        tc.project_options["examples"] = "disabled"
        tc.project_options["tests"] = "disabled"
        tc.project_options["sodium-source"] = "system"
        tc.generate()
        rust_target = self.conf.get(f"user.rust:target_host", check_type=str)
        replace_in_file(self, "conan_meson_cross.ini",
                        "[binaries]",
                        f"[binaries]\nrust = ['rustc', '--target', '{rust_target}']")

        deps = PkgConfigDeps(self)
        deps.generate()

    def build(self):
        meson = Meson(self)
        meson.configure()
        meson.build()

    def _fix_library_names(self, path):
        if is_msvc(self):
            for filename_old in Path(path).glob("*.a"):
                filename_new = str(filename_old)[:-2] + ".lib"
                shutil.move(filename_old, filename_new)

    def package(self):
        copy(self, "LICENSE-*", self.source_folder, os.path.join(self.package_folder, "licenses"))
        meson = Meson(self)
        meson.install()
        self._fix_library_names(os.path.join(self.package_folder, "lib"))
        self._fix_library_names(os.path.join(self.package_folder, "lib", "gstreamer-1.0"))
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))
        rmdir(self, os.path.join(self.package_folder, "lib", "gstreamer-1.0", "pkgconfig"))
        rm(self, "*.pdb", self.package_folder, recursive=True)

    def package_info(self):
        gst_plugins = []

        if self.options.shared:
            self.runenv_info.define_path("GST_PLUGIN_PATH", os.path.join(self.package_folder, "lib", "gstreamer-1.0"))

        def _define_plugin(name, extra_requires):
            name = f"gst{name}"
            component = self.cpp_info.components[name]
            component.requires = [
                "gstreamer::gstreamer-1.0",
                "gstreamer::gstreamer-base-1.0",
                "glib::gobject-2.0",
                "glib::glib-2.0",
                "glib::gio-2.0",
            ] + extra_requires
            component.includedirs = []
            component.bindirs = []
            component.resdirs = ["res"]
            if self.options.shared:
                component.bindirs.append(os.path.join("lib", "gstreamer-1.0"))
            else:
                component.libs = [name]
                component.libdirs = [os.path.join("lib", "gstreamer-1.0")]
                if self.settings.os in ["Linux", "FreeBSD"]:
                    component.system_libs = ["m"]
            gst_plugins.append(name)
            return component

        for plugin, plugin_requires in self._plugins.items():
            if self._is_enabled(plugin):
                _define_plugin(plugin, plugin_requires)
