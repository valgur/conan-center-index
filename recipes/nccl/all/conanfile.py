import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import check_min_cppstd
from conan.tools.files import *
from conan.tools.gnu import AutotoolsToolchain, Autotools
from conan.tools.layout import basic_layout
from conan.tools.scm import Version

required_conan_version = ">=2.1"


class NcclConan(ConanFile):
    name = "nccl"
    description = "NCCL: NVIDIA Collective Communications Library"
    license = "BSD-3-Clause AND Apache-2.0 WITH LLVM-exception"
    homepage = "https://developer.nvidia.com/nccl"
    topics = ("cuda", "multi-gpu", "communication")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type", "cuda"
    options = {
        "shared": [True, False],
        "with_ibverbs": [True, False],
        "with_mlx5": [True, False],
    }
    default_options = {
        "shared": False,
        # Dynamic loading support for ibverbs and mlx5 is still provided even if not explicitly linked against.
        "with_ibverbs": False,
        "with_mlx5": False,
    }
    implements = ["auto_shared_fpic"]

    python_requires = "conan-utils/latest"

    @property
    def _utils(self):
        return self.python_requires["conan-utils"].module

    def layout(self):
        basic_layout(self, src_folder="src")

    def package_id(self):
        del self.info.settings.cuda.version

    def requirements(self):
        self.requires(f"cudart/[~{self.settings.cuda.version}]", transitive_headers=True, transitive_libs=True)
        if self.options.with_ibverbs or self.options.with_mlx5:
            self.requires("rdma-core/[*]")

    def validate(self):
        if self.settings.os != "Linux":
            raise ConanInvalidConfiguration(f"{self.name} only supports Linux.")
        check_min_cppstd(self, 14 if Version(self.settings.cuda.version) < 13 else 17)
        if self.options.with_mlx5 and not self.dependencies["rdma-core"].options.build_libmlx5:
            raise ConanInvalidConfiguration("rdma-core must be built with 'build_libmlx5=True' to use the 'with_mlx5' option.")

    def build_requirements(self):
        self.tool_requires(f"nvcc/[~{self.settings.cuda.version}]")
        # The build also requires Python 3 for code generation

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        nvcc_tc = self._utils.NvccToolchain(self)
        nvcc_tc.generate()

        # Copy cudart and its deps into a single dir to keep things simple for some hard-coded logic in the makefiles.
        fake_cuda_home = os.path.join(self.build_folder, "cuda_home")
        for _, dep in self.dependencies.host.items():
            copy(self, "*", dep.package_folder, fake_cuda_home)

        incflags = " ".join(f"-I{dep.cpp_info.includedir}" for _, dep in self.dependencies.host.items())
        incflags += f" -I{self.source_folder}/src/include"
        incflags += f" -I{self.source_folder}/src/device"
        incflags += f" -I{self.source_folder}/build/include"
        ldflags = " ".join(f"-L{dep.cpp_info.libdirs[0]}" for _, dep in self.dependencies.host.items() if dep.cpp_info.libdirs)

        tc = AutotoolsToolchain(self)
        tc.make_args.append(f"DEBUG={'1' if self.settings.build_type == 'Debug' else '0'}")
        tc.make_args.append("NVCC=nvcc")
        tc.make_args.append(f"CUDA_HOME={self.dependencies['cudart'].package_folder}")
        tc.make_args.append(f"CUDA_LIB={self.dependencies['cudart'].cpp_info.libdirs[0]}")
        tc.make_args.append(f"NVCC_GENCODE={' '.join(nvcc_tc.cudaflags)}")
        tc.make_args.append(f"INCFLAGS+={incflags}")
        tc.make_args.append(f"CXXFLAGS+={incflags} -fPIC")
        tc.make_args.append(f"LDFLAGS+={ldflags}")
        tc.make_args.append(f"NVLDFLAGS+={ldflags} {' '.join(nvcc_tc.cudaflags)}")
        tc.make_args.append(f"RDMA_CORE={'1' if self.options.with_ibverbs else '0'}")
        tc.make_args.append(f"MLX5DV={'1' if self.options.with_mlx5 else '0'}")
        if self.conf.get("tools.build:verbosity", "quiet") == "verbose":
            tc.make_args.append("VERBOSE=1")
        tc.generate()

    def build(self):
        with chdir(self, self.source_folder):
            autotools = Autotools(self)
            autotools.make()

    def package(self):
        copy(self, "LICENSE.txt", self.source_folder, os.path.join(self.package_folder, "licenses"))
        with chdir(self, self.source_folder):
            autotools = Autotools(self)
            autotools.install(args=[f"PREFIX={self.package_folder}"])
        if self.options.shared:
            rm(self, "*_static.a", os.path.join(self.package_folder, "lib"))
        else:
            rm(self, "*.so*", os.path.join(self.package_folder, "lib"))
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))

    def package_info(self):
        self.cpp_info.set_property("pkg_config_name", "nccl")
        self.cpp_info.libs = ["nccl" if self.options.shared else "nccl_static"]
        self.cpp_info.requires = ["cudart::cudart_"]
        if self.options.with_ibverbs:
            self.cpp_info.requires.append("rdma-core::libibverbs")
        if self.options.with_mlx5:
            self.cpp_info.requires.append("rdma-core::libmlx5")
