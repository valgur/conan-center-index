import os

from conan import ConanFile
from conan.tools.files import *
from conan.tools.layout import basic_layout

required_conan_version = ">=2.1"


class XcbProtoConan(ConanFile):
    name = "xcb-proto"
    description = "XML-XCB protocol descriptions used by libxcb for the X11 protocol & extensions"
    license = "X11-distribute-modifications-variant"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://gitlab.freedesktop.org/xorg/proto/xcbproto"
    topics = ("xorg", "x11", "xcb")

    package_type = "build-scripts"
    settings = "os", "arch", "compiler", "build_type"

    def layout(self):
        basic_layout(self, src_folder="src")

    def package_id(self):
        self.info.clear()

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def package(self):
        copy(self, "COPYING", self.source_folder, os.path.join(self.package_folder, "licenses"))
        copy(self, "*.py",
             os.path.join(self.source_folder, "xcbgen"),
             os.path.join(self.package_folder, "lib", "xcbgen"))
        copy(self, "*.xml",
             os.path.join(self.source_folder, "src"),
             os.path.join(self.package_folder, "res", "xcb"))

    def package_info(self):
        self.cpp_info.resdirs = ["lib", "res"]
        self.cpp_info.includedirs = []
        self.cpp_info.bindirs = []
        self.cpp_info.libdirs = []

        self.cpp_info.set_property("pkg_config_name", "xcb-proto")
        # Fill in additional .pc fields
        # https://gitlab.freedesktop.org/xorg/proto/xcbproto/-/blob/xcb-proto-1.17.0/xcb-proto.pc.in
        self.cpp_info.set_property("pkg_config_custom_content", "\n".join([
            "exec_prefix=${prefix}",
            "datarootdir=${prefix}/res",
            "datadir=${datarootdir}",
            "xcbincludedir=${datadir}/xcb",
            "pythondir=${prefix}/lib"
        ]))

        self.buildenv_info.prepend_path("PYTHONPATH", os.path.join(self.package_folder, "lib"))
