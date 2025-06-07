import os
from pathlib import Path

from conan import ConanFile
from conan.tools.build import cross_building
from conan.tools.env import Environment
from conan.tools.files import *
from conan.tools.gnu import GnuToolchain
from conan.tools.layout import basic_layout

required_conan_version = ">=2.4"


class RustBindgenConan(ConanFile):
    name = "rust-bindgen"
    description = "bindgen automatically generates Rust FFI bindings to C (and some C++) libraries."
    license = "BSD-3-Clause"
    homepage = "https://github.com/rust-lang/rust-bindgen"
    url = "https://github.com/conan-io/conan-center-index"
    topics = ("rust", "ffi", "c-bindings", "c++-bindings")
    package_type = "application"
    settings = "os", "arch", "compiler", "build_type"
    languages = ["C"]
    options = {
        "use_system_libclang": [True, False],
    }
    default_options = {
        "use_system_libclang": False,
    }
    default_build_options = {
        "clang/*:shared": True,
    }

    def config_options(self):
        self.options.use_system_libclang = self.settings.compiler in ["clang", "apple-clang"]

    def layout(self):
        basic_layout(self, src_folder="src")

    def requirements(self):
        if not self.options.use_system_libclang:
            self.requires("clang/[*]")

    def build_requirements(self):
        self.tool_requires("rust/[^1.72]")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        env = Environment()
        # Ensure the correct linker is used, especially when cross-compiling
        target_upper = self.conf.get("user.rust:target_host", check_type=str).upper().replace("-", "_")
        cc = GnuToolchain(self).extra_env.vars(self)["CC"]
        env.define_path(f"CARGO_TARGET_{target_upper}_LINKER", cc)
        # Don't add the Cargo dependencies to a global Cargo cache
        env.define_path("CARGO_HOME", os.path.join(self.build_folder, "cargo"))
        if not self.options.use_system_libclang:
            env.define_path("LIBCLANG_PATH", self.dependencies["clang"].cpp_info.libdir)
        env.vars(self).save_script("cargo_paths")

    @property
    def _build_type_flag(self):
        if self.settings.build_type == "Debug":
            return ""
        return "--release"

    def build(self):
        self.run(f"cargo build {self._build_type_flag} --target-dir {self.build_folder}",
                 cwd=self.source_folder)

    @property
    def _dist_dir(self):
        build_type = "debug" if self.settings.build_type == "Debug" else "release"
        if cross_building(self):
            platform = self.conf.get("user.rust:target_host", check_type=str)
            return Path(self.build_folder, platform, build_type)
        return Path(self.build_folder, build_type)

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        suffix = ".exe" if self.settings.os == "Windows" else ""
        copy(self, "bindgen" + suffix, self._dist_dir, os.path.join(self.package_folder, "bin"))

    def package_info(self):
        self.cpp_info.frameworkdirs = []
        self.cpp_info.libdirs = []
        self.cpp_info.resdirs = []
        self.cpp_info.includedirs = []
