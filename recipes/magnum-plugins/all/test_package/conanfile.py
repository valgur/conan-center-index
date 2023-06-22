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
        tc = CMakeToolchain(self)
        tc.variables["IMPORTER_PLUGINS_FOLDER"] = os.path.join(
            self.deps_user_info["magnum-plugins"].plugins_basepath, "importers"
        ).replace("\\", "/")
        # STL file taken from https://www.thingiverse.com/thing:2798332
        tc.variables["CONAN_STL_FILE"] = os.path.join(self.source_folder, "conan.stl").replace("\\", "/")
        tc.variables["SHARED_PLUGINS"] = self.options["magnum-plugins"].shared_plugins
        tc.variables["TARGET_EMSCRIPTEN"] = bool(self.settings.os == "Emscripten")
        cmake.configure()
        cmake.build()

    def test(self):
        if can_run(self):
            bin_path = os.path.join(self.cpp.build.bindir, "test_package")
            self.run(bin_path, env="conanrun")

        if self.settings.os == "Emscripten":
            bin_path = os.path.join(self.cpp.build.bindir, "test_package.js")
            self.run(f"node {bin_path}", env="conanrun")
