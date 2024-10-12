import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.apple import fix_apple_shared_install_name
from conan.tools.build import can_run
from conan.tools.env import VirtualBuildEnv
from conan.tools.files import copy, get, rm, rmdir
from conan.tools.gnu import PkgConfigDeps, AutotoolsToolchain, Autotools
from conan.tools.layout import basic_layout
from conan.tools.microsoft import is_msvc

required_conan_version = ">=1.53.0"


class LibXtConan(ConanFile):
    name = "libxt"
    description = "libXt: X Toolkit Intrinsics library"
    license = "MIT AND HPND-sell-variant AND SMLNJ AND MIT-open-group AND X11"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://gitlab.freedesktop.org/xorg/lib/libxt"
    topics = ("xorg", "x11")

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

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")
        self.settings.rm_safe("compiler.cppstd")
        self.settings.rm_safe("compiler.libcxx")

    def layout(self):
        basic_layout(self, src_folder="src")

    def requirements(self):
        self.requires("xorg-proto/2024.1", transitive_headers=True)
        self.requires("libx11/1.8.10", transitive_headers=True)
        self.requires("libsm/1.2.4", transitive_headers=True)
        self.requires("libice/1.1.1")

    def validate(self):
        if is_msvc(self):
            raise ConanInvalidConfiguration("MSVC is not supported.")

    def build_requirements(self):
        if not self.conf.get("tools.gnu:pkg_config", check_type=str):
            self.tool_requires("pkgconf/[>=2.2 <3]")
        if self._settings_build.os == "Windows":
            self.win_bash = True
            if not self.conf.get("tools.microsoft.bash:path", check_type=str):
                self.tool_requires("msys2/cci.latest")
        self.tool_requires("xorg-macros/1.20.0")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        VirtualBuildEnv(self).generate()
        tc = AutotoolsToolchain(self)
        tc.configure_args.extend([
            # Disable optional tools
            "--without-fop",
            "--without-perl",
            "--without-xsltproc",
            "--without-xmlto",
        ])
        if not can_run(self):
            # Skip a check that tries to run a test executable
            tc.configure_args.append("xorg_cv_malloc0_returns_null=no")
        tc.generate()
        deps = PkgConfigDeps(self)
        deps.generate()

    def build(self):
        autotools = Autotools(self)
        autotools.configure()
        autotools.make()

    def package(self):
        copy(self, "COPYING", self.source_folder, os.path.join(self.package_folder, "licenses"))
        autotools = Autotools(self)
        autotools.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))
        rmdir(self, os.path.join(self.package_folder, "share"))
        rm(self, "*.la", os.path.join(self.package_folder, "lib"))
        fix_apple_shared_install_name(self)

    def package_info(self):
        self.cpp_info.set_property("pkg_config_name", "xt")
        self.cpp_info.set_property("cmake_target_name", "X11::Xt")
        self.cpp_info.libs = ["Xt"]
        self.cpp_info.requires = [
            "xorg-proto::xorg-proto",
            "libx11::x11",
            "libice::libice",
            "libsm::libsm",
        ]

        # Copied from the generated official .pc file
        xfilesearchpath = ":".join([
            "$(sysconfdir)/X11/%L/%T/%N%C%S",
            "$(sysconfdir)/X11/%l/%T/%N%C%S",
            "$(sysconfdir)/X11/%T/%N%C%S",
            "$(sysconfdir)/X11/%L/%T/%N%S",
            "$(sysconfdir)/X11/%l/%T/%N%S",
            "$(sysconfdir)/X11/%T/%N%S",
            "$(datadir)/X11/%L/%T/%N%C%S",
            "$(datadir)/X11/%l/%T/%N%C%S",
            "$(datadir)/X11/%T/%N%C%S",
            "$(datadir)/X11/%L/%T/%N%S",
            "$(datadir)/X11/%l/%T/%N%S",
            "$(datadir)/X11/%T/%N%S",
            "$(libdir)/X11/%L/%T/%N%C%S",
            "$(libdir)/X11/%l/%T/%N%C%S",
            "$(libdir)/X11/%T/%N%C%S",
            "$(libdir)/X11/%L/%T/%N%S",
            "$(libdir)/X11/%l/%T/%N%S",
            "$(libdir)/X11/%T/%N%S",
        ])
        self.cpp_info.set_property("pkg_config_custom_content", "\n".join([
            "appdefaultdir=${prefix}/res/X11/app-defaults",
            "datarootdir=${prefix}/res",
            "errordbdir=${datarootdir}/X11",
            f"xfilesearchpath={xfilesearchpath}",
        ]))

