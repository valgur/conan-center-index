import json
import re
from functools import cached_property
from pathlib import Path
from tempfile import TemporaryDirectory

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.env import Environment
from conan.tools.files import download, get
from conan.tools.gnu import AutotoolsToolchain


class NvccToolchain:
    def __init__(self, conanfile: ConanFile):
        self.conanfile = conanfile

        if not self.conanfile.settings.get_safe("cuda.version"):
            raise ConanInvalidConfiguration("'cuda.version' setting must be defined, e.g. 'cuda.version=12.1'.")
        if not self.arch_flags:
            raise ConanInvalidConfiguration("No valid CUDA architectures found in 'cuda.architectures' setting. "
                                 "Please specify at least one architecture, e.g. 'cuda.architectures=70,75'.")

        self.cudaflags = []
        self.cudaflags.extend(self.arch_flags)
        if "cudart" in self.conanfile.dependencies.host:
            cudart_info = self.conanfile.dependencies.host["cudart"].cpp_info
            runtime_type = "shared" if self.conanfile.dependencies.host["cudart"].options.shared else "static"
            self.cudaflags.append(f"--cudart={runtime_type}")
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
            assert re.match(r"\d\d\d?[a-z]?", arch), f"Invalid CUDA architecture value: {arch}"
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


def validate_cuda_settings(conanfile: ConanFile):
    NvccToolchain(conanfile)


def cuda_platform_id(settings):
    if settings.arch == "armv8" and settings.get_safe("arch.cuda_platform") == "sbsa":
        if settings.os != "Linux":
            raise ConanInvalidConfiguration(f"Invalid OS for cuda.platform=sbsa: {settings.os}")
        return "linux-sbsa"
    return {
        ("Windows", "x86_64"): "windows-x86_64",
        ("Linux", "x86_64"): "linux-x86_64",
        ("Linux", "armv8"): "linux-aarch64",
    }.get((str(settings.os), str(settings.arch)))


_redistrib_info_cache = {}


def _fetch_redistrib_info(conanfile):
    url = conanfile.conan_data["sources"][conanfile.version]["url"]
    redistrib_info = _redistrib_info_cache.get(url)
    if not redistrib_info:
        with TemporaryDirectory() as td:
            temp_path = Path(td, "conan_cuda_redist.json")
            download(conanfile, **conanfile.conan_data["sources"][conanfile.version], filename=temp_path)
            redistrib_info = json.loads(temp_path.read_text(encoding="utf8"))
        _redistrib_info_cache[url] = redistrib_info
    return redistrib_info


def get_cuda_package_info(conanfile: ConanFile, package_name: str):
    redistrib_info = _fetch_redistrib_info(conanfile)
    package_info = redistrib_info[package_name]
    assert package_info["version"] == conanfile.version
    return package_info


def validate_cuda_package(conanfile: ConanFile, package_name: str):
    platform_id = cuda_platform_id(conanfile.settings)
    if platform_id is None:
        raise ConanInvalidConfiguration(f"Unsupported platform: {conanfile.settings.os}/{conanfile.settings.arch}")
    package_info = get_cuda_package_info(conanfile, package_name)
    if platform_id not in package_info:
        raise ConanInvalidConfiguration(f"Unsupported platform {platform_id} for CUDA package '{package_name}'")


def download_cuda_package(conanfile: ConanFile, package_name: str, scope="host", destination=None, **kwargs):
    destination = destination or conanfile.source_folder
    if scope == "host":
        settings = conanfile.settings
    elif scope == "build":
        settings = conanfile.settings_build
    elif scope == "target":
        settings = conanfile.settings_target
    else:
        raise ConanInvalidConfiguration(f"Unknown scope: {scope}")
    package_info = get_cuda_package_info(conanfile, package_name)
    archive_info = package_info[cuda_platform_id(settings)]
    url = "https://developer.download.nvidia.com/compute/cuda/redist/" + archive_info["relative_path"]
    sha256 = archive_info["sha256"]
    get(conanfile, url, sha256=sha256, strip_root=True, destination=destination, **kwargs)


__all__ = [
    "NvccToolchain",
    "validate_cuda_settings",
    "cuda_platform_id",
    "get_cuda_package_info",
    "validate_cuda_package",
    "download_cuda_package",
]
