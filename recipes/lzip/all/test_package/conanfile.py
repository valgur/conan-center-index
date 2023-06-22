import os
import shutil

from conan import ConanFile
from conan.tools.build import can_run


class TestPackageConan(ConanFile):
    settings = "os", "arch", "compiler", "build_type"
    generators = "VirtualBuildEnv"
    test_type = "explicit"

    def build_requirements(self):
        self.tool_requires(self.tested_reference_str)

    def test(self):
        if can_run(self):
            lzip = os.path.join(self.deps_cpp_info["lzip"].bin_paths[0], "lzip")
            self.run(f"{lzip} --version")

            shutil.copy(os.path.join(self.source_folder, "conanfile.py"), "conanfile.py")

            sha256_original = sha256sum(self, "conanfile.py")
            self.run(f"{lzip} conanfile.py")
            if not os.path.exists("conanfile.py.lz"):
                raise ConanException("conanfile.py.lz does not exist")
            if os.path.exists("conanfile.py"):
                raise ConanException("copied conanfile.py should not exist anymore")

            self.run(f"{lzip} -d conanfile.py.lz")
            if sha256sum(self, "conanfile.py") != sha256_original:
                raise ConanException("sha256 from extracted conanfile.py does not match original")
