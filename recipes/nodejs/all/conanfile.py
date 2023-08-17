import os
import re
from six import StringIO
from conan import ConanFile, conan_version
from conan.tools.scm import Version
from conan.tools.files import copy, get
from conan.errors import ConanInvalidConfiguration

required_conan_version = ">=1.59.0"


class NodejsConan(ConanFile):
    name = "nodejs"
    description = "nodejs binaries for use in recipes"
    license = "MIT"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://nodejs.org"
    topics = ("node", "javascript", "runtime", "pre-built")

    package_type = "application"
    settings = "os", "arch", "compiler", "build_type"

    def layout(self):
        pass

    def package_id(self):
        del self.info.settings.compiler
        del self.info.settings.build_type

    @property
    def _nodejs_arch(self):
        if str(self.settings.os) in ["Linux", "FreeBSD"]:
            if str(self.settings.arch).startswith("armv7"):
                return "armv7"
            if str(self.settings.arch).startswith("armv8") and "32" not in str(self.settings.arch):
                return "armv8"
        return str(self.settings.arch)

    @property
    def _glibc_version(self):
        cmd = ["ldd", "--version"] if conan_version.major == "1" else ["ldd --version"]
        buff = StringIO()
        self.run(cmd, buff)
        return str(re.search(r"GLIBC (\d{1,3}.\d{1,3})", buff.getvalue()).group(1))

    def validate(self):
        if (
            not self.version in self.conan_data["sources"]
            or not str(self.settings.os) in self.conan_data["sources"][self.version]
            or not self._nodejs_arch in self.conan_data["sources"][self.version][str(self.settings.os)]
        ):
            raise ConanInvalidConfiguration(
                "Binaries for this combination of architecture/version/os not available"
            )

        if Version(self.version) >= "18.0.0":
            if str(self.settings.os) in ["Linux", "FreeBSD"]:
                if Version(self._glibc_version) < "2.27":
                    raise ConanInvalidConfiguration(
                        "Binaries for this combination of architecture/version/os not available"
                    )

    def build(self):
        get(
            self,
            **self.conan_data["sources"][self.version][str(self.settings.os)][self._nodejs_arch],
            strip_root=True,
        )

    def package(self):
        copy(self, "LICENSE",
             dst=os.path.join(self.package_folder, "licenses"),
             src=self.source_folder)
        copy(self, "*",
             dst=os.path.join(self.package_folder, "bin"),
             src=os.path.join(self.source_folder, "bin"))
        copy(self, "*",
             dst=os.path.join(self.package_folder, "lib"),
             src=os.path.join(self.source_folder, "lib"))
        copy(self, "node.exe",
             dst=os.path.join(self.package_folder, "bin"),
             src=self.source_folder)
        copy(self, "npm",
             dst=os.path.join(self.package_folder, "bin"),
             src=self.source_folder)
        copy(self, "npx",
             dst=os.path.join(self.package_folder, "bin"),
             src=self.source_folder)

    def package_info(self):
        self.cpp_info.includedirs = []
        self.cpp_info.frameworkdirs = []
        self.cpp_info.libdirs = []
        self.cpp_info.resdirs = []
        bin_dir = os.path.join(self.package_folder, "bin")
        self.output.info("Appending PATH environment variable: {}".format(bin_dir))
        self.env_info.PATH.append(bin_dir)
