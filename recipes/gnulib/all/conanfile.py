# TODO: verify the Conan v2 migration

import os
import shutil

from conan import ConanFile
from conan.tools.files import copy, get
from conan.tools.layout import basic_layout

required_conan_version = ">=1.52.0"


class GnuLibConanFile(ConanFile):
    name = "gnulib"
    description = (
        "Gnulib is a central location for common GNU code, intended to be shared among GNU packages."
    )
    license = ("GPL-3.0-or-later", "LGPL-3.0-or-later", "Unlicense")
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://www.gnu.org/software/gnulib/"
    topics = ("library", "gnu", "header-only")

    package_type = "header-library"
    settings = "os", "arch", "compiler", "build_type"
    no_copy_source = True

    def layout(self):
        basic_layout(self, src_folder="src")

    def package_id(self):
        self.info.clear()

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True, filename="gnulib.tar.gz")

    def package(self):
        copy(self, "COPYING", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))

        # The following line did not work, so do it the long way...
        # shutil.copy(self.source_folder, os.path.join(self.package_folder, "bin"))

        gnulib_dir = self.source_folder
        for root, _, files in os.walk(gnulib_dir):
            relpath = os.path.relpath(root, gnulib_dir)
            dstdir = os.path.join(self.package_folder, "bin", relpath)
            try:
                os.makedirs(dstdir)
            except FileExistsError:
                pass
            for file in files:
                src = os.path.join(root, file)
                dst = os.path.join(dstdir, file)
                shutil.copy(src, dst)

    def package_info(self):
        self.cpp_info.libdirs = []

        binpath = os.path.join(self.package_folder, "bin")
        self.output.info(f"Appending PATH environment var: {binpath}")
        self.env_info.PATH.append(binpath)
