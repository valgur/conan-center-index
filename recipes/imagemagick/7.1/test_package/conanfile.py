import json
import os

from conan import ConanFile
from conan.tools.build import can_run
from conan.tools.cmake import cmake_layout, CMake


class TestPackageConan(ConanFile):
    settings = "os", "arch", "compiler", "build_type"
    generators = "CMakeDeps", "CMakeToolchain", "VirtualRunEnv"
    test_type = "explicit"

    def requirements(self):
        self.requires(self.tested_reference_str)

    def layout(self):
        cmake_layout(self)

    def generate(self):
        dependency_opts = {k: str(v) != "False" for k, v in self.dependencies["imagemagick"].options.items() if k.startswith("with_")}
        self.generators_path.joinpath("dependencies.json").write_text(json.dumps(dependency_opts, indent=2, sort_keys=True))

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def test(self):
        if can_run(self):
            bin_path = os.path.join(self.cpp.build.bindir, "test_package")
            self.run(bin_path, env="conanrun")

            dependency_opts = json.loads(self.generators_path.joinpath("dependencies.json").read_text())

            with open("delegates.txt") as f:
                content = f.read().strip()
                delegates = content.split()

            def check(option, token):
                self.output.info(f"checking feature {token}...")
                if dependency_opts.get(option, False):
                    if token not in delegates:
                        raise Exception(f"enabled feature {token} is not available!")
                elif token in delegates:
                    raise Exception(f"disabled feature {token} is available!")
                self.output.info(f"checking feature {token}... OK!")

            check("with_bzlib", "bzlib")
            check("with_cairo", "cairo")
            check("with_djvu", "djvu")
            check("with_dmr", "dmr")
            check("with_dps", "dps")
            check("with_emf", "emf")
            check("with_fftw", "fftw")
            check("with_flif", "flif")
            check("with_fontconfig", "fontconfig")
            check("with_fpx", "fpx")
            check("with_freetype", "freetype")
            check("with_gslib", "gslib")
            check("with_gvc", "gvc")
            check("with_heic", "heic")
            check("with_jbig", "jbig")
            check("with_jpeg", "jpeg")
            check("with_jxl", "jxl")
            check("with_lcms", "lcms")
            check("with_lqr", "lqr")
            check("with_ltdl", "ltdl")
            check("with_lzma", "lzma")
            check("with_openexr", "openexr")
            check("with_openjp2", "jp2")
            check("with_pango", "pangocairo")
            check("with_png", "png")
            check("with_ps", "ps")
            check("with_raqm", "raqm")
            check("with_raw", "raw")
            check("with_rsvg", "rsvg")
            check("with_tiff", "tiff")
            check("with_webp", "webp")
            check("with_wmf", "wmf")
            check("with_x11", "x")
            check("with_xml2", "xml")
            check("with_zlib", "zlib")
            # zstd delegate info is missing:
            # https://github.com/ImageMagick/ImageMagick/blob/7.1.1-22/MagickCore/version.c#L218
            # check("with_zstd", "zstd")
