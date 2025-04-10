import os

from conan import ConanFile
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout, CMakeDeps
from conan.tools.files import *
from conan.tools.microsoft import is_msvc, is_msvc_static_runtime

required_conan_version = ">=2.4"


class SoxrConan(ConanFile):
    name = "soxr"
    description = "The SoX Resampler library libsoxr performs fast, high-quality one-dimensional sample rate conversion."
    homepage = "https://sourceforge.net/projects/soxr/"
    topics = ("resampling", "audio", "sample-rate", "conversion")
    license = "LGPL-2.1-or-later"
    url = "https://github.com/conan-io/conan-center-index"
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "with_openmp": [True, False],
        "with_lsr_bindings": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "with_openmp": True,
        "with_lsr_bindings": True,
    }
    implements = ["auto_shared_fpic"]
    languages = ["C"]

    def export_sources(self):
        export_conandata_patches(self)

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        if self.options.with_openmp:
            # not used in public headers
            self.requires("openmp/system")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        apply_conandata_patches(self)

    def generate(self):
        tc = CMakeToolchain(self)
        if is_msvc(self):
            tc.variables["BUILD_SHARED_RUNTIME"] = not is_msvc_static_runtime(self)
        # Disable SIMD based resample engines for Apple Silicon and iOS ARMv8 architecture
        if (self.settings.os == "Macos" or self.settings.os == "iOS") and self.settings.arch == "armv8":
            tc.variables["WITH_CR32S"] = False
            tc.variables["WITH_CR64S"] = False
        tc.variables["BUILD_TESTS"] = False
        tc.variables["WITH_OPENMP"] = self.options.with_openmp
        tc.variables["WITH_LSR_BINDINGS"] = self.options.with_lsr_bindings
        tc.generate()

        deps = CMakeDeps(self)
        deps.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def _extract_pffft_license(self):
        pffft_c = load(self, os.path.join(self.source_folder, "src", "pffft.c"))
        return pffft_c[pffft_c.find("/* Copyright")+3:pffft_c.find("modern CPUs.")+13]

    def package(self):
        copy(self, "COPYING*", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        copy(self, "LICENCE", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        save(self, os.path.join(self.package_folder, "licenses", "LICENSE_pffft"), self._extract_pffft_license())
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "doc"))
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))
        rmdir(self, os.path.join(self.package_folder, "share"))

    def package_info(self):
        # core component
        self.cpp_info.components["core"].set_property("pkg_config_name", "soxr")
        self.cpp_info.components["core"].libs = ["soxr"]
        if self.settings.os in ("FreeBSD", "Linux"):
            self.cpp_info.components["core"].system_libs = ["m"]
        if self.settings.os == "Windows" and self.options.shared:
            self.cpp_info.components["core"].defines.append("SOXR_DLL")
        if self.options.with_openmp:
            self.cpp_info.components["core"].requires.append("openmp::openmp")
        # lsr component
        if self.options.with_lsr_bindings:
            self.cpp_info.components["lsr"].set_property("pkg_config_name", "soxr-lsr")
            self.cpp_info.components["lsr"].libs = ["soxr-lsr"]
            if self.settings.os == "Windows" and self.options.shared:
                self.cpp_info.components["lsr"].defines.append("SOXR_DLL")
            self.cpp_info.components["lsr"].requires = ["core"]
