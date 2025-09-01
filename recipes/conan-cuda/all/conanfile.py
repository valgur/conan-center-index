"""
CUDA support functions.

You can use them by adding
```
  python_requires = "conan-cuda/latest"

  @cached_property
  def _cuda(self):
      return self.python_requires["conan-cuda"].module.Interface(self)

  def requires(self):
        self._cuda.requires("cudart")
        # etc.
```
"""

import sys
from functools import partial, cached_property
from pathlib import Path

from conan import ConanFile
from conan.tools.scm import Version

sys.path.append(str(Path(__file__).resolve().parent))


from src.cuda_toolchain import * # NOQA
from src.nvidia_packages import *  # NOQA
from src.utils import *  # NOQA

required_conan_version = ">=2.1"


class ConanCudaPackage(ConanFile):
    name = "conan-cuda"
    version = "latest"
    description = "Functions to support the use of the CUDA language and CUDA Toolkit libraries in Conan recipes."
    license = "MIT"
    package_type = "python-require"
    exports = ["src/*.py"]


class Interface:
    _public_methods = {
        "CudaToolchain",
        "check_min_cuda_architecture",
        "get_version_range",
        "requires",
        "tool_requires",
        "validate_settings",
    }
    _private_methods = {
        "download_package",
        "get_package_info",
        "get_package_versions",
        "get_platform_id",
        "get_redistrib_info",
        "require_shared_deps",
        "validate_package",
    }

    def __init__(self, conanfile, enable_private=False):
        self._conanfile = conanfile
        self._methods = self._public_methods
        if enable_private:
            self._methods |= self._private_methods

    def __getattr__(self, item):
        if item in self._methods:
            return partial(globals()[item], self._conanfile)
        else:
            raise AttributeError(f"No method named '{item}' exists in the conan-cuda interface")

    @cached_property
    def version(self):
        if self._conanfile.name in packages_following_ctk_minor_version:
            v = Version(self._conanfile.version)
        else:
            v = self._conanfile.dependencies["cuda-driver-stubs"].ref.version
        return Version(f"{v.major}.{v.minor}")

    @cached_property
    def architectures(self):
        return str(self._conanfile.settings.cuda.architectures).split(",")
