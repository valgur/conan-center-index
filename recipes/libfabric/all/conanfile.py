import os
from functools import cached_property

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.apple import fix_apple_shared_install_name
from conan.tools.build import cross_building
from conan.tools.env import VirtualRunEnv
from conan.tools.files import *
from conan.tools.gnu import Autotools, AutotoolsDeps, GnuToolchain
from conan.tools.layout import basic_layout
from conan.tools.scm import Version

required_conan_version = ">=2.1"


class LibfabricConan(ConanFile):
    name = "libfabric"
    description = ("Libfabric, also known as Open Fabrics Interfaces (OFI), "
                   "defines a communication API for high-performance parallel and distributed applications.")
    license = ("BSD-2-Clause", "GPL-2.0-or-later")
    homepage = "http://libfabric.org"
    topics = ("fabric", "rdma", "communication", "distributed-computing", "hpc")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type", "cuda"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "cuda": [True, False],
        "dmabuf_peer_mem": [True, False],
        "efa": [True, False],
        "gdrcopy": [True, False],
        "hook_debug": [True, False],
        "hook_hmem": [True, False],
        "lnx": [True, False],
        "lpp": [True, False],
        "lttng": [True, False],
        "monitor": [True, False],
        "mrail": [True, False],
        "numa": [True, False],
        "opx": [True, False],
        "perf": [True, False],
        "profile": [True, False],
        "rxd": [True, False],
        "rxm": [True, False],
        "shm": [True, False],
        "sm2": [True, False],
        "trace": [True, False],
        "ucx": [True, False],
        "uring": [True, False],
        "verbs": [True, False],
        "xpmem": [True, False],
        "ze": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "cuda": False,
        "dmabuf_peer_mem": True,
        "efa": True,
        "gdrcopy": False,
        "hook_debug": True,
        "hook_hmem": True,
        "lnx": True,
        "lpp": True,
        "lttng": False,
        "monitor": True,
        "mrail": True,
        "numa": True,
        "opx": False,
        "perf": True,
        "profile": True,
        "rxd": True,
        "rxm": True,
        "shm": True,
        "sm2": True,
        "trace": True,
        "ucx": False,
        "uring": True,
        "verbs": True,
        "xpmem": True,
        "ze": False,
    }
    implements = ["auto_shared_fpic"]
    languages = ["C"]

    python_requires = "conan-cuda/latest"

    @cached_property
    def cuda(self):
        return self.python_requires["conan-cuda"].module.Interface(self)

    def config_options(self):
        if Version(self.version) < "2.0":
            del self.options.lpp
            del self.options.monitor
            del self.options.lnx

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")
        if not self.options.cuda:
            del self.settings.cuda
            del self.options.gdrcopy
        if not self.options.opx:
            del self.options.numa
        if self.options.ucx:
            if self.options.cuda:
                self.options["openucx"].cuda = True
            if self.options.get_safe("gdrcopy"):
                self.options["openucx"].gdrcopy = True
            if self.options.xpmem:
                self.options["openucx"].xpmem = True
            if self.options.ze:
                self.options["openucx"].ze = True

    def requirements(self):
        if self.options.efa or self.options.verbs:
            self.requires("rdma-core/[*]")
        if self.options.cuda:
            self.cuda.requires("cudart")
            self.cuda.requires("nvml-stubs")
            if self.options.gdrcopy:
                self.requires("gdrcopy/[^2.5]")
        if self.options.lttng:
            self.requires("lttng-ust/[^2.13]")
        if self.options.get_safe("numa"):
            self.requires("libnuma/[^2.0.14]")
        if self.options.ucx:
            self.requires("openucx/[^1.19.0]")
        if self.options.uring:
            self.requires("liburing/[^2.4]")
        if self.options.xpmem:
            self.requires("xpmem/[^2.6.5]")
        if self.options.ze:
            self.requires("level-zero/[^1.17]")

    def layout(self):
        basic_layout(self, src_folder="src")

    def validate(self):
        if self.settings.os != "Linux":
            # TODO: libfabric provides msbuild project files for Windows
            raise ConanInvalidConfiguration("Only Linux is supported")

    def build_requirements(self):
        self.tool_requires("libtool/[^2.4.7]")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        if not cross_building(self):
            VirtualRunEnv(self).generate(scope="build")

        yes_no = lambda val: "yes" if val else "no"
        root_no = lambda pkg, val: self.dependencies[pkg].package_folder if val else "no"
        tc = GnuToolchain(self)
        tc.configure_args["--enable-option-checking"] = "yes"
        tc.configure_args["--enable-debug"] = yes_no(self.settings.build_type == "Debug")
        tc.configure_args["--enable-cxi"] = "no"
        tc.configure_args["--enable-dmabuf_peer_mem"] = yes_no(self.options.dmabuf_peer_mem)
        tc.configure_args["--enable-efa"] = yes_no(self.options.efa)
        tc.configure_args["--enable-hook_debug"] = yes_no(self.options.hook_debug)
        tc.configure_args["--enable-hook_hmem"] = yes_no(self.options.hook_hmem)
        tc.configure_args["--enable-mrail"] = yes_no(self.options.mrail)
        tc.configure_args["--enable-opx"] = yes_no(self.options.opx)
        tc.configure_args["--enable-perf"] = yes_no(self.options.perf)
        tc.configure_args["--enable-profile"] = yes_no(self.options.profile)
        tc.configure_args["--enable-psm2"] = "no"
        tc.configure_args["--enable-psm3"] = "no"
        tc.configure_args["--enable-rxd"] = yes_no(self.options.rxd)
        tc.configure_args["--enable-rxm"] = yes_no(self.options.rxm)
        tc.configure_args["--enable-shm"] = yes_no(self.options.shm)
        tc.configure_args["--enable-sm2"] = yes_no(self.options.sm2)
        tc.configure_args["--enable-sockets"] = "yes"
        tc.configure_args["--enable-tcp"] = "yes"
        tc.configure_args["--enable-trace"] = yes_no(self.options.trace)
        tc.configure_args["--enable-ucx"] = yes_no(self.options.ucx)
        tc.configure_args["--enable-udp"] = "yes"
        tc.configure_args["--enable-usnic"] = "no"  # requires infiniband driver headers
        tc.configure_args["--enable-verbs"] = yes_no(self.options.verbs)
        tc.configure_args["--enable-xpmem"] = root_no("xpmem", self.options.xpmem)
        tc.configure_args["--with-cuda"] = root_no("cudart", self.options.cuda)
        tc.configure_args["--with-curl"] = root_no("libcurl", False)  # cxi dependency
        tc.configure_args["--with-dsa"] = root_no("dsa", False)
        tc.configure_args["--with-gdrcopy"] = root_no("gdrcopy", self.options.get_safe("gdrcopy"))
        tc.configure_args["--with-json-c"] = root_no("json-c", False)  # cxi dependency
        tc.configure_args["--with-libnl"] = root_no("libnl", False)  # usnic dependency
        tc.configure_args["--with-lttng"] = root_no("lttng-ust", self.options.lttng)
        tc.configure_args["--with-neuron"] = root_no("neuron", False)
        tc.configure_args["--with-numa"] = root_no("libnuma", self.options.get_safe("numa"))  # only used with opx, dsa, psm2, psm3
        tc.configure_args["--with-rocr"] = root_no("rocr", False)
        tc.configure_args["--with-uring"] = root_no("liburing", self.options.uring)
        tc.configure_args["--with-valgrind"] = root_no("valgrind", False)
        tc.configure_args["--with-ze"] = root_no("level-zero", self.options.ze)
        if Version(self.version) >= "2.0":
            tc.configure_args["--enable-lpp"] = yes_no(self.options.lpp)
            tc.configure_args["--enable-monitor"] = yes_no(self.options.monitor)
            tc.configure_args["--enable-lnx"] = yes_no(self.options.lnx)
        tc.generate()

        deps = AutotoolsDeps(self)
        deps.generate()

    def build(self):
        if self.options.cuda and not self.dependencies["cudart"].options.shared:
            replace_in_file(self, os.path.join(self.source_folder, "configure"), "cudart", "cudart_static")
        autotools = Autotools(self)
        autotools.configure()
        autotools.make()

    def package(self):
        copy(self, "COPYING", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder)
        autotools = Autotools(self)
        autotools.install()
        rmdir(self, os.path.join(self.package_folder, "share"))
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))
        rm(self, "*.la", self.package_folder, recursive=True)
        fix_apple_shared_install_name(self)

    def package_info(self):
        self.cpp_info.set_property("pkg_config_name", "libfabric")
        self.cpp_info.libs = ["fabric"]
        if  self.settings.get_safe("compiler.libcxx") == "libstdc++":
            self.cpp_info.system_libs.append("atomic")
