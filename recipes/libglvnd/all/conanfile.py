from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.files import get, rmdir, save
from conan.tools.env import VirtualBuildEnv
from conan.tools.gnu import PkgConfigDeps
from conan.tools.layout import basic_layout
from conan.tools.meson import Meson, MesonToolchain
import os
import textwrap

required_conan_version = ">=1.64.0 <2 || >=2.2.0"

class LibGlvndConan(ConanFile):
    name = "libglvnd"
    description = "The GL Vendor-Neutral Dispatch library"
    license = "MIT"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://gitlab.freedesktop.org/glvnd/libglvnd"
    topics = ("dispatch", "egl", "gl", "gles", "glx", "glvnd", "opengl", "vendor-neutral")
    settings = "os", "arch", "compiler", "build_type"
    package_type = "shared-library"
    options = {
        "asm": [True, False],
        "x11": [True, False],
        "egl": [True, False],
        "glx": [True, False],
        "gles1": [True, False],
        "gles2": [True, False],
        "tls": [True, False],
        "dispatch_tls": [True, False],
        "headers": [True, False],
        "entrypoint_patching": [True, False],
    }
    default_options = {
        "asm" : True,
        "x11": True,
        "egl": True,
        "glx": True,
        "gles1": True,
        "gles2": True,
        "tls": True,
        "dispatch_tls": True,
        "headers": True,
        "entrypoint_patching": True,
    }

    def configure(self):
        self.settings.rm_safe("compiler.cppstd")
        self.settings.rm_safe("compiler.libcxx")

    def requirements(self):
        if self.options.x11:
            self.requires("xorg/system")
        if self.options.glx:
            self.requires("xorg-proto/2022.2")

    def validate(self):
        if self.settings.os not in ['Linux', 'FreeBSD']:
            raise ConanInvalidConfiguration(f"{self.name} is only compatible with Linux and FreeBSD")

    def build_requirements(self):
        self.tool_requires("meson/[>=1.2.3 <2]")
        if not self.conf.get("tools.gnu:pkg_config", default=False, check_type=str):
            self.tool_requires("pkgconf/[>=2.2 <3]")

    def layout(self):
        basic_layout(self, src_folder="src")

    def source(self):
        get(self, **self.conan_data["sources"][self.version],
                  strip_root=True)

    def generate(self):
        virtual_build_env = VirtualBuildEnv(self)
        virtual_build_env.generate()
        pkg_config_deps = PkgConfigDeps(self)
        pkg_config_deps.generate()
        tc = MesonToolchain(self)
        tc.project_options["asm"] = "enabled" if self.options.asm else "disabled"
        tc.project_options["x11"] = "enabled" if self.options.x11 else "disabled"
        tc.project_options["egl"] = self.options.egl
        tc.project_options["glx"] = "enabled" if self.options.glx else "disabled"
        tc.project_options["gles1"] = self.options.gles1
        tc.project_options["gles2"] = self.options.gles2
        tc.project_options["tls"] = self.options.tls
        tc.project_options["dispatch-tls"] = self.options.dispatch_tls
        tc.project_options["headers"] = self.options.headers
        tc.project_options["entrypoint-patching"] = "enabled" if self.options.entrypoint_patching else "disabled"
        tc.project_options["libdir"] = "lib"
        # Configure the data directory so that it defaults to the correct location for ICD discovery on the local system.
        tc.project_options["datadir"] = os.path.join("usr", "share") if self.settings.os == "Linux" else os.path.join("usr", "local", "share")
        if self.settings.os == "FreeBSD":
            tc.project_options["sysconfdir"] = os.path.join("usr", "local", "etc")
        tc.generate()

    def build(self):
        meson = Meson(self)
        meson.configure()
        meson.build()

    def package(self):
        meson = Meson(self)
        meson.install()

        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))
        rmdir(self, os.path.join(self.package_folder, "share"))

        save(self, os.path.join(self.package_folder, "licenses", "LICENSE"), textwrap.dedent('''\
            Copyright (c) 2013, NVIDIA CORPORATION.

            Permission is hereby granted, free of charge, to any person obtaining a
            copy of this software and/or associated documentation files (the
            "Materials"), to deal in the Materials without restriction, including
            without limitation the rights to use, copy, modify, merge, publish,
            distribute, sublicense, and/or sell copies of the Materials, and to
            permit persons to whom the Materials are furnished to do so, subject to
            the following conditions:

            The above copyright notice and this permission notice shall be included
            unaltered in all copies or substantial portions of the Materials.
            Any additions, deletions, or changes to the original source files
            must be clearly indicated in accompanying documentation.

            THE MATERIALS ARE PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
            EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
            MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
            IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
            CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
            TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
            MATERIALS OR THE USE OR OTHER DEALINGS IN THE MATERIALS.
            '''))

    def package_info(self):
        self.cpp_info.components['gldispatch'].libs = ["GLdispatch"]
        self.cpp_info.components['gldispatch'].system_libs.extend(["pthread", "dl"])

        self.cpp_info.components['opengl'].libs = ["OpenGL"]
        self.cpp_info.components['opengl'].requires.extend(["gldispatch"])
        self.cpp_info.components['opengl'].set_property("pkg_config_name", "opengl")

        if self.options.egl:
            self.cpp_info.components['egl'].libs = ["EGL"]
            self.cpp_info.components['egl'].system_libs.extend(["pthread", "dl", "m"])
            self.cpp_info.components['egl'].requires.append("gldispatch")
            if self.options.x11:
                self.cpp_info.components['egl'].requires.append("xorg::x11")
            self.cpp_info.components['egl'].set_property("pkg_config_name", "egl")

        if self.options.glx:
            self.cpp_info.components['glx'].libs = ["GLX"]
            self.cpp_info.components['glx'].system_libs.extend(["dl"])
            self.cpp_info.components['glx'].requires.extend(["xorg::x11", "xorg::xext", "xorg-proto::glproto", "gldispatch"])
            self.cpp_info.components['glx'].set_property("pkg_config_name", "glx")

            self.cpp_info.components['gl'].libs = ["GL"]
            self.cpp_info.components['gl'].system_libs.extend(["dl"])
            self.cpp_info.components['gl'].requires.extend(["xorg::x11", "glx", "gldispatch"])
            self.cpp_info.components['gl'].set_property("pkg_config_name", "gl")

        if self.options.gles1:
            self.cpp_info.components['gles1'].libs = ["GLESv1_CM"]
            self.cpp_info.components['gles1'].requires.extend(["gldispatch"])
            self.cpp_info.components['gles1'].set_property("pkg_config_name", "glesv1_cm")

        if self.options.gles2:
            self.cpp_info.components['gles2'].libs = ["GLESv2"]
            self.cpp_info.components['gles2'].requires.extend(["gldispatch"])
            self.cpp_info.components['gles2'].set_property("pkg_config_name", "glesv2")
