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

    @property
    def _executables(self):
        available = []
        # (executable, option name)
        all_execs = (
            ("gl-info", "gl_info"),
            ("al-info", "al_info"),
            ("distancefieldconverter", "distance_field_converter"),
            ("fontconverter", "font_converter"),
            ("imageconverter", "image_converter"),
            ("sceneconverter", "scene_converter"),
        )
        for executable, opt_name in all_execs:
            try:
                if getattr(self.options["magnum"], opt_name):
                    available.append(executable)
            except ConanException:
                pass
        return available

    def build(self):
        cmake = CMake(self)
        for exec in self._executables:
            cmake.definitions["EXEC_{}".format(exec.replace("-", "_")).upper()] = True
        cmake.definitions["IMPORTER_PLUGINS_FOLDER"] = os.path.join(
            self.deps_user_info["magnum"].plugins_basepath, "importers"
        ).replace("\\", "/")
        cmake.definitions["OBJ_FILE"] = os.path.join(self.source_folder, "triangleMesh.obj").replace(
            "\\", "/"
        )
        cmake.definitions["SHARED_PLUGINS"] = self.options["magnum"].shared_plugins
        cmake.configure()
        cmake.build()

    def test(self):
        if can_run(self):
            for exec in self._executables:
                self.run(f"magnum-{exec} --help")

            bin_path = os.path.join(self.cpp.build.bindir, "test_package")
            self.run(bin_path, env="conanrun")
