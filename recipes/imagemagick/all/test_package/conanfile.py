from conan import ConanFile
from conan.tools.build import can_run
from conan.tools.cmake import cmake_layout, CMake
import os


class TestPackageConan(ConanFile):
    settings = "os", "arch", "compiler", "build_type"
    generators = "CMakeDeps", "CMakeToolchain", "VirtualRunEnv"
    test_type = "explicit"

    def requirements(self):
        self.requires(self.tested_reference_str)

    def layout(self):
        cmake_layout(self)

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def test(self):
        if can_run(self):
            bin_path = os.path.join(self.cpp.build.bindir, "test_package")
            self.run(bin_path, env="conanrun")

            with open("delegates.txt") as f:
                content = f.read()

            def check(option, token):
                self.output.info(f"checking feature {token}...")
                if option:
                    if token not in content.split():
                        raise Exception(f"feature {token} wasn't enabled!")
                self.output.info(f"checking feature {token}... OK!")

            check(self.dependencies["imagemagick"].options.with_zlib, "zlib")
            check(self.dependencies["imagemagick"].options.with_bzlib, "bzlib")
            check(self.dependencies["imagemagick"].options.with_lzma, "lzma")
            check(self.dependencies["imagemagick"].options.with_lcms, "lcms")
            check(self.dependencies["imagemagick"].options.with_openexr, "openexr")
            check(self.dependencies["imagemagick"].options.with_heic, "heic")
            check(self.dependencies["imagemagick"].options.with_jbig, "jbig")
            check(self.dependencies["imagemagick"].options.with_jpeg, "jpeg")
            check(self.dependencies["imagemagick"].options.with_openjp2, "jp2")
            check(self.dependencies["imagemagick"].options.with_pango, "pangocairo")
            check(self.dependencies["imagemagick"].options.with_png, "png")
            check(self.dependencies["imagemagick"].options.with_tiff, "tiff")
            check(self.dependencies["imagemagick"].options.with_webp, "webp")
            check(self.dependencies["imagemagick"].options.with_freetype, "freetype")
            check(self.dependencies["imagemagick"].options.with_xml2, "xml")
