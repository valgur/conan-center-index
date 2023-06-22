from conan import ConanFile
from conan.tools.build import build_jobs, can_run
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout
from conan.tools.files import chdir


class TestPackageConan(ConanFile):
    settings = "os", "arch", "compiler", "build_type"
    generators = "CMakeDeps", "VirtualRunEnv"
    test_type = "explicit"

    def layout(self):
        cmake_layout(self)

    def requirements(self):
        self.requires(self.tested_reference_str)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["WITH_MAIN"] = self.dependencies["catch2"].options.with_main
        tc.variables["WITH_BENCHMARK"] = self.dependencies["catch2"].options.get_safe(
            "with_benchmark", False
        )
        tc.variables["WITH_PREFIX"] = self.dependencies["catch2"].options.with_prefix
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def test(self):
        if can_run(self):
            with chdir(self, self.build_folder):
                self.run(
                    f"ctest --output-on-failure -C {self.settings.build_type} -j {build_jobs(self)}",
                    env="conanrun",
                )
