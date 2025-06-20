import json
import os
import urllib.parse
from functools import cached_property
from pathlib import Path

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.files import *
from conan.tools.microsoft import is_msvc

required_conan_version = ">=2.1"


class OneMKLConan(ConanFile):
    name = "onemkl"
    description = "Intel oneAPI Math Kernel Library (oneMKL)"
    # https://intel.ly/393CijO
    license = "DocumentRef-license.txt:LicenseRef-Intel-DevTools-EULA"
    homepage = "https://www.intel.com/content/www/us/en/developer/tools/oneapi/onemkl.html"
    topics = ("intel", "oneapi", "math", "blas", "lapack", "linear-algebra", "pre-built")
    package_type = "shared-library"  # static is not supported due to Conan's inability to handle circular dependencies
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "interface": ["lp64", "ilp64"],  # GNU or Intel interface to use
        "sdl": [True, False],  # Use Single Dynamic Library interface for CMake targets
        "interface_type": ["intel", "gf"],  # Intel or GNU Fortran interface for CMake targets
        "threading": ["sequential", "tbb", "intel", "gomp"],  # Threading layer for CMake targets
        "mpi": ["intelmpi", "openmpi"],  # BLACS interface to export
        "blas95": [True, False],  # Add blas95 to MKL::MKL
        "lapack95": [True, False],  # Add lapack95 to MKL::MKL
    }
    default_options = {
        "interface": "lp64",
        "sdl": True,
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
        # These only affect package_info() targets
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

        # Keep only the libraries for the selected interface.
        # Could theoretically package both, but the other interface is just a gigabyte of dead weight.
        if self.options.interface == "ilp64":
            rm(self, "*_lp64*", os.path.join(self.package_folder, "lib"))
        else:
            rm(self, "*_ilp64*", os.path.join(self.package_folder, "lib"))

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

        interface = self.options.interface.value
        threading_component = "seq" if self.options.threading == "sequential" else self.options.threading.value
        mkl_lib = f"mkl-{threading_component}"

        # The main target
        self.cpp_info.components["mkl"].set_property("cmake_target_name", "MKL::MKL")
        if self.options.get_safe("sdl"):
            self.cpp_info.components["mkl"].requires = ["mkl-sdl"]
        else:
            self.cpp_info.components["mkl"].requires = [mkl_lib]
        if self.options.blas95:
            self.cpp_info.components["mkl"].requires.append("blas95")
        if self.options.lapack95:
            self.cpp_info.components["mkl"].requires.append("lapack95")

        # Single Dynamic Library (SDL) interface
        if self.options.get_safe("shared", True):
            self.cpp_info.components["mkl-sdl"].set_property("pkg_config_name", "mkl-sdl")
            self.cpp_info.components["mkl-sdl"].libs = ["mkl_rt"]
            # Configure the default interface via env vars
            # https://www.intel.com/content/www/us/en/docs/onemkl/developer-guide-linux/2025-1/dynamic-select-the-interface-and-threading-layer.html
            sdl_interface = interface.upper()
            if self.options.interface_type == "gf":
                sdl_interface = f"GNU,{sdl_interface}"
            self.runenv_info.define("MKL_INTERFACE_LAYER", sdl_interface)
            self.runenv_info.define("MKL_THREADING_LAYER", self.options.threading.value.upper())

        # Core library
        self.cpp_info.components["mkl-core"].libs = ["mkl_core"]
        self.cpp_info.components["mkl-core"].system_libs = ["pthread", "m", "dl"]
        if not is_msvc(self) and self.options.get_safe("shared", True):
            # Hacky fix to handle circular dependencies between the shared libraries
            self.cpp_info.components["mkl-core"].sharedlinkflags = ["-Wl,--start-group"]
            self.cpp_info.components["mkl-core"].exelinkflags = ["-Wl,--start-group"]
            self.cpp_info.components["mkl-core"].system_libs.append("-Wl,--end-group")
        if interface == "ilp64":
            self.cpp_info.components["mkl-core"].defines = ["MKL_ILP64"]

        # Interface libraries
        interface_lib = f"mkl-{self.options.interface_type}"
        linkage = "dynamic" if self.options.get_safe("shared", True) else "static"
        self.cpp_info.components["mkl-gf"].libs = [f"mkl_gf_{interface}"]
        self.cpp_info.components["mkl-gf"].requires = ["mkl-core"]
        self.cpp_info.components["mkl-intel"].libs = [f"mkl_intel_{interface}"]
        self.cpp_info.components["mkl-intel"].requires = ["mkl-core"]

        # Threading backend libraries
        self.cpp_info.components["mkl-seq"].set_property("pkg_config_name", f"mkl-{linkage}-{interface}-seq")
        self.cpp_info.components["mkl-seq"].libs = ["mkl_sequential"]
        self.cpp_info.components["mkl-seq"].requires = [interface_lib]

        self.cpp_info.components["mkl-tbb"].set_property("pkg_config_name", f"mkl-{linkage}-{interface}-tbb")
        self.cpp_info.components["mkl-tbb"].libs = ["mkl_tbb_thread"]
        self.cpp_info.components["mkl-tbb"].requires = [interface_lib, "onetbb::onetbb"]

        self.cpp_info.components["mkl-gomp"].set_property("pkg_config_name", f"mkl-{linkage}-{interface}-gomp")
        self.cpp_info.components["mkl-gomp"].libs = ["mkl_gnu_thread"]
        self.cpp_info.components["mkl-gomp"].system_libs = ["gomp"]
        self.cpp_info.components["mkl-gomp"].exelinkflags = ["-Wl,--no-as-needed"]
        self.cpp_info.components["mkl-gomp"].sharedlinkflags = ["-Wl,--no-as-needed"]
        self.cpp_info.components["mkl-gomp"].requires = [interface_lib]

        self.cpp_info.components["mkl-iomp"].set_property("pkg_config_name", f"mkl-{linkage}-{interface}-iomp")
        self.cpp_info.components["mkl-iomp"].libs = ["mkl_intel_thread"]
        self.cpp_info.components["mkl-iomp"].system_libs = ["libiomp5md" if self.settings.os == "Windows" else "iomp5"]
        self.cpp_info.components["mkl-iomp"].requires = [interface_lib]

        # Cluster libraries
        self.cpp_info.components["cdft"].set_property("cmake_target_name", "MKL::MKL_CDFT")
        self.cpp_info.components["cdft"].libs = ["mkl_cdft_core"]
        self.cpp_info.components["cdft"].requires = [f"blacs-{self.options.mpi}"]
        self.cpp_info.components["cdft"].requires = [mkl_lib]

        self.cpp_info.components["scalapack"].set_property("cmake_target_name", "MKL::MKL_SCALAPACK")
        self.cpp_info.components["scalapack"].libs = [f"mkl_scalapack_{interface}"]
        self.cpp_info.components["scalapack"].requires = [f"blacs-{self.options.mpi}"]
        self.cpp_info.components["scalapack"].requires = [mkl_lib]

        self.cpp_info.components["blacs"].set_property("cmake_target_name", "MKL::MKL_BLACS")
        self.cpp_info.components["blacs"].requires = [f"blacs-{self.options.mpi}"]
        self.cpp_info.components["blacs-intelmpi"].libs = [f"mkl_blacs_intelmpi_{interface}"]
        self.cpp_info.components["blacs-intelmpi"].requires = [mkl_lib]
        self.cpp_info.components["blacs-openmpi"].libs = [f"mkl_blacs_openmpi_{interface}"]
        self.cpp_info.components["blacs-openmpi"].requires = [mkl_lib]

        # Fortran95 API libraries
        self.cpp_info.components["blas95"].libs = [f"mkl_blas95_{interface}"]
        self.cpp_info.components["blas95"].requires = [mkl_lib]
        self.cpp_info.components["lapack95"].libs = [f"mkl_lapack95_{interface}"]
        self.cpp_info.components["lapack95"].requires = [mkl_lib]

        self.runenv_info.define_path("MKLROOT", self.package_folder)
        # Make mkl_link_tool available in build context
        self.buildenv_info.prepend_path("PATH", os.path.join(self.package_folder, "bin"))
