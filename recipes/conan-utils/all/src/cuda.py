import json
import os
import re
import stat
from functools import cached_property
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Union, List

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration, ConanException
from conan.tools.env import Environment
from conan.tools.files import download, get
from conan.tools.gnu import AutotoolsToolchain
from conan.tools.scm import Version

cuda_supported_arch_ranges = {
    9: (30, 70),
    10: (30, 75),
    11: (35, 90),
    12: (50, 121),
    13: (75, None),
}

packages_following_ctk_minor_version = {
    "cublas",
    "cuda-crt",
    "cuda-driver-stubs",
    "cuda-gdb",
    "cuda-opencl",
    "cuda-profiler-api",
    "cuda-sanitizer-api",
    "cudart",
    "cudla",
    "culibos",
    "cupti",
    "npp",
    "nvcc",
    "nvfatbin",
    "nvml-stubs",
    "nvptxcompiler",
    "nvrtc",
    "nvvm",
}
packages_following_ctk_major_version = {
    "cuda-samples",
    "npp",
    "nvjpeg",
}


class NvccToolchain:
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


def validate_cuda_settings(conanfile: ConanFile):
    NvccToolchain(conanfile)


def cuda_platform_id(settings):
    if settings.arch == "armv8" and settings.os == "Linux" and Version(settings.cuda.version) >= "13.0":
        # CUDA 13 unified aarch64 and sbsa platforms into just sbsa, so assume implicit cuda.platform=sbsa for all armv8
        return "linux-sbsa"
    elif settings.get_safe("cuda.platform") == "sbsa":
        if settings.os != "Linux":
            raise ConanInvalidConfiguration(f"Invalid OS for cuda.platform=sbsa: {settings.os}")
        if settings.arch != "armv8":
            raise ConanInvalidConfiguration(f"Invalid architecture for cuda.platform=sbsa: {settings.arch}")
        return "linux-sbsa"
    return {
        ("Windows", "x86_64"): "windows-x86_64",
        ("Linux", "x86_64"): "linux-x86_64",
        ("Linux", "armv8"): "linux-aarch64",
        ("Linux", "ppc64le"): "linux-ppc64le",
    }.get((str(settings.os), str(settings.arch)))


_redistrib_info_cache = {}


def get_cuda_redistrib_info(conanfile):
    url = conanfile.conan_data["sources"][conanfile.version]["url"]
    redistrib_info = _redistrib_info_cache.get(url)
    if not redistrib_info:
        with TemporaryDirectory() as td:
            temp_path = Path(td, "conan_cuda_redist.json")
            download(conanfile, **conanfile.conan_data["sources"][conanfile.version], filename=temp_path)
            redistrib_info = json.loads(temp_path.read_text(encoding="utf8"))
        redistrib_info["base_url"] = conanfile.conan_data["sources"][conanfile.version]["url"].rsplit("/", 1)[0] + "/"
        _redistrib_info_cache[url] = redistrib_info
    return redistrib_info


def get_cuda_package_info(conanfile: ConanFile, package_name: str):
    redistrib_info = get_cuda_redistrib_info(conanfile)
    package_info = redistrib_info[package_name]
    package_info["base_url"] = redistrib_info["base_url"]
    assert package_info["version"] == conanfile.version, f"Version mismatch for {package_name}: {package_info['version']} != {conanfile.version}"
    return package_info

def get_cuda_package_versions(conanfile: ConanFile):
    redistrib_info = get_cuda_redistrib_info(conanfile)
    versions = {pkg: Version(info["version"]) for pkg, info in redistrib_info.items() if isinstance(info, dict)}
    if "release_product" in redistrib_info and redistrib_info["release_product"] not in versions:
        versions[redistrib_info["release_product"]] = redistrib_info["release_label"]
    return versions

