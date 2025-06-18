import json
import os
import urllib.parse
from functools import cached_property
from pathlib import Path

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.files import *

required_conan_version = ">=2.1"


class OneMKLConan(ConanFile):
    name = "onemkl"
    description = "Intel oneAPI Math Kernel Library (oneMKL)"
    # https://intel.ly/393CijO
    license = "DocumentRef-license.txt:LicenseRef-Intel-DevTools-EULA"
    homepage = "https://www.intel.com/content/www/us/en/developer/tools/oneapi/onemkl.html"
    topics = ("intel", "oneapi", "math", "blas", "lapack", "linear-algebra", "pre-built")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "opencl": [True, False],
        "sycl": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "opencl": True,
        "sycl": False,
    }
    provides = ["blas", "lapack", "mkl"]

    def package_id(self):
        del self.info.settings.compiler
        del self.info.settings.build_type

    def requirements(self):
        # Requires libonetbb.so.12
        self.requires("onetbb/[>=2021 <2023]")
        if self.options.opencl:
            self.requires("ocl-icd/[^2.3]")

    def validate(self):
        # TODO: add Windows support
        if self.settings.os not in ["FreeBSD", "Linux"]:
            raise ConanInvalidConfiguration(f"{self.settings.os} is not supported")
        if self.settings.arch != "x86_64":
            raise ConanInvalidConfiguration("Only x86_64 host architecture is supported")

    @cached_property
    def _extracted_installer_dir(self):
        return next(Path(self.build_folder).glob("intel-onemkl-*"))

    def _fix_package_symlinks(self):
        filelist = json.loads(load(self, "filelist.json"))
        for file_info in filelist["files"]:
            if "sha384" not in file_info:
                dst = file_info["fileName"]
                src = load(self, dst).strip()
                os.unlink(dst)
                os.symlink(src, urllib.parse.unquote(dst))

    def _extract_package(self, name):
        package_dir = next(p for p in Path(self._extracted_installer_dir, "packages").glob(f"{name},*") if p.is_dir())
        unzip(self, str(package_dir / "cupPayload.cup"), destination=self.build_folder)
        self._fix_package_symlinks()

    def build(self):
        # Download and extract
        download(self, **self.conan_data["sources"][self.version][str(self.settings.os)], filename="installer.sh")
        self.run(f"sh installer.sh -x -f .")
        rm(self, "installer.sh", self.build_folder)
        self._extract_package("intel.oneapi.lin.mkl.devel")
        self._extract_package("intel.oneapi.lin.mkl.runtime")

    @property
    def _staging_dir(self):
        return os.path.join(self.build_folder, "_installdir")

    def package(self):
        copy(self, "license.txt", self._extracted_installer_dir, os.path.join(self.package_folder, "licenses"))
        rmdir(self, self._extracted_installer_dir)
        mkl_dir = next(Path(self._staging_dir, "mkl").iterdir())
        move_folder_contents(self, mkl_dir, self.package_folder)
        rm(self, "intel64", os.path.join(self.package_folder, "lib"))
        rmdir(self, os.path.join(self.package_folder, ".toolkit_linking_tool"))
        rmdir(self, os.path.join(self.package_folder, "env"))
        rmdir(self, os.path.join(self.package_folder, "etc"))
        rmdir(self, os.path.join(self.package_folder, "share", "doc"))
        # rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))
        # rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "MKL")

        self.runenv_info.define_path("MKLROOT", self.package_folder)

        raise
