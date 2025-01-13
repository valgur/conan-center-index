from conan import ConanFile
from conan.tools.files import copy, rename, rm
from conan.tools.build import can_run
from conan.tools.cmake import cmake_layout, CMake
import os


class TestPackageConan(ConanFile):
    settings = "os", "arch", "compiler", "build_type"
    generators = "CMakeDeps", "CMakeToolchain"

    def requirements(self):
        self.requires(self.tested_reference_str)
        if can_run(self):
            self.requires("libpcap/1.10.1")

    def configure(self):
        if can_run(self):
            self.options["libpcap"].shared = True

    def layout(self):
        cmake_layout(self)

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def test(self):
        if can_run(self):
            bindir = self.cpp.build.bindir
            # Use libpcap DLL as a replacement for npcap DLL
            # It will not provide all the functions
            # but it will cover enough to check that what we compiled is correct
            rm(self, "wpcap.dll", bindir)
            libpcap_bin_path = self.dependencies["libpcap"].cpp_info.bindir
            copy(self, "pcap.dll", libpcap_bin_path, os.path.join(self.build_folder, bindir))
            rename(self, os.path.join(bindir, "pcap.dll"), os.path.join(bindir, "wpcap.dll"))

            self.run(os.path.join(bindir, "test_package"), env="conanrun")
