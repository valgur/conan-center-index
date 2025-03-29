import os

from conan import ConanFile
from conan.tools.files import download, rm

required_conan_version = ">=2.0"


class NanopbConan(ConanFile):
    name = "nanopb"
    description = ("Nanopb is a small code-size Protocol Buffers implementation in ansi C. "
                   "It is especially suitable for use in microcontrollers, but fits any memory restricted system.")
    license = "Zlib"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://jpa.kapsi.fi/nanopb/"
    topics = ("protocol-buffers", "protobuf", "microcontrollers")
    package_type = "application"
    settings = "os", "arch", "compiler", "build_type"

    def package_id(self):
        del self.settings.compiler
        del self.settings.build_type

    def build_requirements(self):
        self.tool_requires("cpython/[*]", visible=True)

    @property
    def _site_packages_dir(self):
        python_ver = self.dependencies.build["cpython"].ref.version
        return os.path.join(self.package_folder, "lib", f"python{python_ver.major}.{python_ver.minor}", "site-packages")

    def package(self):
        download(self, **self.conan_data["sources"][self.version]["license"],
                 filename=os.path.join(self.package_folder, "licenses", "LICENSE.txt"))
        pkgs = " ".join([
            f"nanopb=={self.version}",
            # protobuf v6 is too new for nanopb v0.4.9.1
            f"protobuf==5.*",
        ])
        self.run(f'python -m pip install {pkgs} --no-cache-dir --target="{self._site_packages_dir}"')
        rm(self, "*.pyc", self.package_folder, recursive=True)

    def package_info(self):
        self.cpp_info.frameworkdirs = []
        self.cpp_info.libdirs = []
        self.cpp_info.resdirs = []
        self.cpp_info.includedirs = []

        self.buildenv_info.prepend_path("PYTHONPATH", self._site_packages_dir)
        self.runenv_info.prepend_path("PYTHONPATH", self._site_packages_dir)
        self.cpp_info.bindirs = [os.path.join(self._site_packages_dir, "bin")]