def validate_cuda_package(conanfile: ConanFile, package_name: str):
    platform_id = cuda_platform_id(conanfile.settings)
    if platform_id is None:
        raise ConanInvalidConfiguration(f"Unsupported platform: {conanfile.settings.os}/{conanfile.settings.arch}")
    package_info = get_cuda_package_info(conanfile, package_name)
    if "cuda_variant" in package_info:
        cuda_major = conanfile.settings.cuda.version.value.split(".")[0]
        if cuda_major not in package_info["cuda_variant"]:
            supported = ", ".join(f"v{v}" for v in package_info['cuda_variant'])
            suff = "s" if len(package_info['cuda_variant']) > 1 else ""
            raise ConanInvalidConfiguration(f"{conanfile.ref} only supports CUDA major version{suff} {supported} and"
                                            f" is not compatible with cuda.version={conanfile.settings.cuda.version}")
    if conanfile.name in packages_following_ctk_minor_version or package_name in packages_following_ctk_major_version:
        if Version(conanfile.version).major != Version(str(conanfile.settings.cuda.version)).major:
            raise ConanInvalidConfiguration(
                f"Package version is not compatible with cuda.version={conanfile.settings.cuda.version}"
            )
    if platform_id not in package_info:
        raise ConanInvalidConfiguration(f"Unsupported platform {platform_id} for CUDA package '{package_name}'")
    is_static = conanfile.package_type == "static-library" or conanfile.options.get_safe("shared") is False
    libcxx = conanfile.settings.get_safe("compiler.libcxx")
    safe = ["cudart", "culibos", "nvptxcompiler"]  # these don't have a strong dependency on libstdc++
    if conanfile.settings.os == "Linux" and is_static and libcxx not in [None, "libstdc++11"] and conanfile.name not in safe:
        # Most CUDA libraries expose only a C API, so an ABI mismatch between libstdc++ and libc++ is not likely to be an issue.
        # However, linking against both libstdc++ and libc++ simultaneously in a C++ project is not safe.
        conanfile.output.warning(
            f"CUDA Toolkit libraries are built with libstdc++, but compiler.libcxx={libcxx}. "
            f"Using {conanfile.name} in a C++ project is only safe with libcxx=libstdc++11 or with '-o {conanfile.name}/*:shared=False'."
        )


def _chmod_plus_w(path):
    if os.name == "posix":
        os.chmod(path, os.stat(path).st_mode | stat.S_IWUSR)


def download_cuda_package(conanfile: ConanFile, package_name: str, scope="host", destination=None, platform_id=None, **kwargs):
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
    platform_id = platform_id or cuda_platform_id(settings)
    archive_info = package_info[platform_id]
    if "cuda_variant" in package_info:
        cuda_major = conanfile.settings.cuda.version.value.split(".")[0]
        archive_info = archive_info[f"cuda{cuda_major}"]
    url = package_info["base_url"] + archive_info["relative_path"]
    sha256 = archive_info["sha256"]
    get(conanfile, url, sha256=sha256, strip_root=True, destination=destination, **kwargs)
    # Old CTK archives set a read-only flag on LICENSE for some reason. Fix that.
    license_file = os.path.join(destination, "LICENSE")
    if os.path.exists(license_file):
        _chmod_plus_w(license_file)


def check_min_cuda_architecture(conanfile: ConanFile, min_arch: Union[str, int]):
    """Raises a ConanInvalidConfiguration if any of the architectures in 'cuda.architectures' setting
    are below the given minimum architecture.

    :param conanfile: The current recipe object. Always use ``self``.
    :param min_arch: Minimal CUDA architecture to check against, e.g. "70" or "80".
    """
    if not conanfile.settings.get_safe("cuda.architectures"):
        raise ConanInvalidConfiguration("No 'cuda.architectures' setting defined.")
    min_arch = int(min_arch)
    architectures = str(conanfile.settings.cuda.architectures).strip()
    for arch in architectures.split(","):
        if arch == "native":
            # Can't check
            continue
        if arch in ["all", "all-major"]:
            cuda_major = int(Version(conanfile.settings.cuda.version).major.value)
            supported_range = cuda_supported_arch_ranges[cuda_major]
            if min_arch > supported_range[0]:
                raise ConanInvalidConfiguration(
                    f"Can't use cuda.architectures={architectures}: {conanfile.name} requires at least {min_arch},"
                    f" but 'all' will cover {supported_range[0]} to {supported_range[1] or 'latest'}."
                )
        arch = arch.split("-", 1)[0]
        if int(arch) < min_arch:
            raise ConanInvalidConfiguration(
                f"cuda.architectures={architectures} is below the minimum required of {min_arch} by {conanfile.name}."
            )


