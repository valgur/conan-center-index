import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.apple import fix_apple_shared_install_name
from conan.tools.build import cross_building
from conan.tools.env import VirtualRunEnv
from conan.tools.files import *
from conan.tools.gnu import Autotools, AutotoolsDeps, AutotoolsToolchain
from conan.tools.layout import basic_layout

required_conan_version = ">=2.18"


class UccConan(ConanFile):
    name = "ucc"
    description = "Unified Collective Communication Library"
    license = "BSD-3-Clause"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://openucx.github.io/ucc/"
    topics = ("deep-learning", "hpc", "mpi", "cuda", "pgas", "sharp", "infiniband", "roce", "openshmem", "collectives")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type", "cuda"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "cuda": [True, False],
        "mlx5": [True, False],
        "nccl": [True, False],
        "self": [True, False],
        "ucp": [True, False],
        # "rccl": [True, False],
        # "sharp": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": False,
        "cuda": False,
        "mlx5": False,
        "nccl": False,
        "self": False,
        "ucp": False,
        # "rccl": True,
        # "sharp": True,
    }
    implements = ["auto_shared_fpic"]

    python_requires = "conan-utils/latest"

    @property
    def _utils(self):
        return self.python_requires["conan-utils"].module

    def configure(self):
        if not self.options.cuda:
            del self.settings.cuda

    def layout(self):
        basic_layout(self, src_folder="src")

    def package_id(self):
        if self.options.cuda:
            del self.info.settings.cuda.version

    def requirements(self):
        self.requires("openucx/[^1.19.0]", options={
            "cuda": self.options.cuda,
            "mlx5": self.options.mlx5,
            "rdmacm": self.options.mlx5,
            "verbs": self.options.mlx5,
        })
        if self.options.cuda:
            self.requires(f"cuda-driver-stubs/[~{self.settings.cuda.version}]")
            self.requires(f"cudart/[~{self.settings.cuda.version}]")
            self.requires(f"nvml-stubs/[~{self.settings.cuda.version}]")
        if self.options.nccl:
            self.requires("nccl/[^2]")
        if self.options.mlx5:
            self.requires("rdma-core/[*]")

    def validate(self):
        if self.settings.os not in ["Linux", "FreeBSD"]:
            raise ConanInvalidConfiguration(f"{self.ref} is not supported on {self.settings.os}.")

    def build_requirements(self):
        self.tool_requires("libtool/[^2.4.7]")
        if self.options.cuda:
            self.tool_requires(f"nvcc/[~{self.settings.cuda.version}]")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        save(self, "test/gtest/Makefile.am", "all:;\ninstall:;\n")
        save(self, "test/mpi/Makefile.am", "all:;\ninstall:;\n")
        save(self, "tools/perf/Makefile.am", "all:;\ninstall:;\n")

    def generate(self):
        if not cross_building(self):
            VirtualRunEnv(self).generate(scope="build")

        if self.options.cuda:
            nvcc_tc = self._utils.NvccToolchain(self, skip_arch_flags=True)
            nvcc_tc.generate()

        def enable_disable(opt, val):
            return f"--enable-{opt}" if val else f"--disable-{opt}"

        def with_without(opt, val, pkg=None):
            if val and pkg:
                return f"--with-{opt}={self.dependencies[pkg].package_folder}"
            return f"--with-{opt}" if val else f"--without-{opt}"

        tls = []
        for tl in ["cuda", "mlx5", "nccl", "rccl", "self", "sharp", "ucp"]:
            if self.options.get_safe(tl):
                tls.append(tl)

        tc = AutotoolsToolchain(self)
        tc.configure_args.extend([
            "--with-tls=" + ",".join(tls),
            "--disable-doxygen-doc",
            enable_disable("debug", self.settings.build_type in ["Debug", "RelWithDebInfo"]),
            "--with-sse41",
            "--with-sse42",
            # "--with-avx",
            with_without("ucx", True, "openucx"),
            with_without("cuda", self.options.cuda, "cudart"),
            "--without-rocm",
            "--without-doca-urom",
            with_without("ibverbs", self.options.mlx5, "rdma-core"),
            with_without("rdmacm", self.options.mlx5, "rdma-core"),
            with_without("nccl", self.options.nccl, "nccl"),
            "--without-rccl",
            "--without-sharp",
            "NVCC=nvcc",
            "tlcp_ucp_example_enabled=n",
            "TLCP_UCP_EXAMPLE_ENABLED_FALSE=y",
        ])
        if self.options.cuda:
            tc.configure_args.append(f"--with-nvcc-gencode={' '.join(nvcc_tc.arch_flags)}")
        tc.generate()

        deps = AutotoolsDeps(self)
        deps.generate()

    def _patch_sources(self):
        if self.options.cuda and not self.dependencies["cudart"].options.shared:
            replace_in_file(self, os.path.join(self.source_folder, "config/m4/cuda.m4"), "cudart", "cudart_static")
        if self.options.nccl and not self.dependencies["nccl"].options.shared:
            nccl_m4 = os.path.join(self.source_folder, "config/m4/nccl.m4")
            replace_in_file(self, nccl_m4, "AC_CHECK_LIB([nccl]", "AC_CHECK_LIB([nccl_static]")
            replace_in_file(self, nccl_m4, "-lnccl", "-lnccl_static")

    def build(self):
        self._patch_sources()
        autotools = Autotools(self)
        self.run("./autogen.sh", cwd=self.source_folder)
        autotools.configure()
        autotools.make()

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        autotools = Autotools(self)
        autotools.install()
        rm(self, "*.la", os.path.join(self.package_folder, "lib"), recursive=True)
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))
        fix_apple_shared_install_name(self)

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "ucc")
        self.cpp_info.set_property("pkg_config_name", "none")

        self.cpp_info.components["ucc_"].set_property("cmake_target_name", "ucc::ucc")
        self.cpp_info.components["ucc_"].libs = ["ucc"]
        self.cpp_info.components["ucc_"].requires = ["openucx::ucs"]

        # The CMake targets and pkg-config names that follow are not official.
        # https://github.com/openucx/ucc/blob/v1.5.0/docs/user_guide.md#cls-and-tls

        def _add_component(name, requires=None):
            component = self.cpp_info.components[name]
            component.set_property("cmake_target_name", f"ucc::{name}")
            component.set_property("pkg_config_name", name)
            component.libs = [name]
            component.libdirs = ["lib/ucc"]
            component.requires = ["ucc_"] + (requires or [])

        cudart = ["cudart::cudart_", "nvml-stubs::nvml-stubs", "cuda-driver-stubs::cuda-driver-stubs"]

        # Collective Layer
        _add_component("ucc_cl_basic")
        _add_component("ucc_cl_hier")
        _add_component("ucc_ec_cpu")
        if self.options.cuda:
            _add_component("ucc_ec_cuda", requires=cudart)
        _add_component("ucc_mc_cpu")
        if self.options.cuda:
            _add_component("ucc_mc_cuda", requires=cudart)
        # Team Layer
        if self.options.self:
            _add_component("ucc_tl_self")
        if self.options.cuda:
            _add_component("ucc_tl_cuda", requires=cudart)
        if self.options.mlx5:
            _add_component("ucc_tl_mlx5", requires=["rdma-core::librdmacm", "rdma-core::libmlx5", "rdma-core::libibverbs"])
        if self.options.nccl:
            _add_component("ucc_tl_nccl", requires=["nccl::nccl"] + cudart)
        if self.options.ucp:
            _add_component("ucc_tl_ucp", requires=["openucx::ucp"])
