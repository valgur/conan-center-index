"""
A collection of helper functions for Conan recipes.

You can use them by adding
  python_requires = "conan-utils/latest"
to the top of your ConanFile class, and then calling the functions like this:
  utils = self.python_requires["conan-utils"].module
  utils.limit_build_jobs(self, gb_mem_per_job=4)
"""

import math
import os
import platform
import subprocess
from pathlib import Path

from conan import ConanFile
from conan.tools.files import rename

required_conan_version = ">=2.1"


class ConanUtilsPackage(ConanFile):
    name = "conan-utils"
    version = "latest"
    description = "Miscellaneous Conan helper for functions"
    license = "MIT"
    package_type = "python-require"


def fix_msvc_libnames(conanfile: ConanFile, extensions=None, remove_lib_prefix=True):
    """
    Rename all lib*.a files built by Meson to *.lib files when using a cl-like compiler on Windows.
    See https://github.com/mesonbuild/meson/issues/8153 for context.
    """
    if not conanfile.settings.os == "Windows":
        return
    if conanfile.settings.compiler == "msvc" or conanfile.settings.get_safe("compiler.runtime"):
        _fix_libnames(conanfile, conanfile.package_folder, extensions, remove_lib_prefix)


def _fix_libnames(conanfile: ConanFile, lib_dir, extensions=None, remove_lib_prefix=True):
    extensions = extensions or [".a"]
    for ext in extensions:
        for lib_path in sorted(Path(lib_dir).rglob(f"*{ext}")):
            libname = lib_path.name[0:-len(ext)]
            if remove_lib_prefix and libname.startswith("lib"):
                libname = libname[3:]
            rename(conanfile, lib_path, lib_path.parent / f"{libname}.lib")


def limit_build_jobs(conanfile: ConanFile, gb_mem_per_job: float):
    """
    Limit the number of build jobs based on available memory.
    :param gb_mem_per_job: Memory in GB that each job is expected to use at their peak.
    """
    mem_free_gb = _get_free_memory_gb()
    max_jobs = max(math.floor(mem_free_gb / gb_mem_per_job), 1)
    if int(conanfile.conf.get("tools.build:jobs", default=os.cpu_count())) > max_jobs:
        conanfile.output.warning(f"Limiting the number of build jobs to {max_jobs} "
                                 f"to fit the available {mem_free_gb:.1f} GB of memory "
                                 f"with {gb_mem_per_job} GB per job.")
        conanfile.conf.define("tools.build:jobs", max_jobs)


def _get_free_memory_gb():
    try:
        import psutil
        return psutil.virtual_memory().available / 1024**3
    except:
        pass
    try:
        system = platform.system()
        if system == "Linux":
            for l in open("/proc/meminfo"):
                if l.startswith("MemAvailable:"):
                    return int(l.split()[1]) / 1024**2
        elif system in ("Darwin", "FreeBSD"):
            page_size = os.sysconf("SC_PAGE_SIZE") or os.sysconf("SC_PAGESIZE")
            if not page_size:
                return 0
            pages = 0
            for key in [
                    "vm.stats.vm.v_free_count",
                    "vm.stats.vm.v_inactive_count",
                    "vm.stats.vm.v_speculative_count",  # Darwin
                    "vm.stats.vm.v_cache_count",        # FreeBSD
            ]:
                try:
                    out = subprocess.check_output(["sysctl", "-n", key])
                    pages += int(out.strip())
                except Exception:
                    pass
            return pages * page_size / 1024**3
        elif system == "Windows":
            import ctypes
            class MEMORYSTATUSEX(ctypes.Structure):
                _fields_ = [("dwLength", ctypes.c_uint32),
                            ("dwMemoryLoad", ctypes.c_uint32),
                            ("ullTotalPhys", ctypes.c_uint64),
                            ("ullAvailPhys", ctypes.c_uint64),
                            ("ullTotalPageFile", ctypes.c_uint64),
                            ("ullAvailPageFile", ctypes.c_uint64),
                            ("ullTotalVirtual", ctypes.c_uint64),
                            ("ullAvailVirtual", ctypes.c_uint64),
                            ("sullAvailExtendedVirtual", ctypes.c_uint64)]
            mem_status = MEMORYSTATUSEX()
            mem_status.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(mem_status))
            return mem_status.ullAvailPhys / 1024**3
    except:
        pass
    return 0