def require_shared_deps(conanfile: ConanFile, deps: List[str]):
    """Checks if the given dependencies are shared, and raises a ConanInvalidConfiguration if not.
    This is needed for pre-built shared libraries to find their shared dependencies at runtime.

    :param conanfile: The current recipe object. Always use ``self``.
    :param deps: List of dependency names to check.
    """
    for dep_name in deps:
        if dep_name not in conanfile.dependencies.host:
            continue
        dep = conanfile.dependencies.host[dep_name]
        if not dep.options.get_safe("shared", True):
            if "shared" in conanfile.options:
                raise ConanInvalidConfiguration(f"{conanfile.name} requires -o {dep_name}/*:shared=True when -o {conanfile.name}/*:shared=True")
            else:
                raise ConanInvalidConfiguration(f"{conanfile.name} requires -o {dep_name}/*:shared=True")


def get_version_range(package_name, cuda_version):
    """Returns the version range that is compatible with the given CUDA (major) version for a CUDA Toolkit package."""
    cuda_version = Version(str(cuda_version))
    cuda_major = int(cuda_version.major.value)
    if package_name in packages_following_ctk_minor_version:
        if cuda_version.minor is None:
            return f"^{cuda_major}"
        return f"~{cuda_version.major}.{cuda_version.minor}"
    if package_name in packages_following_ctk_major_version:
        return f"^{cuda_major}"
    if package_name == "cuda-cccl":
        if cuda_major >= 13:
            return "^3"
        elif cuda_version >= "12.2":
            return "^2"
        else:
            return "^1"
    if package_name == "cufft":
        return f"^{cuda_major - 1}"
    if package_name == "cufile":
        if cuda_major >= 13:
            return ">=1.15"
        elif cuda_major == 12:
            return ">=1.5 <1.15"
        else:
            return "<1.5"
    if package_name == "curand":
        if cuda_major >= 13:
            return "~10.4"
        elif cuda_major == 12:
            return "~10.3"
        else:
            return "~10.2"
    if package_name == "cusolver":
        return "^12" if cuda_major >= 13 else "^11"
    if package_name == "cusparse":
        if cuda_major >= 13:
            return ">=12.6"
        elif cuda_major == 12:
            return ">=12 <12.6"
        else:
            return "^11"
    raise ConanException(f"Unknown CUDA package name: {package_name}")


def cuda_requires(conanfile: ConanFile, package_name: str, **kwargs):
    """A convenience function to require a CUDA package with the correct version range.
    It will automatically determine the version range based on the cuda.version setting.

    :param conanfile: The current recipe object. Always use ``self``.
    :param package_name: Name of the CUDA package, e.g. "cudart", "cublas", etc.
    :param kwargs: Additional keyword arguments to pass to `conanfile.requires()`.
    """
    version_range = get_version_range(package_name, conanfile.settings.cuda.version)
    conanfile.requires(f"{package_name}/[{version_range}]", **kwargs)


__all__ = [
    "NvccToolchain",
    "validate_cuda_settings",
    "cuda_platform_id",
    "get_cuda_redistrib_info",
    "get_cuda_package_versions",
    "get_cuda_package_info",
    "validate_cuda_package",
    "download_cuda_package",
    "check_min_cuda_architecture",
    "cuda_supported_arch_ranges",
    "require_shared_deps",
    "get_version_range",
    "cuda_requires",
]
