import re
import typing
import unittest


def get_gnu_triplet(settings):
    return GNUTriplet.from_settings(settings).triplet


class ArchOs:
    def __init__(self, arch: str, os: str, extra: typing.Optional[typing.Dict[str, str]] = None):
        self.arch = arch
        self.os = os
        self.extra = extra if extra is not None else {}

    def is_compatible(self, triplet: "GNUTriplet") -> bool:
        return self.arch in self.calculate_archs(triplet) and self.os == self.calculate_os(triplet)

    _MACHINE_TO_ARCH_LUT = {
        "arm": "armv7",
        "aarch64": ("armv8", "armv9"),
        "i386": "x86",
        "i486": "x86",
        "i586": "x86",
        "i686": "x86",
        "x86_64": "x86_64",
        "riscv32": "riscv32",
        "riscv64": "riscv64",
    }

    @classmethod
    def calculate_archs(cls, triplet: "GNUTriplet") -> typing.Tuple[str]:
        if triplet.machine == "arm":
            archs = "armv7" + ("hf" if "hf" in triplet.abi else "")
        else:
            archs = cls._MACHINE_TO_ARCH_LUT[triplet.machine]
        if isinstance(archs, str):
            archs = (archs,)
        return archs

    _GNU_OS_TO_OS_LUT = {
        None: "baremetal",
        "android": "Android",
        "mingw32": "Windows",
        "linux": "Linux",
        "freebsd": "FreeBSD",
        "darwin": "Macos",
        "none": "baremetal",
        "unknown": "baremetal",
    }

    @classmethod
    def calculate_os(cls, triplet: "GNUTriplet") -> str:
        if triplet.abi and "android" in triplet.abi:
            return "Android"
        return cls._GNU_OS_TO_OS_LUT[triplet.os]

    @classmethod
    def from_triplet(cls, triplet: "GNUTriplet") -> "ArchOs":
        archs = cls.calculate_archs(triplet)
        _os = cls.calculate_os(triplet)
        extra = {}

        if _os == "Android" and triplet.abi:
            m = re.match(".*([0-9]+)", triplet.abi)
            if m:
                extra["os.api_level"] = m.group(1)

        # Assume first architecture
        return cls(arch=archs[0], os=_os, extra=extra)

    def __eq__(self, other) -> bool:
        if type(self) != type(other):
            return False
        if not (self.arch == other.arch and self.os == other.os):
            return False
        self_extra_keys = set(self.extra.keys())
        other_extra_keys = set(other.extra.keys())
        if (self_extra_keys - other_extra_keys) or (other_extra_keys - self_extra_keys):
            return False
        return True

    def __repr__(self) -> str:
        return f"<{type(self).__name__}:arch='{self.arch}',os='{self.os}',extra={self.extra}>"


