from conan import ConanFile
from conan.tools.layout import basic_layout


class TestPackageConan(ConanFile):
    settings = "os", "arch", "compiler", "build_type"
    python_requires = "conan-gnu-triplet/latest"
    python_requires_extend = "conan-gnu-triplet.TripletMixin"

    def layout(self):
        basic_layout(self)

    def test(self):
        print(f"Build triplet: {self.gnu_triplet_build}")
        print(f"Host triplet: {self.gnu_triplet_host}")
        print(f"Target triplet: {self.gnu_triplet_target}")
