import re
from functools import cached_property

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.env import Environment
from conan.tools.gnu import AutotoolsToolchain
from conan.tools.scm import Version

from .utils import cuda_supported_arch_ranges


class CudaToolchain:
    def __init__(self, conanfile: ConanFile, skip_arch_flags=False):
        self.conanfile = conanfile

        cuda_version = self.conanfile.settings.get_safe("cuda.version")
        if not cuda_version:
            raise ConanInvalidConfiguration("'cuda.version' setting must be defined, e.g. 'cuda.version=12.1'.")

        # Allow `del self.settings.cuda.architectures` for packages that only use the cuda/cudart API without building any device code.
        have_architectures = conanfile.settings.get_safe("cuda.architectures") is not None
        skip_arch_flags = skip_arch_flags or not have_architectures
        if have_architectures and not self.arch_flags:
            raise ConanInvalidConfiguration("No valid CUDA architectures found in 'cuda.architectures' setting. "
                                            "Please specify at least one architecture, e.g. 'cuda.architectures=70,75'.")

        self.cudaflags = []
        if not skip_arch_flags:
            self.cudaflags.extend(self.arch_flags)
        if "cudart" in self.conanfile.dependencies.host:
            runtime_type = "shared" if self.conanfile.dependencies.host["cudart"].options.shared else "static"
            self.cudaflags.append(f"--cudart={runtime_type}")
            for pkg in ["cudart", "cuda-crt", "cuda-driver-stubs", "libcudacxx", "thrust", "cub"]:
                if pkg in self.conanfile.dependencies.host:
                    pkg_info = self.conanfile.dependencies.host[pkg].cpp_info
                    for path in pkg_info.libdirs:
                        self.cudaflags.append(f"-L{path}")
                    for path in pkg_info.includedirs:
                        self.cudaflags.append(f"-I{path}")
        self.cudaflags.extend(self.conanfile.conf.get("user.tools.build:cudaflags", check_type=list, default=[]))
        self.extra_cudaflags = []

    @cached_property
    def _host_compiler(self):
        return AutotoolsToolchain(self.conanfile).vars().get("CC", None)

    @cached_property
    def architectures(self):
        return str(self.conanfile.settings.cuda.architectures).strip().split(",")

    @cached_property
    def arch_flags(self):
        # https://docs.nvidia.com/cuda/cuda-compiler-driver-nvcc/#gpu-name-gpuname-arch

        cuda_major = int(Version(self.conanfile.settings.cuda.version).major.value)
        supported_arch_range = cuda_supported_arch_ranges[cuda_major]

        flags = []
        for arch in self.architectures:
            if arch in ["native", "all", "all-major"]:
                flags.append(f"-arch={arch}")
                continue
            virtual = True
            real = True
            if "-" in arch:
                arch, suffix = arch.split("-", 1)
                if suffix == "virtual":
                    real = False
                elif suffix == "real":
                    virtual = False
                else:
                    raise ConanInvalidConfiguration(f"Unknown CUDA architecture suffix: {suffix}")
            assert re.match(r"\d\d\d?[a-z]?", arch), f"Invalid CUDA architecture value: {arch}"

            # Validate architecture
            if int(arch) < supported_arch_range[0]:
                raise ConanInvalidConfiguration(f"CUDA architecture {arch} is no longer supported by CUDA {cuda_major}.")
            if supported_arch_range[1] is not None and int(arch) > supported_arch_range[1]:
                raise ConanInvalidConfiguration(f"CUDA architecture {arch} is not supported by CUDA {cuda_major}.")

            if real and virtual:
                flags.append(f"-gencode=arch=compute_{arch},code=[compute_{arch},sm_{arch}]")
            elif virtual:
                flags.append(f"-gencode=arch=compute_{arch},code=compute_{arch}")
            elif real:
                flags.append(f"-gencode=arch=compute_{arch},code=sm_{arch}")
        return flags

    def environment(self):
        env = Environment()
        flags = " ".join(self.cudaflags + self.extra_cudaflags).strip()
        env.define("NVCC_PREPEND_FLAGS", flags)
        if self._host_compiler:
            env.define_path("NVCC_CCBIN", self._host_compiler)
            # Initialize CMAKE_CUDA_COMPILER
            env.define_path("CUDAHOSTCXX", self._host_compiler)
        # Initialize CMAKE_CUDA_FLAGS.
        env.define("CUDAFLAGS", flags)
        # Initialize CMAKE_CUDA_ARCHITECTURES. Requires CMake >= 3.20.
        env.define("CUDAARCHS", ";".join(self.architectures))
        return env

    def generate(self, env=None, scope="build"):
        env = env or self.environment()
        env.vars(self.conanfile, scope).save_script("nvcc_toolchain")


def validate_settings(conanfile: ConanFile):
    CudaToolchain(conanfile)


__all__ = [
    "CudaToolchain",
    "validate_settings",
]
