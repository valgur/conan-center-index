import os
from functools import cached_property

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.files import *
from conan.tools.layout import basic_layout
from conan.tools.scm import Version

required_conan_version = ">=2.1"


class GccArmPrebuiltConan(ConanFile):
    name = "gcc-arm-prebuilt"
    description = (
        "The GNU Compiler Collection includes front ends for C, "
        "C++, Objective-C, Fortran, Ada, Go, and D, as well as "
        "libraries for these languages (libstdc++,...). "
    )
    topics = ("gcc", "gnu", "compiler", "pre-built")
    homepage = "https://gcc.gnu.org"
    license = "GPL-3.0-only"
    settings = "os", "arch", "compiler", "build_type"
    package_type = "application"
    options = {
        "target_triplet": [None, "ANY"],
        "add_unprefixed_to_path": [True, False],
    }
    default_options = {
        "target_triplet": None,
        "add_unprefixed_to_path": False,
    }
    provides = ["gcc"]

    def config_options(self):
        target_arch = self.settings_target.arch if self.settings_target else self.settings.arch
        triplet = guess_triplet(str(self.settings.os), str(target_arch))
        self.options.target_triplet = triplet
        self.output.info(f"target_triplet={self.options.target_triplet}")

    def package_id(self):
        del self.info.settings.compiler
        del self.info.settings.build_type
        if self.info.settings_target:
            # The platform info is captured in
            #   self.info.options.target_triplet
            self.info.settings_target.clear()

    def layout(self):
        basic_layout(self, src_folder="src")

    @cached_property
    def _host_id(self):
        return get_host_id(str(self.settings.os), str(self.settings.arch))

    @cached_property
    def _triplet(self):
        triplet = str(self.options.target_triplet)
        if Version(self.version) < "9":
            # v8 does not set the vendor part to "none"
            triplet = triplet.replace("-none", "")
        return triplet

    @cached_property
    def _platform_id(self):
        return f"{self._host_id}-{self._triplet}"

    def validate(self):
        if self.settings.os not in ["Linux", "Macos"]:
            raise ConanInvalidConfiguration(f"Unsupported host OS: {self.settings.os}")
        if Version(self.version) >= "11" and self.settings.arch == "x86":
            raise ConanInvalidConfiguration(f"x86 is not supported by GCC {self.version}.")
        if self.settings.arch not in ["x86_64", "armv8"]:
            raise ConanInvalidConfiguration(f"Unsupported host architecture: {self.settings.arch}")
        if self._platform_id not in self.conan_data["sources"][self.version]:
            ids = list(self.conan_data["sources"][self.version])
            supported_triplets = [x.replace(f"{self._host_id}-", "") for x in ids if x.startswith(self._host_id)]
            raise ConanInvalidConfiguration(
                f"Unsupported platform: {self._platform_id}\n"
                f"Supported triplets:\n- {'\n- '.join(supported_triplets)}"
            )

    def package(self):
        get(self, **self.conan_data["sources"][self.version][self._platform_id],
            destination=self.package_folder, strip_root=True)
        mkdir(self, os.path.join(self.package_folder, "licenses"))
        copy(self, "license.txt", self.package_folder, os.path.join(self.package_folder, "licenses"))
        # Contains only some irrelevant Jenkins CI files
        rmdir(self, os.path.join(self.package_folder, "data"))
        rmdir(self, os.path.join(self.package_folder, "share", "doc"))
        rmdir(self, os.path.join(self.package_folder, "share", "info"))
        rmdir(self, os.path.join(self.package_folder, "share", "man"))

    def package_info(self):
        def _add_env_var(var, tool_name):
            self.buildenv_info.define_path(var, os.path.join(self.package_folder, "bin", f"{self._triplet}-{tool_name}"))

        _add_env_var("CC", "gcc")
        _add_env_var("CXX", "g++")
        _add_env_var("FC", "gfortran")
        _add_env_var("CPP", "cpp")
        _add_env_var("CXXCPP", "cpp")

        _add_env_var("ADDR2LINE", "addr2line")
        _add_env_var("AR", "ar")
        _add_env_var("AS", "as")
        _add_env_var("DWP", "dwp")
        _add_env_var("GDB", "gdb")
        _add_env_var("GPROF", "gprof")
        _add_env_var("LD", "ld")
        _add_env_var("NM", "nm")
        _add_env_var("OBJCOPY", "objcopy")
        _add_env_var("OBJDUMP", "objdump")
        _add_env_var("RANLIB", "ranlib")
        _add_env_var("READLINK", "readlink")
        _add_env_var("SIZE", "size")
        _add_env_var("STRINGS", "strings")
        _add_env_var("STRIP", "strip")

        bindir = os.path.join(self.package_folder, "bin")
        self.buildenv_info.prepend_path("PATH", bindir)
        if self.options.add_unprefixed_to_path:
            target_bindir = os.path.join(self.package_folder, self._triplet, "bin")
            self.buildenv_info.prepend_path("PATH", target_bindir)


def is_aarch64(arch):
    return str(arch) in {"armv8", "armv8.3", "arm64", "arm64ec", "aarch64"}


def get_host_id(host_os, host_arch):
    if host_os == "Linux":
        if host_arch == "x86_64":
            return "x86_64"
        elif host_arch == "x86":
            return "i686"
        elif is_aarch64(host_arch):
            return "aarch64"
    elif host_os == "Macos":
        if host_arch == "x86_64":
            return "darwin-x86_64"
        elif is_aarch64(host_arch):
            return "darwin-arm64"
    return None


def guess_triplet(host_os, target_arch):
    if host_os == "Linux":
        if is_aarch64(target_arch):
            return "aarch64-none-linux-gnu"
        else:
            triplet = "arm-none-linux-gnueabi"
            if "hf" in target_arch or target_arch == "armv8_32":
                triplet += "hf"
            return triplet
    else:
        if is_aarch64(target_arch):
            return "aarch64-none-elf"
        else:
            return "arm-none-eabi"
