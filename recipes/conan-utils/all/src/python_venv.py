from pathlib import Path

from conan import ConanFile
from conan.tools.env import Environment, VirtualBuildEnv


def _python_executable(conanfile: ConanFile):
    return conanfile.conf.get("user.cpython:python", default="python3", check_type=str)


class PythonVenv:
    """
    Creates and activates a Python virtual environment.
    The main intended use case is to provide build-time Python-based tools and libraries in an isolated environment.
    The default location is <build_folder>/python_venv.
    """

    def __init__(self, conanfile: ConanFile):
        self.conanfile = conanfile

    def generate(self, scope="build", destination=None, system_site_packages=False, upgrade_deps=False):
        default_dir_name = "python_venv_run" if scope == "run" else "python_venv"
        destination = Path(destination) if destination else Path(self.conanfile.build_folder) / default_dir_name
        executable = _python_executable(self.conanfile)
        args = [f'"{executable}"', "-m", "venv", f'"{destination}"']
        if system_site_packages:
            args.append("--system-site-packages")
        if upgrade_deps:
            args.append("--upgrade-deps")
        buildenv_enabled = self.conanfile.virtualbuildenv
        buildenv = VirtualBuildEnv(self.conanfile)
        # Touching the VirtualBuildEnv disables automatic generation, so work around it
        if buildenv_enabled:
            buildenv.generate(scope="build")
        with buildenv.environment().vars(self.conanfile).apply():
            self.conanfile.run(" ".join(args))

        env = Environment()
        env.define_path("VIRTUAL_ENV", str(destination))
        env.prepend_path("PATH", str(destination / "bin"))
        # Setting PYTHONPATH is redundant to VIRTUAL_ENV, but it helps in some edge cases
        # where the original Python interpreter gets picked up instead of the venv one.
        env.prepend_path("PYTHONPATH", str(next(destination.rglob("site-packages"))))
        env.vars(self.conanfile, scope=scope).save_script("python_venv")

        new_exe_path = str(Path(destination, "bin", Path(executable).name))
        self.conanfile.conf.define("user.cpython:python", new_exe_path)


def pip_install(conanfile: ConanFile, pks, cwd=None, **kwargs):
    args = []
    for k, v in kwargs.items():
        if v is True or v is None:
            args.append(f"--{k}")
        elif v is not False:
            args.append(f"--{k}={v}")
    executable = _python_executable(conanfile)
    conanfile.run(f'"{executable}" -m pip install {" ".join(pks)} {" ".join(args)}', scope="build", cwd=cwd)
