import contextlib
import math
import os
import platform
import subprocess
import sys
import threading
import time

from conan import ConanFile

# Keep the original value in case limit_build_jobs() is applied multiple times
_max_jobs_original = None


def limit_build_jobs(conanfile: ConanFile, gb_mem_per_job: float):
    """
    Limit the number of build jobs based on available memory.
    :param gb_mem_per_job: Memory in GB that each job is expected to use at their peak.
    """
    mem_free_gb = _get_free_memory_gb()
    max_jobs = max(math.floor(mem_free_gb / gb_mem_per_job), 1)
    global _max_jobs_original
    _max_jobs_original = _max_jobs_original or int(conanfile.conf.get("tools.build:jobs", default=os.cpu_count()))
    if _max_jobs_original > max_jobs:
        conanfile.output.warning(f"Limiting the number of build jobs to {max_jobs} "
                                 f"to fit the available {mem_free_gb:.1f} GB of memory "
                                 f"with {gb_mem_per_job} GB per job.")
        conanfile.conf.define("tools.build:jobs", max_jobs)


@contextlib.contextmanager
def monitor_memory_usage(conanfile: ConanFile, log_every_n_seconds: float = None, terminate_threshold_gb: float = 0.5):
    num_jobs = int(conanfile.conf.get("tools.build:jobs", default=os.cpu_count()))
    baseline_mem_usage = _get_free_memory_gb()
    peak_mem_usage = 0
    stop_event = threading.Event()
    def monitor():
        nonlocal peak_mem_usage
        prev_time = 0
        while not stop_event.is_set():
            free = _get_free_memory_gb()
            peak_mem_usage = max(peak_mem_usage, baseline_mem_usage - free)
            if log_every_n_seconds and time.time() - prev_time > log_every_n_seconds:
                conanfile.output.info(f"Peak memory usage: {peak_mem_usage / num_jobs:.2f} GB per job. "
                                     f"Current free memory: {free:.2f} GB")
                prev_time = time.time()
            if terminate_threshold_gb and free < terminate_threshold_gb:
                conanfile.output.error(f"Terminating the build as the free memory is below {terminate_threshold_gb} GB")
                sys.exit(1)
            stop_event.wait(0.1)
    monitor_thread = threading.Thread(target=monitor)
    monitor_thread.start()
    try:
        yield
    finally:
        stop_event.set()
        monitor_thread.join()
        if peak_mem_usage > 0:
            gb_mem_per_job = peak_mem_usage / num_jobs
            conanfile.output.info(f"Detected peak memory usage of {peak_mem_usage:.2f} GB "
                                 f"with {num_jobs} jobs, i.e. {gb_mem_per_job:.2f} GB per job.")


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
