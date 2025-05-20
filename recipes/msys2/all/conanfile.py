import errno
import os
import shutil
import subprocess
from pathlib import Path

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration, ConanException
from conan.tools.files import *
from conan.tools.layout import basic_layout

required_conan_version = ">=2.1"


class MSYS2Conan(ConanFile):
    name = "msys2"
    description = "MSYS2 is a software distro and building platform for Windows"
    version = "cci.latest"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "http://www.msys2.org"
    license = "BSD 3-Clause"  # only the base installer, not the installed packages
    topics = ("msys", "unix", "subsystem")

    settings = "os", "arch", "compiler", "build_type"
    # "exclude_files", "packages" values are a comma-separated list
    options = {
        "exclude_files": ["ANY"],
        "packages": ["ANY"],
        "no_kill": [True, False],
    }
    default_options = {
        "exclude_files": "*/link.exe",
        # https://packages.msys2.org/packages/base-devel
        "packages": "base-devel",
        "no_kill": False,
    }

    @property
    def _packages(self):
        if self.options.packages:
            return str(self.options.packages).replace(",", " ").split(" ")
        return []

    @property
    def _exclude_files(self):
        if self.options.exclude_files:
            return str(self.options.exclude_files).split(",")
        return []

    def layout(self):
        basic_layout(self, src_folder="src")

    def package_id(self):
        del self.info.settings.compiler
        del self.info.settings.build_type
        del self.info.options.no_kill

    def validate(self):
        if self.settings.os != "Windows":
            raise ConanInvalidConfiguration("Only Windows is supported")
        if self.settings.arch != "x86_64":
            raise ConanInvalidConfiguration("Only Windows x64 is supported")

    def _run_bash(self, cmd, **kwargs):
        return self.run(f'bash -l -c "{cmd}"', cwd=os.path.join(self._msys_root, "usr", "bin"), **kwargs)

    def _pacman(self, args, **kwargs):
        try:
            return self._run_bash(f"pacman --noconfirm {args}", **kwargs)
        except ConanException:
            self.output.warning(f"'pacman --noconfirm {args}' failed")
            packman_log = load(self, os.path.join(self._msys_root, "var", "log", "pacman.log"))
            self.output.warning(f"pacman.log contents:\n{packman_log}")
            raise
        finally:
            # https://github.com/msys2/MSYS2-packages/issues/1966
            if not self.options.no_kill:
                _kill_pacman()

    def _upgrade_packages(self):
        self._pacman("--sync --refresh --sysupgrade --sysupgrade")

    def _install_packages(self, packages):
        self._pacman(f"--sync {' '.join(packages)}")

    def _force_remove_package(self, package):
        if self._pacman(f"--query --quiet {package}", ignore_errors=True, quiet=True) == 0:
            self._pacman(f"--remove --recursive --nodeps --nodeps {package}")

    @property
    def _msys_root(self):
        return os.path.join(self.package_folder, "bin", "msys64")

    def package(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True, destination=self._msys_root)

        # Follows https://www.msys2.org/docs/ci/

        self._run_bash("echo") # Run automatic initial MSYS2 setup

        self._upgrade_packages() # Core update (in case any core packages are outdated)
        self._upgrade_packages() # Normal update

        self._install_packages(self._packages)

        self._force_remove_package("pkgconf")

        # Clear pacman cache
        rmdir(self, os.path.join(self._msys_root, "var"))
        # Don't package /home/%USER%
        rmdir(self, os.path.join(self._msys_root, "home"))
        # Remove any other unwanted files
        for exclude in self._exclude_files:
            for path in Path(self._msys_root).rglob(exclude):
                path.unlink()

        shutil.copytree(os.path.join(self._msys_root, "usr", "share", "licenses"),
                        os.path.join(self.package_folder, "licenses"))

        # create /tmp dir to avoid
        #   bash.exe: warning: could not find /tmp, please create!
        save(self, os.path.join(self._msys_root, "tmp", "dummy"), "")

        # Remove an annoying 'system' flag from /etc/mtab, which raises a prompt when deleting msys2 package files
        self.run(f"attrib -S {os.path.join(self._msys_root, 'etc', 'mtab')}")

    def package_info(self):
        self.cpp_info.libdirs = []
        self.cpp_info.includedirs = []

        msys_bin = os.path.join(self._msys_root, "usr", "bin")
        self.cpp_info.bindirs = [msys_bin]

        self.buildenv_info.define_path("MSYS_ROOT", self._msys_root)
        self.buildenv_info.define_path("MSYS_BIN", msys_bin)

        self.conf_info.define("tools.microsoft.bash:subsystem", "msys2")
        self.conf_info.define("tools.microsoft.bash:path", os.path.join(msys_bin, "bash.exe"))


def _kill_pacman(log_out=True):
    taskkill_exe = os.path.join(os.environ["SystemRoot"], "system32", "taskkill.exe")
    if not os.path.exists(taskkill_exe):
        raise ConanException("Cannot find taskkill.exe")
    if log_out:
        out = subprocess.PIPE
        err = subprocess.STDOUT
    else:
        out = subprocess.DEVNULL
        err = subprocess.PIPE
    for taskkill_cmd in [
        f"{taskkill_exe} /f /t /im pacman.exe",
        f"{taskkill_exe} /f /im gpg-agent.exe",
        f"{taskkill_exe} /f /im dirmngr.exe",
        f'{taskkill_exe} /fi "MODULES eq msys-2.0.dll"',
    ]:
        try:
            proc = subprocess.Popen(taskkill_cmd, stdout=out, stderr=err, bufsize=1)
            proc.wait(timeout=10)
        except OSError as e:
            if e.errno == errno.ENOENT:
                raise ConanException("Cannot kill pacman") from e
