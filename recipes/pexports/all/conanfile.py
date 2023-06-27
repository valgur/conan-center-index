# TODO: verify the Conan v2 migration

import contextlib
import os

from conan import ConanFile
from conan.tools.files import apply_conandata_patches, copy, export_conandata_patches, get
from conan.tools.gnu import Autotools, AutotoolsToolchain
from conan.tools.microsoft import unix_path, is_msvc

required_conan_version = ">=1.47.0"


class PExportsConan(ConanFile):
    name = "pexports"
    description = "pexports is a program to extract exported symbols from a PE image (executable)."
    license = "GPL-2.0-or-later"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://sourceforge.net/projects/mingw/files/MinGW/Extension/pexports/"
    topics = ("windows", "dll", "PE", "symbols", "import", "library")

    package_type = "application"
    settings = "os", "arch", "compiler", "build_type"

    @property
    def _settings_build(self):
        return getattr(self, "settings_build", self.settings)

    def export_sources(self):
        export_conandata_patches(self)

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        self.settings.rm_safe("compiler.cppstd")
        self.settings.rm_safe("compiler.libcxx")

    def layout(self):
        None

    def package_id(self):
        del self.info.settings.compiler

    def build_requirements(self):
        self.build_requires("automake/1.16.3")
        if self._settings_build.os == "Windows" and not get_env(self, "CONAN_BASH_PATH"):
            self.build_requires("msys2/cci.latest")

    def source(self):
        filename = "pexports.tar.xz"
        get(self, **self.conan_data["sources"][self.version], filename=filename, strip_root=True)

    @property
    def _user_info_build(self):
        return getattr(self, "user_info_build", self.deps_user_info)

    @contextlib.contextmanager
    def _build_context(self):
        if is_msvc(self):
            with vcvars(self):
                env = {
                    "CC": "{} cl -nologo".format(unix_path(self._user_info_build["automake"].compile)),
                    "LD": "{} link -nologo".format(unix_path(self._user_info_build["automake"].compile)),
                }
                with environment_append(self, env):
                    yield
        else:
            yield

    def generate(self):
        tc = AutotoolsToolchain(self)
        if is_msvc(self):
            tc.defines.append("YY_NO_UNISTD_H")
        tc.generate()

    def build(self):
        apply_conandata_patches(self)
        with self._build_context():
            autotools = Autotools(self)
            autotools.autoreconf()
            autotools.configure()
            autotools.make()

    def package(self):
        copy(self, "COPYING", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        with self._build_context():
            autotools = Autotools(self)
            autotools.install()

    def package_info(self):
        self.cpp_info.libdirs = []

        bin_path = os.path.join(self.package_folder, "bin")
        self.output.info(f"Appending PATH environment variable: {bin_path}")
        self.env_info.PATH.append(bin_path)
