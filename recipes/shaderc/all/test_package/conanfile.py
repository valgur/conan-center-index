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
        tc.variables["CMAKE_FIND_ROOT_PATH_MODE_PACKAGE"] = "NONE"
        tc.variables["SHADERC_WITH_SPVC"] = self.dependencies["shaderc"].options.get_safe("spvc", False)
        cmake.configure()
        cmake.build()

    def test(self):
        if can_run(self):
            # Test programs consuming shaderc lib
            bin_path_shaderc_c = os.path.join(self.cpp.build.bindir, "test_package_shaderc_c")
            self.run(bin_path_shaderc_c, env="conanrun")
            bin_path_shaderc_cpp = os.path.join(self.cpp.build.bindir, "test_package_shaderc_cpp")
            self.run(bin_path_shaderc_cpp, env="conanrun")
            # Test glslc executable
            in_glsl_name = os.path.join(self.source_folder, "test_package.vert")
            spv_name = "test_package.spv"
            self.run(f'glslc "{in_glsl_name}" -o {spv_name}', env="conanrun")

            if "spvc" in self.options["shaderc"] and self.dependencies["shaderc"].options.spvc:
                # Test programs consuming shaderc_spvc lib
                bin_path_spvc_c = os.path.join(self.cpp.build.bindir, "test_package_spvc_c")
                self.run(bin_path_spvc_c, env="conanrun")
                bin_path_spvc_cpp = os.path.join(self.cpp.build.bindir, "test_package_spvc_cpp")
                self.run(bin_path_spvc_cpp, env="conanrun")
