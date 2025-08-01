from functools import cached_property

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.env import Environment
from conan.tools.gnu import AutotoolsToolchain


class NvccToolchain:
    def __init__(self, conanfile: ConanFile):
        self.conanfile = conanfile

        if not self.conanfile.settings.get_safe("cuda"):
            raise ConanInvalidConfiguration("'cuda' setting must be defined, e.g. 'cuda=12.1'.")
        if not self.conanfile.settings.get_safe("cuda.runtime"):
            raise ConanInvalidConfiguration("'cuda.runtime' setting must be defined, e.g. 'cuda.runtime=shared'.")
        if not self.arch_flags:
            raise ConanInvalidConfiguration("No valid CUDA architectures found in 'cuda.architectures' setting. "
                                 "Please specify at least one architecture, e.g. 'cuda.architectures=70,75'.")

        self.cudaflags = []
        self.cudaflags.append(f"--cudart={self.conanfile.settings.cuda.runtime}")
        self.cudaflags.extend(self.arch_flags)
        if "cudart" in self.conanfile.dependencies.host:
            cudart_info = self.conanfile.dependencies.host["cudart"].cpp_info
            self.cudaflags.append(f"-L{cudart_info.libdir}")
            self.cudaflags.append(f"-I{cudart_info.includedir}")
        self.cudaflags.extend(self.conanfile.conf.get("user.tools.build:cudaflags", "").split())
        self.extra_cudaflags = []

    @cached_property
    def architectures(self):
        return str(self.conanfile.settings.cuda.architectures).split(",")

    @cached_property
    def arch_flags(self):
        # https://docs.nvidia.com/cuda/cuda-compiler-driver-nvcc/#gpu-name-gpuname-arch
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
            if real:
                flags.append(f"-gencode=arch=compute_{arch},code=sm_{arch}")
            if virtual:
                flags.append(f"-gencode=arch=compute_{arch},code=compute_{arch}")
        return flags

    def environment(self):
        env = Environment()
        env.define("NVCC_PREPEND_FLAGS", " ".join(self.cudaflags + self.extra_cudaflags).strip())
        cc = AutotoolsToolchain(self.conanfile).vars().get("CC", None)
        if cc:
            env.define_path("NVCC_CCBIN", cc)
        return env

    def generate(self, env=None, scope="build"):
        env = env or self.environment()
        env.vars(self.conanfile, scope).save_script("nvcc_toolchain")


def validate_cuda(conanfile: ConanFile):
    NvccToolchain(conanfile)


def cuda_platform_id(settings):
    if settings.get_safe("cuda.platform") == "sbsa":
        if settings.os != "Linux" or settings.arch != "armv8":
            raise ConanInvalidConfiguration(f"Invalid OS/arch combination for cuda.platform=sbsa: {settings.os}/{settings.arch}")
        return "linux-sbsa"
    return {
        ("Windows", "x86_64"): "windows-x86_64",
        ("Linux", "x86_64"): "linux-x86_64",
        ("Linux", "armv8"): "linux-aarch64",
    }.get((str(settings.os), str(settings.arch)))
