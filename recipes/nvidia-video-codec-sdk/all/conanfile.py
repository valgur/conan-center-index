import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.files import *
from conan.tools.layout import basic_layout

required_conan_version = ">=2.1"


class NvidiaVideoCodecSdkConan(ConanFile):
    name = "nvidia-video-codec-sdk"
    description = "NVIDIA Video Codec SDK: hardware-accelerated video encode and decode on Windows and Linux"
    license = "DocumentRef-LicenseAgreement.pdf:LicenseRef-NVIDIA-Video-Codec-SDK-End-User-License-Agreement"
    homepage = "https://developer.nvidia.com/video-codec-sdk"
    topics = ("nvidia", "video", "codec", "gpu")
    package_type = "shared-library"
    settings = "os", "arch", "compiler", "build_type", "cuda"
    options = {
        "archive_dir": ["ANY"],
    }
    default_options = {
        "archive_dir": None,
    }

    def layout(self):
        basic_layout(self, src_folder="src")

    def package_id(self):
        del self.info.settings.compiler
        del self.info.settings.build_type
        del self.info.settings.cuda
        del self.info.options.archive_dir

    def requirements(self):
        self.requires(f"cuda-driver-stubs/[~{self.settings.cuda.version}]", transitive_headers=True, transitive_libs=True)

    def validate(self):
        if self.settings.os not in ["Linux", "Windows"]:
            raise ConanInvalidConfiguration("NVIDIA Video Codec SDK is only supported on Linux and Windows.")
        if self.settings.os == "Linux" and self.settings.arch not in ["x86_64", "armv8"]:
            raise ConanInvalidConfiguration("Only x86_64 and armv8 architectures are supported on Linux.")
        if self.settings.os == "Windows" and self.settings.arch not in ["x86_64", "x86"]:
            raise ConanInvalidConfiguration("Only x86_64 and x86 architectures are supported on Windows.")

    @property
    def _file_name(self):
        return f"Video_Codec_SDK_{self.version}.zip"

    def validate_build(self):
        if not self.options.archive_dir:
            raise ConanInvalidConfiguration(
                f"The 'archive_dir' option must be set to a directory path where a '{self._file_name}' file is located"
            )

    def _source(self):
        path = os.path.join(self.options.archive_dir.value, self._file_name)
        check_sha256(self, path, self.conan_data["sources"][self.version]["sha256"])
        unzip(self, path, destination=self.source_folder, strip_root=True)

    def build(self):
        self._source()

    def package(self):
        copy(self, "LicenseAgreement.pdf", self.source_folder, os.path.join(self.package_folder, "licenses"))
        copy(self, "NOTICES.txt", self.source_folder, os.path.join(self.package_folder, "licenses"))
        copy(self, "*", os.path.join(self.source_folder, "Interface"), os.path.join(self.package_folder, "include"))
        if self.settings.os == "Linux":
            arch = "aarch64" if self.settings.arch == "armv8" else "x86_64"
            copy(self, "*", os.path.join(self.source_folder, "Lib", "linux", "stubs", arch), os.path.join(self.package_folder, "lib", "stubs"))
        else:
            arch = "x64" if self.settings.arch == "x86_64" else "Win32"
            copy(self, "*", os.path.join(self.source_folder, "Lib", arch), os.path.join(self.package_folder, "lib"))

    def package_info(self):
        self.cpp_info.components["nvcuvid"].libs = ["nvcuvid"]
        self.cpp_info.components["nvcuvid"].libdirs = ["lib/stubs" if self.settings.os == "Linux" else "lib"]
        self.cpp_info.components["nvcuvid"].bindirs = []
        self.cpp_info.components["nvcuvid"].requires = ["cuda-driver-stubs::cuda-driver-stubs"]

        self.cpp_info.components["nvidia-encode"].libs = ["nvencodeapi" if self.settings.os == "Windows" else "nvidia-encode"]
        self.cpp_info.components["nvidia-encode"].libdirs = ["lib/stubs" if self.settings.os == "Linux" else "lib"]
        self.cpp_info.components["nvidia-encode"].bindirs = []
