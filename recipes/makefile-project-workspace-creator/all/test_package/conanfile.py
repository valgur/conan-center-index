from conan import ConanFile
from conan.tools.layout import basic_layout
import os


class TestPackageConan(ConanFile):
    settings = "os", "arch", "compiler", "build_type"

    def layout(self):
        basic_layout(self)

    def requirements(self):
        self.requires(self.tested_reference_str)

    def test(self):
        build_vars = self.dependencies[self.tested_reference_str].buildenv_info.vars(self)
        mpc_root = build_vars["MPC_ROOT"]
        assert os.path.exists(os.path.join(mpc_root, "mpc.pl"))