class GNUTriplet:
    def __init__(self, machine: str, vendor: typing.Optional[str], os: typing.Optional[str], abi: typing.Optional[str]):
        self.machine = machine
        self.vendor = vendor
        self.os = os
        self.abi = abi

    @property
    def triplet(self) -> str:
        return "-".join(p for p in (self.machine, self.vendor, self.os, self.abi) if p)

    @classmethod
    def from_settings(cls, settings) -> "GNUTriplet":
        archos = ArchOs(str(settings.arch), str(settings.os), extra=dict(settings.values_list))
        gnu_machine = cls.calculate_gnu_machine(archos)
        gnu_vendor = cls.calculate_gnu_vendor(archos)
        gnu_os = cls.calculate_gnu_os(archos)
        gnu_abi = cls.calculate_gnu_abi(archos)
        return cls(gnu_machine, gnu_vendor, gnu_os, gnu_abi)

    @classmethod
    def from_archos(cls, archos: ArchOs) -> "GNUTriplet":
        gnu_machine = cls.calculate_gnu_machine(archos)
        gnu_vendor = cls.calculate_gnu_vendor(archos)
        gnu_os = cls.calculate_gnu_os(archos)
        gnu_abi = cls.calculate_gnu_abi(archos)

        return cls(gnu_machine, gnu_vendor, gnu_os, gnu_abi)

    @classmethod
    def from_text(cls, text: str) -> "GNUTriplet":
        gnu_machine: str
        gnu_vendor: typing.Optional[str]
        gnu_os: typing.Optional[str]
        gnu_abi: typing.Optional[str]

        parts = text.split("-")
        if not 2 <= len(parts) <= 4:
            raise ValueError(
                "Wrong number of GNU triplet components. Count must lie in range [2, 4]. format=$machine(-$vendor)?(-$os)?(-$abi)?"
            )

        gnu_machine = parts[0]
        parts = parts[1:]
        if any(v in parts[-1] for v in cls.KNOWN_GNU_ABIS):
            gnu_abi = parts[-1]
            parts = parts[:-1]
        else:
            gnu_abi = None

        if len(parts) == 2:
            gnu_vendor = parts[0]
            gnu_os = parts[1]
        elif len(parts) == 1:
            if parts[0] in GNUTriplet.UNKNOWN_OS_ALIASES:
                gnu_vendor = None
                gnu_os = parts[0]
            elif parts[0] in cls.OS_TO_GNU_OS_LUT.values():
                gnu_vendor = None
                gnu_os = parts[0]
            else:
                gnu_vendor = parts[0]
                gnu_os = None
        else:
            gnu_vendor = None
            gnu_os = None

        return cls(gnu_machine, gnu_vendor, gnu_os, gnu_abi)

    ARCH_TO_GNU_MACHINE_LUT = {
        "x86": "i686",
        "x86_64": "x86_64",
        "armv7": "arm",
        "armv7hf": "arm",
        "armv8": "aarch64",
        "riscv32": "riscv32",
        "riscv64": "riscv64",
    }

    @classmethod
    def calculate_gnu_machine(cls, archos: ArchOs) -> str:
        return cls.ARCH_TO_GNU_MACHINE_LUT[archos.arch]

    UNKNOWN_OS_ALIASES = (
        "unknown",
        "none",
    )

    OS_TO_GNU_OS_LUT = {
        "baremetal": "none",
        "Android": "linux",
        "FreeBSD": "freebsd",
        "Linux": "linux",
        "Macos": "darwin",
        "Windows": "mingw32",
    }

    @classmethod
    def calculate_gnu_os(cls, archos: ArchOs) -> typing.Optional[str]:
        if archos.os in ("baremetal",):
            if archos.arch in (
                "x86",
                "x86_64",
            ):
                return None
            elif archos.arch in ("riscv32", "riscv64"):
                return "unknown"
        return cls.OS_TO_GNU_OS_LUT[archos.os]

    OS_TO_GNU_VENDOR_LUT = {
        "Windows": "w64",
        "baremetal": None,
    }

    @classmethod
    def calculate_gnu_vendor(cls, archos: ArchOs) -> typing.Optional[str]:
        if archos.os in ("baremetal", "Android"):
            return None
        if archos.os in ("Macos", "iOS", "tvOS", "watchOS"):
            return "apple"
        return cls.OS_TO_GNU_VENDOR_LUT.get(archos.os)

    @staticmethod
    def calculate_gnu_abi(archos: ArchOs) -> typing.Optional[str]:
        if archos.os in ("baremetal",):
            if archos.arch in ("armv7",):
                return "eabi"
            else:
                return "elf"
        abi_start = None
        if archos.os in ("Linux",):
            abi_start = "gnu"
        elif archos.os in ("Android",):
            abi_start = "android"
        else:
            return None
        if archos.arch in ("armv7",):
            abi_suffix = "eabi"
        elif archos.arch in ("armv7hf",):
            abi_suffix = "eabihf"
        else:
            abi_suffix = ""
        if archos.os in ("Android",):
            abi_suffix += str(archos.extra.get("os.api_level", ""))

        return abi_start + abi_suffix

    KNOWN_GNU_ABIS = (
        "android",
        "gnu",
        "eabi",
        "elf",
    )

    def __eq__(self, other: object) -> bool:
        if type(self) != type(other):
            return False
        other: "GNUTriplet"
        return (
            self.machine == other.machine
            and self.vendor == other.vendor
            and self.os == other.os
            and self.abi == other.abi
        )

    def __repr__(self) -> str:
        def x(v):
            if v is None:
                return None
            return f"'{v}'"

        return f"<{type(self).__name__}:machine={x(self.machine)},vendor={x(self.vendor)},os={x(self.os)},abi={x(self.abi)}>"


