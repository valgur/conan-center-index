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


class GStPluginsRsConan(ConanFile):
    name = "gst-plugins-rs"
    description = "GStreamer plugins written in Rust"
    license = "LGPL-2.1-or-later"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://gitlab.freedesktop.org/gstreamer/gst-plugins-rs"
    topics = ("gstreamer", "multimedia", "video", "audio", "broadcasting", "framework", "media")

    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],

        # audio
        "audiofx": [True, False],
        "claxon": [True, False],
        "csound": [True, False],
        "lewton": [True, False],
        "spotify": [True, False],
        "speechmatics": [True, False],

        # generic
        "file": [True, False],
        "originalbuffer": [True, False],
        "gopbuffer": [True, False],
        "sodium": [True, False],
        "threadshare": [True, False],
        "inter": [True, False],
        "streamgrouper": [True, False],

        # mux
        "flavors": [True, False],
        "fmp4": [True, False],
        "mp4": [True, False],

        # net
        "aws": [True, False],
        "hlssink3": [True, False],
        "mpegtslive": [True, False],
        "ndi": [True, False],
        "onvif": [True, False],
        "raptorq": [True, False],
        "reqwest": [True, False],
        "relationmeta": [True, False],
        "rtsp": [True, False],
        "rtp": [True, False],
        "webrtc": [True, False],
        "webrtchttp": [True, False],
        "quinn": [True, False],

        # text
        "textahead": [True, False],
        "json": [True, False],
        "regex": [True, False],
        "textwrap": [True, False],

        # utils
        "fallbackswitch": [True, False],
        "livesync": [True, False],
        "togglerecord": [True, False],
        "tracers": [True, False],
        "uriplaylistbin": [True, False],

        # video
        "cdg": [True, False],
        "closedcaption": [True, False],
        "dav1d": [True, False],
        "ffv1": [True, False],
        "gif": [True, False],
        "gtk4": [True, False],
        "hsv": [True, False],
        "png": [True, False],
        "rav1e": [True, False],
        "videofx": [True, False],
        "webp": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,

        # audio
        "audiofx": False,
        "claxon": False,
        "csound": False,
        "lewton": False,
        "spotify": False,
        "speechmatics": False,

        # generic
        "file": False,
        "originalbuffer": False,
        "gopbuffer": False,
        "sodium": False,
        "threadshare": False,
        "inter": False,
        "streamgrouper": False,

        # mux
        "flavors": False,
        "fmp4": False,
        "mp4": False,

        # net
        "aws": False,
        "hlssink3": False,
        "mpegtslive": False,
        "ndi": False,
        "onvif": False,
        "raptorq": False,
        "reqwest": False,
        "relationmeta": False,
        "rtsp": True,
        "rtp": True,
        "webrtc": False,
        "webrtchttp": False,
        "quinn": False,

        # text
        "textahead": False,
        "json": False,
        "regex": False,
        "textwrap": False,

        # utils
        "fallbackswitch": False,
        "livesync": False,
        "togglerecord": False,
        "tracers": False,
        "uriplaylistbin": False,

        # video
        "cdg": False,
        "closedcaption": False,
        "dav1d": False,
        "ffv1": False,
        "gif": False,
        "gtk4": False,
        "hsv": False,
        "png": False,
        "rav1e": False,
        "videofx": False,
        "webp": False,
    }
    languages = ["C"]

    @property
    def _bad(self):
        return self.dependencies["gst-plugins-bad"].options

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

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

    @property
    def _need_plugins_base(self):
        return [
            "audiofx",
            "aws",
            "cdg",
            "claxon",
            "closedcaption",
            "dav1d",
            "fallbackswitch",
            "ffv1",
            "flv",
            "fmp4",
            "gif",
            "gtk4",
            "hlssink3",
            "hsv",
            "inter",
            "lewton",
            "livesync",
            "mp4",
            "ndi",
            "onvif",
            "originalbuffer",
            "png",
            "raptorq",
            "rav1e",
            "relationmeta",
            "rtp",
            "rtsp",
            "speechmatics",
            "threadshare",
            "togglerecord",
            "videofx",
            "webp",
            "webrtc",
        ]

    def requirements(self):
        self.requires("gstreamer/1.24.11", transitive_headers=True, transitive_libs=True)
        if any(self.options.get_safe(opt) for opt in self._need_plugins_base):
            self.requires("gst-plugins-base/1.24.11", transitive_headers=True, transitive_libs=True)
        if self.options.relationmeta or self.options.webrtc or self.options.webrtchttp:
            self.requires("gst-plugins-bad/1.24.11", transitive_headers=True, transitive_libs=True)
        self.requires("glib/2.78.3", transitive_headers=True, transitive_libs=True)

        if self.options.closedcaption or self.options.videofx:
            self.requires("cairo/1.18.0")
        if self.options.dav1d:
            self.requires("dav1d/1.4.3")
        if self.options.gtk4:
            self.requires("gtk/4.15.6")
        if self.options.aws or self.options.reqwest or self.options.speechmatics:
            self.requires("openssl/[>=1.1 <4]")
        if self.options.closedcaption or self.options.onvif:
            self.requires("pango/1.54.0", options={"with_cairo": True})
        if self.options.sodium:
            self.requires("libsodium/1.0.20")
        if self.options.webp:
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

        def feature(value):
            return "enabled" if value else "disabled"

        # audio
        tc.project_options["audiofx"] = feature(self.options.audiofx)
        tc.project_options["claxon"] = feature(self.options.claxon)
        tc.project_options["csound"] = feature(self.options.csound)
        tc.project_options["lewton"] = feature(self.options.lewton)
        tc.project_options["spotify"] = feature(self.options.spotify)
        tc.project_options["speechmatics"] = feature(self.options.speechmatics)

        # generic
        tc.project_options["file"] = feature(self.options.file)
        tc.project_options["originalbuffer"] = feature(self.options.originalbuffer)
        tc.project_options["gopbuffer"] = feature(self.options.gopbuffer)
        tc.project_options["sodium"] = feature(self.options.sodium)
        tc.project_options["sodium-source"] = "system"
        tc.project_options["threadshare"] = feature(self.options.threadshare)
        tc.project_options["inter"] = feature(self.options.inter)
        tc.project_options["streamgrouper"] = feature(self.options.streamgrouper)

        # mux
        tc.project_options["flavors"] = feature(self.options.flavors)
        tc.project_options["fmp4"] = feature(self.options.fmp4)
        tc.project_options["mp4"] = feature(self.options.mp4)

        # net
        tc.project_options["aws"] = feature(self.options.aws)
        tc.project_options["hlssink3"] = feature(self.options.hlssink3)
        tc.project_options["mpegtslive"] = feature(self.options.mpegtslive)
        tc.project_options["ndi"] = feature(self.options.ndi)
        tc.project_options["onvif"] = feature(self.options.onvif)
        tc.project_options["raptorq"] = feature(self.options.raptorq)
        tc.project_options["reqwest"] = feature(self.options.reqwest)
        tc.project_options["relationmeta"] = feature(self.options.relationmeta)
        tc.project_options["rtsp"] = feature(self.options.rtsp)
        tc.project_options["rtp"] = feature(self.options.rtp)
        tc.project_options["webrtc"] = feature(self.options.webrtc)
        tc.project_options["webrtchttp"] = feature(self.options.webrtchttp)
        tc.project_options["quinn"] = feature(self.options.quinn)

        # text
        tc.project_options["textahead"] = feature(self.options.textahead)
        tc.project_options["json"] = feature(self.options.json)
        tc.project_options["regex"] = feature(self.options.regex)
        tc.project_options["textwrap"] = feature(self.options.textwrap)

        # utils
        tc.project_options["fallbackswitch"] = feature(self.options.fallbackswitch)
        tc.project_options["livesync"] = feature(self.options.livesync)
        tc.project_options["togglerecord"] = feature(self.options.togglerecord)
        tc.project_options["tracers"] = feature(self.options.tracers)
        tc.project_options["uriplaylistbin"] = feature(self.options.uriplaylistbin)

        # video
        tc.project_options["cdg"] = feature(self.options.cdg)
        tc.project_options["closedcaption"] = feature(self.options.closedcaption)
        tc.project_options["dav1d"] = feature(self.options.dav1d)
        tc.project_options["ffv1"] = feature(self.options.ffv1)
        tc.project_options["gif"] = feature(self.options.gif)
        tc.project_options["gtk4"] = feature(self.options.gtk4)
        tc.project_options["hsv"] = feature(self.options.hsv)
        tc.project_options["png"] = feature(self.options.png)
        tc.project_options["rav1e"] = feature(self.options.rav1e)
        tc.project_options["videofx"] = feature(self.options.videofx)
        tc.project_options["webp"] = feature(self.options.webp)

        # Common options
        tc.project_options["doc"] = "disabled"
        tc.project_options["examples"] = "disabled"
        tc.project_options["tests"] = "disabled"

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
            opt = name if not name.startswith("rs") else name[2:]
            if not self.options.get_safe(opt):
                return
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

        _define_plugin("aws", [
            "gst-plugins-base::gstreamer-audio-1.0",
            "gst-plugins-base::gstreamer-video-1.0",
            "openssl::openssl",
        ])

        _define_plugin("cdg", [
            "gst-plugins-base::gstreamer-video-1.0",
        ])

        _define_plugin("claxon", [
            "gst-plugins-base::gstreamer-audio-1.0",
        ])

        _define_plugin("dav1d", [
            "gst-plugins-base::gstreamer-video-1.0",
            "dav1d::dav1d",
        ])

        _define_plugin("fallbackswitch", [
            "gst-plugins-base::gstreamer-audio-1.0",
            "gst-plugins-base::gstreamer-video-1.0",
        ])

        _define_plugin("ffv1", [
            "gst-plugins-base::gstreamer-video-1.0",
        ])

        _define_plugin("fmp4", [
            "gst-plugins-base::gstreamer-audio-1.0",
            "gst-plugins-base::gstreamer-video-1.0",
            "gst-plugins-base::gstreamer-pbutils-1.0",
        ])

        _define_plugin("gif", [
            "gst-plugins-base::gstreamer-video-1.0",
        ])

        _define_plugin("gopbuffer", [])

        _define_plugin("gtk4", [
            "gst-plugins-base::gstreamer-video-1.0",
            "gst-plugins-base::gstreamer-allocators-1.0",
            "gst-plugins-base::gstreamer-gl-1.0",
            "gtk::gtk4",
        ])

        _define_plugin("hlssink3", [
            "gst-plugins-base::gstreamer-app-1.0",
        ])

        _define_plugin("hsv", [
            "gst-plugins-base::gstreamer-video-1.0",
        ])

        _define_plugin("json", [])

        _define_plugin("lewton", [
            "gst-plugins-base::gstreamer-audio-1.0",
        ])

        _define_plugin("livesync", [
            "gst-plugins-base::gstreamer-audio-1.0",
        ])

        _define_plugin("mp4", [
            "gst-plugins-base::gstreamer-audio-1.0",
            "gst-plugins-base::gstreamer-video-1.0",
            "gst-plugins-base::gstreamer-pbutils-1.0",
        ])

        _define_plugin("mpegtslive", [])

        _define_plugin("ndi", [
            "gst-plugins-base::gstreamer-audio-1.0",
            "gst-plugins-base::gstreamer-video-1.0",
        ])

        _define_plugin("originalbuffer", [
            "gst-plugins-base::gstreamer-video-1.0",
        ])

        _define_plugin("quinn", [])

        _define_plugin("raptorq", [
            "gst-plugins-base::gstreamer-rtp-1.0",
        ])

        _define_plugin("rav1e", [
            "gst-plugins-base::gstreamer-video-1.0",
        ])

        _define_plugin("regex", [])

        _define_plugin("reqwest", [
            "openssl::openssl",
        ])

        _define_plugin("rsaudiofx", [
            "gst-plugins-base::gstreamer-audio-1.0",
        ])

        _define_plugin("rsclosedcaption", [
            "gst-plugins-base::gstreamer-video-1.0",
            "pango::pango-1.0",
            "pango::pangocairo-1.0",
            "cairo::cairo-gobject",
        ])

        _define_plugin("rsfile", [])

        _define_plugin("rsflv", [
            "gst-plugins-base::gstreamer-audio-1.0",
        ])

        _define_plugin("rsinter", [
            "gst-plugins-base::gstreamer-video-1.0",
            "gst-plugins-base::gstreamer-app-1.0",
        ])

        _define_plugin("rsonvif", [
            "gst-plugins-base::gstreamer-video-1.0",
            "gst-plugins-base::gstreamer-rtp-1.0",
            "pango::pango-1.0",
            "pango::pangocairo-1.0",
        ])

        _define_plugin("rspng", [
            "gst-plugins-base::gstreamer-video-1.0",
        ])

        _define_plugin("rsrelationmeta", [
            "gst-plugins-base::gstreamer-video-1.0",
            "gst-plugins-bad::gstreamer-analytics-1.0",
        ])

        _define_plugin("rsrtp", [
            "gst-plugins-base::gstreamer-video-1.0",
            "gst-plugins-base::gstreamer-rtp-1.0",
            "gstreamer::gstreamer-net-1.0",
        ])

        _define_plugin("rsrtsp", [
            "gst-plugins-base::gstreamer-app-1.0",
            "gst-plugins-base::gstreamer-pbutils-1.0",
            "gstreamer::gstreamer-net-1.0",
        ])

        _define_plugin("rstracers", [])

        _define_plugin("rsvideofx", [
            "gst-plugins-base::gstreamer-video-1.0",
            "cairo::cairo-gobject",
        ])

        _define_plugin("rswebp", [
            "gst-plugins-base::gstreamer-video-1.0",
            "libwebp::webpdemux",
        ])

        _define_plugin("rswebrtc", [
            "gst-plugins-bad::gstreamer-webrtc-1.0",
            "gst-plugins-base::gstreamer-audio-1.0",
            "gst-plugins-base::gstreamer-video-1.0",
            "gst-plugins-base::gstreamer-app-1.0",
            "gst-plugins-base::gstreamer-rtp-1.0",
            "gst-plugins-base::gstreamer-sdp-1.0",
            "gstreamer::gstreamer-net-1.0",
        ])

        _define_plugin("sodium", [
            "libsodium::libsodium",
        ])

        _define_plugin("speechmatics", [
            "gst-plugins-base::gstreamer-audio-1.0",
            "openssl::openssl",
        ])

        _define_plugin("spotify", [])

        _define_plugin("streamgrouper", [])

        _define_plugin("textahead", [])

        _define_plugin("textwrap", [])

        _define_plugin("threadshare", [
            "gst-plugins-base::gstreamer-audio-1.0",
            "gst-plugins-base::gstreamer-rtp-1.0",
            "gstreamer::gstreamer-net-1.0",
        ])

        _define_plugin("togglerecord", [
            "gst-plugins-base::gstreamer-audio-1.0",
            "gst-plugins-base::gstreamer-video-1.0",
        ])

        _define_plugin("uriplaylistbin", [])

        _define_plugin("webrtchttp", [
            "gst-plugins-bad::gstreamer-webrtc-1.0",
        ])
