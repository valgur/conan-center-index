import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.files import *
from conan.tools.layout import basic_layout

required_conan_version = ">=2.1"

class ZuluOpenJDK(ConanFile):
    name = "zulu-openjdk"
    description = "A OpenJDK distribution"
    license = "https://www.azul.com/products/zulu-and-zulu-enterprise/zulu-terms-of-use/"
    url = "https://github.com/conan-io/conan-center-index/"
    homepage = "https://www.azul.com"
    topics = ("java", "jdk", "openjdk")
    package_type = "application"
    settings = "os", "arch", "compiler", "build_type"

    @property
    def _jni_folder(self):
        folder = {"Linux": "linux", "Macos": "darwin", "Windows": "win32"}.get(str(self.settings_build.os))
        return os.path.join("include", folder)

    def layout(self):
        basic_layout(self, src_folder="src")

    def package_id(self):
        del self.info.settings.compiler
        del self.info.settings.build_type

    def validate(self):
        supported_archs = ["x86_64", "armv8"]
        if self.settings_build.arch not in supported_archs:
            raise ConanInvalidConfiguration(f"Unsupported Architecture ({self.settings_build.arch}). "
                                            f"This version {self.version} currently only supports {supported_archs}.")
        supported_os = ["Windows", "Macos", "Linux"]
        if self.settings_build.os not in supported_os:
            raise ConanInvalidConfiguration(f"Unsupported os ({self.settings_build.os}). "
                                            f"This package currently only support {supported_os}.")

    def build(self):
        get(self, **self.conan_data["sources"][self.version][str(self.settings_build.os)][str(self.settings_build.arch)], strip_root=True)

    def package(self):
        copy(self, pattern="*", dst=os.path.join(self.package_folder, "bin"),
             src=os.path.join(self.source_folder, "bin"),
             excludes=("msvcp140.dll", "vcruntime140.dll", "vcruntime140_1.dll"))
        copy(self, pattern="*", dst=os.path.join(self.package_folder, "include"),
             src=os.path.join(self.source_folder, "include"))
        copy(self, pattern="*", dst=os.path.join(self.package_folder, "lib"),
             src=os.path.join(self.source_folder, "lib"))
        copy(self, pattern="*", dst=os.path.join(self.package_folder, "res"),
             src=os.path.join(self.source_folder, "conf"))
        # conf folder is required for security settings, to avoid
        # java.lang.SecurityException: Can't read cryptographic policy directory: unlimited
        # https://github.com/conan-io/conan-center-index/pull/4491#issuecomment-774555069
        copy(self, pattern="*", dst=os.path.join(self.package_folder, "conf"),
             src=os.path.join(self.source_folder, "conf"))
        copy(self, pattern="*", dst=os.path.join(self.package_folder, "licenses"),
             src=os.path.join(self.source_folder, "legal"))
        copy(self, pattern="*", dst=os.path.join(self.package_folder, "lib", "jmods"),
             src=os.path.join(self.source_folder, "jmods"))

    def package_info(self):
        self.cpp_info.includedirs.append(self._jni_folder)
        self.cpp_info.libdirs = []
        self.buildenv_info.define_path("JAVA_HOME", self.package_folder)
        self.runenv_info.define_path("JAVA_HOME", self.package_folder)
