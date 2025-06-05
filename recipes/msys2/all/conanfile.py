import os
import shutil
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
        "packages": ["ANY"],
        "exclude_files": ["ANY"],
    }
    default_options = {
        # https://packages.msys2.org/packages/base-devel
        # GCC is needed for windres https://github.com/conan-io/conan/issues/12691
        "packages": "base-devel,gcc",
        "exclude_files": "*/link.exe",
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

    def export_sources(self):
        export_conandata_patches(self)

    def layout(self):
        basic_layout(self, src_folder="src")

    def package_id(self):
        del self.info.settings.compiler
        del self.info.settings.build_type

    def validate(self):
        if self.settings.os != "Windows":
            raise ConanInvalidConfiguration("Only Windows is supported")
        if self.settings.arch != "x86_64":
            raise ConanInvalidConfiguration("Only Windows x64 is supported")

    def _run_bash(self, cmd, **kwargs):
        return self.run(f'bash -l -c "{cmd}"', cwd=os.path.join(self._msys_root, "usr", "bin"), **kwargs)

    def _pacman(self, args, **kwargs):
        try:
            result = self._run_bash(f"pacman --noconfirm {args}", **kwargs)
        except ConanException:
            self.output.warning(f"'pacman --noconfirm {args}' failed")
            packman_log = load(self, os.path.join(self._msys_root, "var", "log", "pacman.log"))
            self.output.warning(f"pacman.log contents:\n{packman_log}")
            raise
        finally:
            # https://github.com/msys2/MSYS2-packages/issues/1966
            self.run('taskkill /F /FI "MODULES eq msys-2.0.dll"', ignore_errors=True, env=None)
        return result

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

        # Don't generate a home dir with empty .bashrc etc.
        rm(self, "05-home-dir.post", os.path.join(self._msys_root, "etc", "post-install"))

        # Apply speed-up-key-refresh.patch, which speeds up the install quite a bit but is not critical.
        try:
            patch(self, base_path=self._msys_root, patch_file=self.conan_data["patches"][0]["patch_file"])
        except ConanException:
            # Don't fail if the patch is broken due to changes in the nightly release.
            self.output.warning("Could not patch /usr/bin/pacman-key to run key refresh in parallel")
            pass

        self._run_bash("echo") # Run automatic initial MSYS2 setup

        # Follows https://www.msys2.org/docs/ci/
        self._upgrade_packages() # Core update (in case any core packages are outdated)
        self._upgrade_packages() # Normal update

        self._install_packages(self._packages)

        self._force_remove_package("pkgconf")

        # Clear pacman DB entirely
        rmdir(self, os.path.join(self._msys_root, "var"))

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
        self.run(f"attrib -S {os.path.join(self._msys_root, 'etc', 'mtab')}", env=None)

    def package_info(self):
        self.cpp_info.libdirs = []
        self.cpp_info.includedirs = []
        self.cpp_info.bindirs = [os.path.join(self._msys_root, "usr", "bin")]

        self.buildenv_info.define_path("MSYS_ROOT", self._msys_root)

        self.conf_info.define("tools.microsoft.bash:subsystem", "msys2")
        self.conf_info.define("tools.microsoft.bash:path", os.path.join(self._msys_root, "usr", "bin", "bash.exe"))
