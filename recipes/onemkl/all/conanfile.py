import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.cmake import cmake_layout
from conan.tools.files import download, unzip, copy, export_conandata_patches, rm, rmdir
from conan.tools.scm import Version

required_conan_version = ">=1.53.0"


class OneMklConan(ConanFile):
    name = "onemkl"
    description = "Intel oneAPI Math Kernel Library (oneMKL)"
    license = "Apache-2.0 OR MIT"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://software.intel.com/content/www/us/en/develop/tools/oneapi/components/onemkl.html"
    topics = ("mkl", "blas", "lapack", "ompi5", "pre-built")

    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
    }
    default_options = {
        "shared": False,
    }
    no_copy_source = True

    def export_sources(self):
        export_conandata_patches(self)

    def layout(self):
        cmake_layout(self, src_folder="src")

    def package_id(self):
        del self.info.settings.compiler
        del self.info.settings.build_type

    def requirements(self):
        # oneMKL includes oneTBB, but we package it separately
        self.requires("onetbb/2021.10.0", transitive_headers=True, transitive_libs=True)

    def validate(self):
        if self.settings.os != "Linux":
            raise ConanInvalidConfiguration("oneMKL is currently only supported on Linux.")
        if self.settings.arch not in ["x86_64", "x86"]:
            raise ConanInvalidConfiguration("oneMKL only supports x86_64 and x86 architectures.")

    def source(self):
        download(self, **self.conan_data["sources"][self.version], filename="onemkl.sh")
        with open("onemkl.sh", "rb") as f_in, open("onemkl.tar.gz", "wb") as f_out:
            f_out.write(f_in.read(50000).split(b"__CONTENT__\n")[1])
            for chunk in iter(lambda: f_in.read(10000), b""):
                f_out.write(chunk)
        rm(self, "onemkl.sh", ".")
        unzip(self, "onemkl.tar.gz", strip_root=True, keep_permissions=True)
        rm(self, "onemkl.tar.gz", ".")

    @property
    def _install_folder(self):
        return os.path.join(self.build_folder, "_installdir")

    def build(self):
        # Not calling ./install.sh because it writes to ~/intel and ~/.intel
        # self.run(f"./install.sh --silent --eula accept --intel-sw-improvement-program-consent decline --install-dir '{self._install_folder}'", cwd=self.source_folder)
        # packages/intel.oneapi.lin.mkl.devel,v=2024.1.0+691
        # packages/intel.oneapi.lin.mkl.runtime,v=2024.1.0+691
        # packages/intel.oneapi.lin.openmp,v=2024.1.0+963
        for package in ["mkl.devel", "mkl.runtime", "openmp"]:
            package_archive = next(self.source_path.joinpath("packages").rglob(f"intel.oneapi.lin.{package},*/cupPayload.cup"))
            unzip(self, str(package_archive), destination=self.build_folder, keep_permissions=True)

    @property
    def _short_version(self):
        ver = Version(self.version)
        return f"{ver.major}.{ver.minor}"

    def package(self):
        mkl_folder = os.path.join(self._install_folder, "mkl", self._short_version)
        compiler_folder = os.path.join(self._install_folder, "compiler", self._short_version)
        copy(self, "*",
             os.path.join(mkl_folder, "share", "doc", "mkl", "licensing"),
             os.path.join(self.package_folder, "licenses"))
        rm(self, "third-party-programs-benchmarks.txt", os.path.join(self.package_folder, "licenses"))
        rm(self, "third-party-programs-oneTBB.txt", os.path.join(self.package_folder, "licenses"))

        lib_dir = "lib" if self.settings.arch == "x86_64" else "lib32"
        lib_pattern = "*.so*" if self.options.shared else "*.a"
        copy(self, lib_pattern, os.path.join(mkl_folder, lib_dir), os.path.join(self.package_folder, "lib"))
        libiomp5_pattern = "libiomp5.so*" if self.options.shared else "libiomp5.a"
        copy(self, libiomp5_pattern, os.path.join(compiler_folder, lib_dir), os.path.join(self.package_folder, "lib"))

        for soname_file in self.package_path.joinpath("lib").glob("*.so.*"):
            stem = soname_file.name.split(".", 1)[0]
            so_file = soname_file.parent.joinpath(f"{stem}.so")
            if so_file.exists():
                so_file.unlink()
            so_file.symlink_to(soname_file)

        copy(self, "*",
             os.path.join(mkl_folder, "include"),
             os.path.join(self.package_folder, "include"))
        rm(self, "ia32", os.path.join(self.package_folder, "include"))
        rm(self, "intel64", os.path.join(self.package_folder, "include"))
        rm(self, "locale", os.path.join(self.package_folder, "include"))
        copy(self, "*",
             os.path.join(mkl_folder, "bin"),
             os.path.join(self.package_folder, "bin"))
        copy(self, "*",
             os.path.join(mkl_folder, "share", "mkl", "interfaces"),
             os.path.join(self.package_folder, "res", "mkl", "interfaces"))
        copy(self, "*",
             os.path.join(mkl_folder, "share", "locale"),
             os.path.join(self.package_folder, "res", "locale"))

        # TODO: add support for cluster libs. requires MPI
        rm(self, "libmkl_cdft*", os.path.join(self.package_folder, "lib"))
        rm(self, "libmkl_blacs*", os.path.join(self.package_folder, "lib"))
        rm(self, "libmkl_scalapack*", os.path.join(self.package_folder, "lib"))
        rmdir(self, os.path.join(self.package_folder, "include", "fftw"))

        # TODO: add SYCL support. requires Intel's dpcpp or icpx compiler
        rm(self, "libmkl_sycl_*", os.path.join(self.package_folder, "lib"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "MKL")

        # Based on openmp.pc
        self.cpp_info.components["openmp"].set_property("pkg_config_name", "openmp")
        if self.settings.arch == "x86":
            self.cpp_info.components["openmp"].set_property("pkg_config_aliases", ["openmp32"])
        self.cpp_info.components["openmp"].libs = ["iomp5"]

        # Single Dynamic Library (SDL) interface
        self.cpp_info.components["mkl-sdl"].set_property("pkg_config_name", "mkl-sdl")
        self.cpp_info.components["mkl-sdl"].libs = ["mkl_rt"]
        self.cpp_info.components["mkl-sdl"].system_libs = ["pthread", "m", "dl"]

        linkage = "dynamic" if self.options.shared else "static"
        if self.settings.arch == "x86_64":
            int_types = ["lp64", "ilp64"]
        else:
            int_types = [""]
        for int_type in int_types:
            int_component = f"-{int_type}" if int_type else ""
            common = f"mkl{int_component}-common"
            # TODO: add support for mkl_gf (GFortran) interface in addition to mkl_intel
            self.cpp_info.components[common].libs = [f"mkl_intel_{int_type}" if int_type else "mkl_intel", "mkl_core"]
            self.cpp_info.components[common].system_libs = ["pthread", "m", "dl"]
            if int_type == "ilp64":
                self.cpp_info.components[common].defines = ["MKL_ILP64"]

            self.cpp_info.components[f"mkl{int_component}-iomp"].set_property("pkg_config_name", f"mkl-{linkage}{int_component}-iomp")
            self.cpp_info.components[f"mkl{int_component}-iomp"].libs = ["mkl_intel_thread"]
            self.cpp_info.components[f"mkl{int_component}-iomp"].requires = [common, "openmp"]

            self.cpp_info.components[f"mkl{int_component}-gomp"].set_property("pkg_config_name", f"mkl-{linkage}{int_component}-gomp")
            self.cpp_info.components[f"mkl{int_component}-gomp"].libs = ["mkl_gnu_thread"]
            self.cpp_info.components[f"mkl{int_component}-gomp"].requires = [common]
            self.cpp_info.components[f"mkl{int_component}-gomp"].system_libs = ["gomp"]
            self.cpp_info.components[f"mkl{int_component}-gomp"].exelinkflags = ["-Wl,--no-as-needed"]
            self.cpp_info.components[f"mkl{int_component}-gomp"].sharedlinkflags = ["-Wl,--no-as-needed"]

            self.cpp_info.components[f"mkl{int_component}-tbb"].set_property("pkg_config_name", f"mkl-{linkage}{int_component}-tbb")
            self.cpp_info.components[f"mkl{int_component}-tbb"].libs = ["mkl_tbb_thread"]
            self.cpp_info.components[f"mkl{int_component}-tbb"].requires = [common, "onetbb::onetbb"]

            self.cpp_info.components[f"mkl{int_component}-seq"].set_property("pkg_config_name", f"mkl-{linkage}{int_component}-seq")
            self.cpp_info.components[f"mkl{int_component}-seq"].libs = ["mkl_sequential"]
            self.cpp_info.components[f"mkl{int_component}-seq"].requires = [common]