class _TestOsArch2GNUTriplet(unittest.TestCase):
    def test_linux_x86(self):
        archos = ArchOs(arch="x86", os="Linux")
        self._test_osarch_toGNUTriplet(archos, GNUTriplet(machine="i686", vendor=None, os="linux", abi="gnu"), "i686-linux-gnu")
        self.assertEqual(ArchOs("x86", "Linux"), ArchOs.from_triplet(GNUTriplet.from_text("i386-linux")))
        self.assertEqual(ArchOs("x86", "Linux"), ArchOs.from_triplet(GNUTriplet.from_text("i686-linux")))
        self.assertEqual(GNUTriplet("i486", None, "linux", None), GNUTriplet.from_text("i486-linux"))
        self.assertTrue(archos.is_compatible(GNUTriplet.from_text("i486-linux")))
        self.assertTrue(archos.is_compatible(GNUTriplet.from_text("i486-linux-gnu")))

    def test_linux_x86_64(self):
        self._test_osarch_toGNUTriplet(
            ArchOs(arch="x86_64", os="Linux"),
            GNUTriplet(machine="x86_64", vendor=None, os="linux", abi="gnu"),
            "x86_64-linux-gnu",
        )

    def test_linux_armv7(self):
        archos = ArchOs(arch="armv7", os="Linux")
        self._test_osarch_toGNUTriplet(archos, GNUTriplet(machine="arm", vendor=None, os="linux", abi="gnueabi"), "arm-linux-gnueabi")
        self.assertEqual(GNUTriplet("arm", None, None, "gnueabi"), GNUTriplet.from_text("arm-gnueabi"))
        self.assertEqual(GNUTriplet("arm", None, None, "eabi"), GNUTriplet.from_text("arm-eabi"))
        self.assertEqual(ArchOs("armv7hf", "baremetal"), ArchOs.from_triplet(GNUTriplet.from_text("arm-gnueabihf")))
        self.assertTrue(archos.is_compatible(GNUTriplet.from_text("arm-linux-gnueabi")))
        self.assertTrue(archos.is_compatible(GNUTriplet.from_text("arm-linux-eabi")))
        self.assertFalse(archos.is_compatible(GNUTriplet.from_text("arm-linux-gnueabihf")))
        self.assertFalse(archos.is_compatible(GNUTriplet.from_text("arm-gnueabihf")))

    def test_linux_armv7hf(self):
        archos = ArchOs(arch="armv7hf", os="Linux")
        self._test_osarch_toGNUTriplet(archos, GNUTriplet(machine="arm", vendor=None, os="linux", abi="gnueabihf"), "arm-linux-gnueabihf")
        self.assertEqual(GNUTriplet("arm", None, None, "gnueabihf"), GNUTriplet.from_text("arm-gnueabihf"))
        self.assertEqual(ArchOs("armv7", "baremetal"), ArchOs.from_triplet(GNUTriplet.from_text("arm-gnueabi")))
        self.assertFalse(archos.is_compatible(GNUTriplet.from_text("arm-linux-gnueabi")))
        self.assertFalse(archos.is_compatible(GNUTriplet.from_text("arm-linux-eabi")))
        self.assertTrue(archos.is_compatible(GNUTriplet.from_text("arm-linux-gnueabihf")))
        self.assertFalse(archos.is_compatible(GNUTriplet.from_text("arm-gnueabihf")))

    def test_windows_x86(self):
        self._test_osarch_toGNUTriplet(
            ArchOs(arch="x86", os="Windows"),
            GNUTriplet(machine="i686", vendor="w64", os="mingw32", abi=None),
            "i686-w64-mingw32",
        )

    def test_windows_x86_64(self):
        self._test_osarch_toGNUTriplet(
            ArchOs(arch="x86_64", os="Windows"),
            GNUTriplet(machine="x86_64", vendor="w64", os="mingw32", abi=None),
            "x86_64-w64-mingw32",
        )

    def test_macos_x86_64(self):
        self._test_osarch_toGNUTriplet(
            ArchOs(arch="x86_64", os="Macos"),
            GNUTriplet(machine="x86_64", vendor="apple", os="darwin", abi=None),
            "x86_64-apple-darwin",
        )

    def test_freebsd_x86_64(self):
        self._test_osarch_toGNUTriplet(
            ArchOs(arch="x86_64", os="FreeBSD"),
            GNUTriplet(machine="x86_64", vendor=None, os="freebsd", abi=None),
            "x86_64-freebsd",
        )

    def test_baremetal_x86(self):
        self._test_osarch_toGNUTriplet(
            ArchOs(arch="x86", os="baremetal"),
            GNUTriplet(machine="i686", vendor=None, os=None, abi="elf"),
            "i686-elf",
        )

    def test_baremetal_x86_64(self):
        archos = ArchOs(arch="x86_64", os="baremetal")
        self._test_osarch_toGNUTriplet(archos, GNUTriplet(machine="x86_64", vendor=None, os=None, abi="elf"), "x86_64-elf")
        self.assertTrue(archos.is_compatible(GNUTriplet.from_text("x86_64-elf")))
        self.assertTrue(archos.is_compatible(GNUTriplet.from_text("x86_64-none-elf")))
        self.assertTrue(archos.is_compatible(GNUTriplet.from_text("x86_64-unknown-elf")))

    def test_baremetal_armv7(self):
        archos = ArchOs(arch="armv7", os="baremetal")
        self._test_osarch_toGNUTriplet(archos, GNUTriplet(machine="arm", vendor=None, os="none", abi="eabi"), "arm-none-eabi")
        self.assertTrue(archos.is_compatible(GNUTriplet.from_text("arm-none-eabi")))

    def test_baremetal_armv8(self):
        self._test_osarch_toGNUTriplet(
            ArchOs(arch="armv8", os="baremetal"),
            GNUTriplet(machine="aarch64", vendor=None, os="none", abi="elf"),
            "aarch64-none-elf",
        )

    def test_baremetal_riscv32(self):
        self._test_osarch_toGNUTriplet(
            ArchOs(arch="riscv32", os="baremetal"),
            GNUTriplet(machine="riscv32", vendor=None, os="unknown", abi="elf"),
            "riscv32-unknown-elf",
        )

    def test_baremetal_riscv64(self):
        self._test_osarch_toGNUTriplet(
            ArchOs(arch="riscv64", os="baremetal"),
            GNUTriplet(machine="riscv64", vendor=None, os="unknown", abi="elf"),
            "riscv64-unknown-elf",
        )

    def test_android_armv7(self):
        self._test_osarch_toGNUTriplet(
            ArchOs(arch="armv7", os="Android", extra={"os.api_level": "31"}),
            GNUTriplet(machine="arm", vendor=None, os="linux", abi="androideabi31"),
            "arm-linux-androideabi31",
        )

    def test_android_armv8(self):
        self._test_osarch_toGNUTriplet(
            ArchOs(arch="armv8", os="Android", extra={"os.api_level": "24"}),
            GNUTriplet(machine="aarch64", vendor=None, os="linux", abi="android24"),
            "aarch64-linux-android24",
        )

    def test_android_x86(self):
        self._test_osarch_toGNUTriplet(
            ArchOs(arch="x86", os="Android", extra={"os.api_level": "16"}),
            GNUTriplet(machine="i686", vendor=None, os="linux", abi="android16"),
            "i686-linux-android16",
        )

    def test_android_x86_64(self):
        self._test_osarch_toGNUTriplet(
            ArchOs(arch="x86_64", os="Android", extra={"os.api_level": "29"}),
            GNUTriplet(machine="x86_64", vendor=None, os="linux", abi="android29"),
            "x86_64-linux-android29",
        )
        self.assertEqual(
            ArchOs(arch="x86_64", os="Android", extra={"os.api_level": "25"}),
            ArchOs.from_triplet(GNUTriplet.from_text("x86_64-linux-android29")),
        )

    def _test_osarch_toGNUTriplet(self, archos: ArchOs, gnuobj_expected: GNUTriplet, triplet_expected: str):
        gnuobj = GNUTriplet.from_archos(archos)
        self.assertEqual(gnuobj_expected, gnuobj)
        self.assertEqual(triplet_expected, gnuobj.triplet)
        self.assertEqual(gnuobj_expected, GNUTriplet.from_text(triplet_expected))
        # self.assertEqual(triplet_ref, tools.get_gnu_triplet(archos.os, archos.arch, compiler="gcc"))
