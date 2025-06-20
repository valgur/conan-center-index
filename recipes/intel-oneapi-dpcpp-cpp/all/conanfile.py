import json
import os
import urllib.parse
from functools import cached_property
from pathlib import Path

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.files import *

required_conan_version = ">=2.1"


class PackageConan(ConanFile):
    name = "intel-oneapi-dpcpp-cpp"
    description = "Intel oneAPI DPC++/C++ Compiler"
    # https://intel.ly/393CijO
    license = "DocumentRef-license.txt:LicenseRef-Intel-DevTools-EULA"
    homepage = "https://www.intel.com/content/www/us/en/developer/tools/oneapi/dpc-compiler.html"
    topics = ("intel", "oneapi", "compiler", "sycl", "pre-built")
    package_type = "application"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        # components to install in addition to the compiler
        "debugger": [True, False],
        "dev_utilities": [True, False],
        "dpl": [True, False],
        "tbb": [True, False],
        "tcm": [True, False],
        "umf": [True, False],
    }
    default_options = {
        "debugger": False,
        "dev_utilities": False,
        "dpl": False,
        "tbb": False,
        "tcm": False,
        "umf": False,
    }

    upload_policy = "skip"
    build_policy = "missing"

    def package_id(self):
        del self.info.settings.compiler
        del self.info.settings.build_type

    def validate(self):
        # TODO: add Windows support
        if self.settings.os not in ["FreeBSD", "Linux"]:
            raise ConanInvalidConfiguration(f"{self.settings.os} is not supported")
        if self.settings.arch != "x86_64":
            raise ConanInvalidConfiguration("Only x86_64 host architecture is supported")
        if self.settings.os in ["FreeBSD", "Linux"] and self.settings.compiler.libcxx != "libstdc++11":
            raise ConanInvalidConfiguration("compiler.libcxx=libstdc++11 is required for compatibility with the compiler runtime libraries")

    @cached_property
    def _extracted_installer_dir(self):
        return next(Path(self.build_folder).glob("intel-dpcpp-cpp-compiler-*"))

    def _fix_package_symlinks(self):
        filelist = json.loads(load(self, "filelist.json"))
        for file_info in filelist["files"]:
            if "sha384" not in file_info:
                dst = file_info["fileName"]
                src = load(self, dst).strip()
                os.unlink(dst)
                # unquote is for clang%2B%2B, etc
                os.symlink(src, urllib.parse.unquote(dst))

    def _extract_package(self, name):
        package_dir = next(p for p in Path(self._extracted_installer_dir, "packages").glob(f"{name},*") if p.is_dir())
        unzip(self, str(package_dir / "cupPayload.cup"), destination=self.build_folder, keep_permissions=True)
        self._fix_package_symlinks()

    def build(self):
        # Download and extract
        download(self, **self.conan_data["sources"][self.version][str(self.settings.os)], filename="installer.sh")
        self.run(f"sh installer.sh -x -f .")
        rm(self, "installer.sh", self.build_folder)
        self._extract_package("intel.oneapi.lin.compilers-common")
        self._extract_package("intel.oneapi.lin.compilers-common.runtime")
        self._extract_package("intel.oneapi.lin.dpcpp-cpp-common")
        self._extract_package("intel.oneapi.lin.dpcpp-cpp-common.runtime")
        self._extract_package("intel.oneapi.lin.openmp")
        if self.options.debugger:
            self._extract_package("intel.oneapi.lin.dpcpp_dbg")
        if self.options.dev_utilities:
            self._extract_package("intel.oneapi.lin.dev-utilities.plugins")
        if self.options.dpl:
            self._extract_package("intel.oneapi.lin.dpl")
        if self.options.tbb:
            self._extract_package("intel.oneapi.lin.tbb.devel")
            self._extract_package("intel.oneapi.lin.tbb.runtime")
        if self.options.tcm:
            self._extract_package("intel.oneapi.lin.tcm")
        if self.options.umf:
            self._extract_package("intel.oneapi.lin.umf")

    @property
    def _staging_dir(self):
        return os.path.join(self.build_folder, "_installdir")

    def package(self):
        copy(self, "license.txt", self._extracted_installer_dir, os.path.join(self.package_folder, "licenses"))
        rmdir(self, self._extracted_installer_dir)
        # Merge all package dirs into one in the package folder
        for pkg_dir in Path(self._staging_dir).iterdir():
            subdir = next(pkg_dir.iterdir())
            move_folder_contents(self, subdir, self.package_folder)
        rmdir(self, os.path.join(self.package_folder, ".toolkit_linking_tool"))
        # Remove env/ and etc/ which contain only vars.sh, which is covered by package_info()
        rmdir(self, os.path.join(self.package_folder, "env"))
        rmdir(self, os.path.join(self.package_folder, "etc"))
        # Remove linux/include -> ../include symlink
        rmdir(self, os.path.join(self.package_folder, "linux"))
        rmdir(self, os.path.join(self.package_folder, "share", "doc"))
        rmdir(self, os.path.join(self.package_folder, "share", "man"))
        rmdir(self, self._staging_dir)

        # Create a dummy setvars.sh for Conan's IntelCC generator
        save(self, os.path.join(self.package_folder, "setvars.sh"), "#!/bin/sh\n")
        os.chmod(os.path.join(self.package_folder, "setvars.sh"), 0o755)

    def package_info(self):
        # self.cpp_info.bindirs.append("bin/compiler")
        self.cpp_info.frameworkdirs = []
        self.cpp_info.libdirs = ["lib"]
        self.cpp_info.resdirs = ["share", "opt"]

        if self.options.debugger:
            self.cpp_info.bindirs.append(os.path.join("opt", "debugger", "bin"))
            self.cpp_info.libdirs.append(os.path.join("opt", "debugger", "lib"))

        # Reproduce parts of vars.sh that are not automatically handled by Conan
        self.runenv_info.prepend_path("NLSPATH", os.path.join(self.package_folder, "lib/compiler/locale/%l_%t/%N"))
        self.runenv_info.append_path("OCL_ICD_FILENAMES", os.path.join(self.package_folder, "lib/libintelocl.so"))
        if Path(self.package_folder, "lib", "libigdrcl.so").exists():
            self.runenv_info.append_path("OCL_ICD_FILENAMES", os.path.join(self.package_folder, "lib/libigdrcl.so"))
        if self.options.umf:
            self.runenv_info.define_path("UMF_ROOT", self.package_folder)
        if self.options.tcm:
            self.runenv_info.define_path("TCM_ROOT", self.package_folder)
        if self.options.dpl:
            self.runenv_info.define_path("DPL_ROOT", self.package_folder)
        if self.options.tbb:
            self.runenv_info.define_path("TBBROOT", self.package_folder)
        if self.options.debugger:
            self.runenv_info.define_path("INTEL_PYTHONHOME", os.path.join(self.package_folder, "opt", "debugger"))
            self.runenv_info.prepend_path("GDB_INFO", os.path.join(self.package_folder, "share", "info"))

        self.runenv_info.define("CC", "icx")
        self.runenv_info.define("CXX", "icpx")
        # configure: error: C preprocessor "icx" fails sanity check
        # self.runenv_info.define("CPP", "icx")
        # self.runenv_info.define("CXXCPP", "icx")

        self.conf_info.update("tools.build:compiler_executables", {
            "c": "icx",
            "cpp": "icpx",
        })

        self.conf_info.define_path("tools.intel:installation_path", self.package_folder)
