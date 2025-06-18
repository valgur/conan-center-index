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
    package_type = "shared-library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "sdl": [True, False],  # Use Single Dynamic Library interface for CMake targets
        "interface": ["lp64", "ilp64"],  # GNU or Intel interface for CMake targets
        "interface_type": ["intel", "gf"],  # Intel or GNU Fortran interface for CMake targets
        "threading": ["sequential", "tbb", "intel", "gomp"],  # Threading layer for CMake targets
        "mpi": ["intelmpi", "openmpi"],  # BLACS interface to export
        "blas95": [True, False],  # Add blas95 to MKL::MKL
        "lapack95": [True, False],  # Add lapack95 to MKL::MKL
    }
    default_options = {
        "sdl": True,
        "interface": "lp64",
        "interface_type": "intel",
        "threading": "tbb",
        "mpi": "intelmpi",
        "blas95": False,
        "lapack95": False,
    }
    provides = ["blas", "lapack", "mkl"]

    def config_options(self):
        if self.settings.compiler == "intel-cc":
            self.options.interface = "ilp64"
            self.options.threading = "intel"

    def configure(self):
        if not self.options.get_safe("shared", True):
            del self.options.sdl

    def package_id(self):
        del self.info.settings.compiler
        del self.info.settings.build_type
        self.info.options.rm_safe("sdl")
        del self.info.options.mpi

    def requirements(self):
        # Requires libonetbb.so.12
        self.requires("onetbb/[>=2021 <2023]")

    def validate(self):
        # TODO: add Windows support
        if self.settings.os not in ["FreeBSD", "Linux"]:
            raise ConanInvalidConfiguration(f"{self.settings.os} is not supported")
        if self.settings.arch != "x86_64":
            raise ConanInvalidConfiguration("Only x86_64 architecture is supported")

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
        unzip(self, str(package_dir / "cupPayload.cup"), destination=self.build_folder, keep_permissions=True)
        self._fix_package_symlinks()

    def build(self):
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
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))

        # TODO: add sycl support
        rm(self, "*_sycl*", os.path.join(self.package_folder, "lib"))
        # Remove all non-runtime libraries that don't match shared=True/False
        if self.options.get_safe("shared", True):
            rm(self, "*.a", os.path.join(self.package_folder, "lib"), excludes=["*blas95*", "*lapack95*"])
        else:
            rm(self, "libmkl_rt.so*", os.path.join(self.package_folder, "lib"))
            for static_lib in Path(self.package_folder, "lib").glob("*.a"):
                if static_lib.with_suffix(".so").exists():
                    rm(self, f"{static_lib.stem}.so*", os.path.join(self.package_folder, "lib"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "MKL")

        if self.options.get_safe("shared", True):
            # Single Dynamic Library (SDL) interface
            self.cpp_info.components["sdl"].set_property("pkg_config_name", "mkl-sdl")
            self.cpp_info.components["sdl"].libs = ["mkl_rt"]
            # Configure the default interface via env vars
            # https://www.intel.com/content/www/us/en/docs/onemkl/developer-guide-linux/2025-1/dynamic-select-the-interface-and-threading-layer.html
            interface = self.options.interface.value.upper()
            if self.options.interface_type == "gf":
                interface = f"GNU,{interface}"
            self.runenv_info.define("MKL_INTERFACE_LAYER", interface)
            self.runenv_info.define("MKL_THREADING_LAYER", self.options.threading.value.upper())

        self.cpp_info.components["core"].set_property("cmake_target_name", f"MKL::mkl_core")
        self.cpp_info.components["core"].libs = ["mkl_core"]
        self.cpp_info.components["core"].system_libs = ["pthread", "m", "dl"]

        linkage = "dynamic" if self.options.get_safe("shared", True) else "static"
        for int_type in ["lp64", "ilp64"]:
            common = f"{int_type}-common"
            self.cpp_info.components[common].requires = [f"{int_type}-{self.options.interface_type}", "core"]
            if int_type == "ilp64":
                self.cpp_info.components[common].defines = ["MKL_ILP64"]

            self.cpp_info.components[f"{int_type}-seq"].set_property("pkg_config_name", f"mkl-{linkage}-{int_type}-seq")
            self.cpp_info.components[f"{int_type}-seq"].libs = ["mkl_sequential"]
            self.cpp_info.components[f"{int_type}-seq"].requires = [common]

            self.cpp_info.components[f"{int_type}-tbb"].set_property("pkg_config_name", f"mkl-{linkage}-{int_type}-tbb")
            self.cpp_info.components[f"{int_type}-tbb"].libs = ["mkl_tbb_thread"]
            self.cpp_info.components[f"{int_type}-tbb"].requires = [common, "onetbb::onetbb"]

            self.cpp_info.components[f"{int_type}-gomp"].set_property("pkg_config_name", f"mkl-{linkage}-{int_type}-gomp")
            self.cpp_info.components[f"{int_type}-gomp"].libs = ["mkl_gnu_thread"]
            self.cpp_info.components[f"{int_type}-gomp"].system_libs = ["gomp"]
            self.cpp_info.components[f"{int_type}-gomp"].exelinkflags = ["-Wl,--no-as-needed"]
            self.cpp_info.components[f"{int_type}-gomp"].sharedlinkflags = ["-Wl,--no-as-needed"]
            self.cpp_info.components[f"{int_type}-gomp"].requires = [common]

            self.cpp_info.components[f"{int_type}-iomp"].set_property("pkg_config_name", f"mkl-{linkage}-{int_type}-iomp")
            self.cpp_info.components[f"{int_type}-iomp"].libs = ["mkl_intel_thread"]
            self.cpp_info.components[f"{int_type}-iomp"].system_libs = ["iomp5"]
            self.cpp_info.components[f"{int_type}-iomp"].requires = [common]

            for lib in ["gf", "intel", "blas95", "lapack95", "scalapack", "blacs_intelmpi", "blacs_openmpi"]:
                component =  self.cpp_info.components[f"{int_type}-{lib.replace('_', '-')}"]
                component.set_property("cmake_target_name", f"MKL::mkl_{lib}_{int_type}")
                component.libs = [f"mkl_{lib}_{int_type}"]
                component.requires = ["core"]
                if int_type == "ilp64":
                    component.defines = ["MKL_ILP64"]

        self.cpp_info.components["cdft-core"].set_property("cmake_target_name", "MKL::mkl_cdft_core")
        self.cpp_info.components["cdft-core"].libs = ["mkl_cdft_core"]

        if self.options.get_safe("sdl"):
            backend = "sdl"
        else:
            backend = f"{self.options.interface}-{self.options.threading}"

        self.cpp_info.components["cdft"].set_property("cmake_target_name", "MKL::MKL_CDFT")
        self.cpp_info.components["cdft"].requires = ["cdft-core", backend]

        self.cpp_info.components["scalapack"].set_property("cmake_target_name", "MKL::MKL_SCALAPACK")
        self.cpp_info.components["scalapack"].requires = [f"{self.options.interface}-scalapack", backend]

        self.cpp_info.components["blacs"].set_property("cmake_target_name", "MKL::MKL_BLACS")
        self.cpp_info.components["blacs"].requires = [f"{self.options.interface}-blacs-{self.options.mpi}", backend]

        self.cpp_info.components["mkl"].set_property("cmake_target_name", "MKL::MKL")
        self.cpp_info.components["mkl"].requires = [backend]
        if self.options.blas95:
            self.cpp_info.components["mkl"].requires.append(f"{self.options.interface}-blas95")
        if self.options.lapack95:
            self.cpp_info.components["mkl"].requires.append(f"{self.options.interface}-lapack95")

        self.runenv_info.define_path("MKLROOT", self.package_folder)
        # Make mkl_link_tool available in build context
        self.buildenv_info.prepend_path("PATH", os.path.join(self.package_folder, "bin"))
