import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.apple import is_apple_os
from conan.tools.build import can_run
from conan.tools.env import VirtualBuildEnv
from conan.tools.files import chdir, copy, get, rmdir
from conan.tools.gnu import Autotools, AutotoolsToolchain
from conan.tools.layout import basic_layout

required_conan_version = ">=1.53.0"


class ScdocInstallerConan(ConanFile):
    name = "scdoc"
    description = "scdoc is a simple man page generator for POSIX systems written in C99."
    license = "MIT"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://git.sr.ht/~sircmpwn/scdoc"
    topics = ("manpage", "documentation", "posix")

    package_type = "application"
    settings = "os", "arch", "compiler", "build_type"

    def configure(self):
        self.settings.rm_safe("compiler.libcxx")
        self.settings.rm_safe("compiler.cppstd")

    def layout(self):
        basic_layout(self, src_folder="src")

    def package_id(self):
        del self.info.settings.compiler

    def validate(self):
        if self.settings.os == "Windows" or is_apple_os(self):
            raise ConanInvalidConfiguration(f"Builds aren't supported on {self.settings.os}")

    def build_requirements(self):
        if not self.conf.get("tools.gnu:make_program", check_type=str):
            self.tool_requires("make/4.4.1")
        if not can_run(self):
            self.tool_requires(f"scdoc/{self.version}")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        VirtualBuildEnv(self).generate()
        tc = AutotoolsToolchain(self)
        tc.make_args = ["PREFIX=/"]
        if not can_run(self):
            host_scdoc = os.path.join(self.dependencies.build["scdoc"].package_folder, "bin", "scdoc")
            tc.make_args.append(f"HOST_SCDOC={host_scdoc}")
        tc.generate()

    def build(self):
        with chdir(self, self.source_folder):
            autotools = Autotools(self)
            autotools.make()

    def package(self):
        with chdir(self, self.source_folder):
            autotools = Autotools(self)
            autotools.install()
        copy(self, "COPYING",
             dst=os.path.join(self.package_folder, "licenses"),
             src=self.source_folder)
        rmdir(self, os.path.join(self.package_folder, "share"))

    @staticmethod
    def _chmod_plus_x(filename):
        if os.name == "posix":
            os.chmod(filename, os.stat(filename).st_mode | 0o111)

    def package_info(self):
        self.cpp_info.frameworkdirs = []
        self.cpp_info.libdirs = []
        self.cpp_info.resdirs = []
        self.cpp_info.includedirs = []

        scdoc_root = os.path.join(self.package_folder, "bin")
        self._chmod_plus_x(os.path.join(scdoc_root, "scdoc"))
        pkgconfig_variables = {
            "exec_prefix": "${prefix}/bin",
            "scdoc": "${exec_prefix}/scdoc",
        }
        self.cpp_info.set_property(
            "pkg_config_custom_content",
            "\n".join(f"{key}={value}" for key, value in pkgconfig_variables.items()),
        )
