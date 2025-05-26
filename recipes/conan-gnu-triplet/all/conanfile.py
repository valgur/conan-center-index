from functools import cached_property

from conan import ConanFile

required_conan_version = ">=2.1"


class ConanGnuTripletConan(ConanFile):
    name = "conan-gnu-triplet"
    version = "latest"
    description = "Conan helper to determine the GNU triplet based on settings."
    license = "MIT"
    package_type = "python-require"
    exports = ["gnu_triplet.py"]


from gnu_triplet import get_gnu_triplet, GNUTriplet, ArchOs  # NOQA


class TripletMixin:
    @cached_property
    def gnu_triplets(self):
        return {
            "build": get_gnu_triplet(self.settings_build),
            "host": get_gnu_triplet(self.settings),
            "target": get_gnu_triplet(self.settings_target) if self.settings_target else None,
        }

    @property
    def gnu_triplet_build(self):
        return self.gnu_triplets["build"]

    @property
    def gnu_triplet_host(self):
        return self.gnu_triplets["host"]

    @property
    def gnu_triplet_target(self):
        return self.gnu_triplets["target"]
