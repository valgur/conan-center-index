# TODO: verify the Conan v2 migration

import os

from conan import ConanFile
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout
from conan.tools.files import apply_conandata_patches, copy, export_conandata_patches, get, load, save

required_conan_version = ">=1.53.0"


class EazylzmaConan(ConanFile):
    name = "easylzma"
    description = (
        "An easy to use, tiny, public domain, C wrapper library around "
        "Igor Pavlov's work that can be used to compress and extract lzma files"
    )
    license = "Unlicense"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/lloyd/easylzma"
    topics = ("eazylzma", "lzma")

    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
    }

    @property
    def _license_text(self):
        # Extract the License/s from the README to a file
        tmp = load(self, os.path.join("source_subfolder", "README"))
        return tmp[tmp.find("License", 1) : tmp.find("work.", 1) + 5]

    @property
    def _libname(self):
        return "easylzma" if self.options.shared else "easylzma_s"

    def export_sources(self):
        export_conandata_patches(self)

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")
        self.settings.rm_safe("compiler.libcxx")
        self.settings.rm_safe("compiler.cppstd")

    def layout(self):
        cmake_layout(self, src_folder="src")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        extracted_dir = self.name + "-" + self.version
        os.rename(extracted_dir, self.source_folder)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.generate()

    def build(self):
        apply_conandata_patches(self)
        cmake = CMake(self)
        cmake.configure()
        cmake.build(target=self._libname)

    def package(self):
        save(self, os.path.join(self.package_folder, "licenses", "LICENSE"), self._license_text)

        for pattern in ["*.lib", "*.a", "*.so", "*.dylib"]:
            copy(
                self,
                pattern,
                src=self.build_folder,
                dst=os.path.join(self.package_folder, "lib"),
                keep_path=False,
            )
        copy(
            self,
            pattern="*.dll",
            dst=os.path.join(self.package_folder, "bin"),
            src=os.path.join(self.build_folder, "bin"),
            keep_path=False,
        )

        copy(
            self,
            "easylzma/*",
            dst=os.path.join(self.package_folder, "include"),
            src=os.path.join(self.source_folder, "src"),
        )

    def package_info(self):
        self.cpp_info.libs = [self._libname]
        if self.options.shared:
            self.cpp_info.defines = ["EASYLZMA_SHARED"]
        if self.settings.compiler == "Visual Studio":
            if "d" in str(self.settings.compiler.runtime):
                self.cpp_info.defines.append("DEBUG")
