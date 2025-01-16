import os
import shutil
from pathlib import Path

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.env import Environment
from conan.tools.files import copy, get, rm, rmdir, export_conandata_patches, apply_conandata_patches
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
    }
    default_options = {
        "shared": False,
        "fPIC": True,
    }
    languages = ["C"]

    def export_sources(self):
        export_conandata_patches(self)

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")
        self.options["gstreamer"].shared = self.options.shared

    def layout(self):
        basic_layout(self, src_folder="src")

    def requirements(self):
        self.requires("gstreamer/1.24.11", transitive_headers=True, transitive_libs=True)
        self.requires("gst-plugins-base/1.24.11", transitive_headers=True, transitive_libs=True)
        self.requires("gst-plugins-bad/1.24.11", transitive_headers=True, transitive_libs=True, options={
            "with_nice": True,
            "with_sctp": True,
            "with_srtp": True,
            "with_ssl": "openssl",
        })
        self.requires("glib/2.78.3", transitive_headers=True, transitive_libs=True)

    def validate(self):
        if not self.dependencies["glib"].options.shared and self.options.shared:
            # https://gitlab.freedesktop.org/gstreamer/gst-build/-/issues/133
            raise ConanInvalidConfiguration("shared GStreamer cannot link to static GLib")
        if self.options.shared != self.dependencies["gstreamer"].options.shared:
            # https://gitlab.freedesktop.org/gstreamer/gst-build/-/issues/133
            raise ConanInvalidConfiguration("GStreamer and GstPlugins must be either all shared, or all static")

    def build_requirements(self):
        self.tool_requires("meson/[>=1.2.3 <2]")
        if not self.conf.get("tools.gnu:pkg_config", check_type=str):
            self.tool_requires("pkgconf/[>=2.2 <3]")
        self.tool_requires("glib/<host_version>")
        self.tool_requires("rust/1.84.0")
        self.tool_requires("cargo-c/0.10.8")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        apply_conandata_patches(self)

    def generate(self):
        tc = MesonToolchain(self)

        def feature(value):
            return "enabled" if value else "disabled"

        # audio
        tc.project_options["audiofx"] = "disabled"
        tc.project_options["claxon"] = "disabled"
        tc.project_options["csound"] = "disabled"
        tc.project_options["lewton"] = "disabled"
        tc.project_options["spotify"] = "disabled"
        tc.project_options["speechmatics"] = "disabled"

        # generic
        tc.project_options["file"] = "disabled"
        tc.project_options["originalbuffer"] = "disabled"
        tc.project_options["gopbuffer"] = "disabled"
        tc.project_options["sodium"] = "disabled"
        tc.project_options["sodium-source"] = "system"
        tc.project_options["threadshare"] = "disabled"
        tc.project_options["inter"] = "disabled"
        tc.project_options["streamgrouper"] = "disabled"

        # mux
        tc.project_options["flavors"] = "disabled"
        tc.project_options["fmp4"] = "disabled"
        tc.project_options["mp4"] = "disabled"

        # net
        tc.project_options["aws"] = "disabled"
        tc.project_options["hlssink3"] = "disabled"
        tc.project_options["mpegtslive"] = "disabled"
        tc.project_options["ndi"] = "disabled"
        tc.project_options["onvif"] = "disabled"
        tc.project_options["raptorq"] = "disabled"
        tc.project_options["reqwest"] = "disabled"
        tc.project_options["relationmeta"] = "disabled"
        tc.project_options["rtsp"] = "disabled"
        tc.project_options["rtp"] = "enabled"
        tc.project_options["webrtc"] = "enabled"
        tc.project_options["webrtchttp"] = "disabled"
        tc.project_options["quinn"] = "disabled"

        # text
        tc.project_options["textahead"] = "disabled"
        tc.project_options["json"] = "disabled"
        tc.project_options["regex"] = "disabled"
        tc.project_options["textwrap"] = "disabled"

        # utils
        tc.project_options["fallbackswitch"] = "disabled"
        tc.project_options["livesync"] = "disabled"
        tc.project_options["togglerecord"] = "disabled"
        tc.project_options["tracers"] = "disabled"
        tc.project_options["uriplaylistbin"] = "disabled"

        # video
        tc.project_options["cdg"] = "disabled"
        tc.project_options["closedcaption"] = "disabled"
        tc.project_options["dav1d"] = "disabled"
        tc.project_options["ffv1"] = "disabled"
        tc.project_options["gif"] = "disabled"
        tc.project_options["gtk4"] = "disabled"
        tc.project_options["hsv"] = "disabled"
        tc.project_options["png"] = "disabled"
        tc.project_options["rav1e"] = "disabled"
        tc.project_options["videofx"] = "disabled"
        tc.project_options["webp"] = "disabled"

        # Common options
        tc.project_options["doc"] = "disabled"
        tc.project_options["examples"] = "disabled"
        tc.project_options["tests"] = "disabled"

        tc.generate()

        deps = PkgConfigDeps(self)
        deps.generate()

        env = Environment()
        # Ensure the correct linker is used, especially when cross-compiling
        target_upper = self.conf.get("user.rust:target_host", check_type=str).upper().replace("-", "_")
        cc = GnuToolchain(self).extra_env.vars(self)["CC"]
        env.define_path(f"CARGO_TARGET_{target_upper}_LINKER", cc)
        # Don't add the Cargo dependencies to a global Cargo cache
        env.define_path("CARGO_HOME", os.path.join(self.build_folder, "cargo"))
        env.vars(self).save_script("cargo_paths")

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

        _define_plugin("rsrtp", [])

        _define_plugin("rswebrtc", [
            "gst-plugins-bad::gstreamer-webrtc-1.0",
            "gst-plugins-base::gstreamer-audio-1.0",
            "gst-plugins-base::gstreamer-video-1.0",
            "gst-plugins-base::gstreamer-app-1.0",
            "gst-plugins-base::gstreamer-rtp-1.0",
            "gst-plugins-base::gstreamer-sdp-1.0",
            "gstreamer::gstreamer-net-1.0",
        ])
