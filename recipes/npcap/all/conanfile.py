from conan import ConanFile
from conan.tools.files import get, download, copy, collect_libs
from conan.errors import ConanInvalidConfiguration
from os.path import join

required_conan_version = ">=1.47.0"


class NpcapConan(ConanFile):
    name = "npcap"
    description = "Windows port of the libpcap library"
    license = "LicenseRef-NPCAP"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://npcap.com/"
    topics = ("pcap", "windows", "packet-capture")

    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"

    def layout(self):
        pass

    def package_id(self):
        del self.info.settings.compiler
        del self.info.settings.build_type

    def validate(self):
        if self.info.settings.os != "Windows":
            raise ConanInvalidConfiguration(f"{self.ref} requires Windows")

    # do not cache as source, instead, use build folder
    def source(self):
        pass

    def build(self):
        source = self.conan_data["sources"][self.version]
        get(self, **source["sdk"], destination=self.source_folder)
        download(self, filename="LICENSE", **source["license"])

    def package(self):
        copy(self, "LICENSE",
             dst=join(self.package_folder, "licenses"),
             src=self.source_folder)
        copy(self, "*.h",
             dst=join(self.package_folder, "include"),
             src=join(self.source_folder, "Include"))

        if self.settings.arch == "x86_64":
            copy(self, "*.lib",
                 dst=join(self.package_folder, "lib"),
                 src=join(self.source_folder, "Lib", "x64"))
        elif self.settings.arch == "armv8":
            copy(self, "*.lib",
                 dst=join(self.package_folder, "lib"),
                 src=join(self.source_folder, "Lib", "ARM64"))
        else:
            copy(self, "*.lib",
                 dst=join(self.package_folder, "lib"),
                 src=join(self.source_folder, "Lib"))

    def package_info(self):
        self.cpp_info.frameworkdirs = []
        self.cpp_info.bindirs = []
        self.cpp_info.resdirs = []
        self.cpp_info.libs = collect_libs(self)
