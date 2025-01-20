import os
from pathlib import Path

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.files import copy, get


class GoConan(ConanFile):
    name = "go"
    description = "The Go programming language"
    license = "BSD-3-Clause"
    homepage = "https://go.dev/"
    url = "https://github.com/conan-io/conan-center-index"
    topics = ("language", "compiler", "pre-built")
    package_type = "application"
    settings = "os", "arch", "compiler", "build_type"
    upload_policy = "skip"
    build_policy = "missing"

    def package_id(self):
        del self.info.settings.compiler
        del self.info.settings.build_type

    @property
    def _url(self):
        sources = self.conan_data["sources"][self.version]
        return sources.get(str(self.settings.os), {}).get(str(self.settings.arch))

    def validate(self):
        if not self._url:
            raise ConanInvalidConfiguration(f"Unsupported OS/arch combination: {self.settings.os}/{self.settings.arch}")

    def build(self):
        get(self, **self._url, strip_root=True)

    def package(self):
        copy(self, "LICENSE", self.build_folder, os.path.join(self.package_folder, "licenses"))
        copy(self, "PATENTS", self.build_folder, os.path.join(self.package_folder, "licenses"))
        copy(self, "*", os.path.join(self.build_folder, "bin"), os.path.join(self.package_folder, "bin"))
        copy(self, "*", os.path.join(self.build_folder, "lib"), os.path.join(self.package_folder, "lib"))
        copy(self, "*", os.path.join(self.build_folder, "pkg"), os.path.join(self.package_folder, "pkg"))
        copy(self, "*", os.path.join(self.build_folder, "src"), os.path.join(self.package_folder, "src"))

    def _goos(self, os):
        return {
            "AIX": "aix",
            "Android": "android",
            "DragonFly": "dragonfly",
            "Emscripten": "js",
            "FreeBSD": "freebsd",
            "Linux": "linux",
            "Macos": "darwin",
            "NetBSD": "netbsd",
            "OpenBSD": "openbsd",
            "Plan9": "plan9",
            "SunOS": "solaris",
            "Windows": "windows",
            "iOS": "ios",
        }.get(os)

    def _goarch(self, arch):
        return {
            "x86": "386",
            "x86_64": "amd64",
            "armv6": "arm",
            "armv7": "arm",
            "armv7hf": "arm",
            "armv8": "arm64",
            "sparc": "sparc",
            "sparc64": "sparc64",
            "ppc32": "ppc",
            "ppc64": "ppc64",
            "ppc64le": "ppc64le",
            "riscv32": "riscv",
            "riscv64": "riscv64",
            "s390": "s390",
            "s390x": "s390x",
            "wasm": "wasm",
        }.get(arch)

    def package_info(self):
        self.cpp_info.includedirs = []
        self.cpp_info.libdirs = []
        self.cpp_info.bindirs.append(
            next(Path(self.package_folder, "pkg", "tool").iterdir()).relative_to(self.package_folder)
        )
        self.cpp_info.resdirs = ["lib", "pkg", "src"]

        self.buildenv_info.define_path("GOROOT", self.package_folder)
        settings = self.settings_target if self.settings_target else self.settings
        self.buildenv_info.define("GOOS", self._goos(str(settings.os)))
        self.buildenv_info.define("GOARCH", self._goarch(str(settings.arch)))
