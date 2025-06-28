from conan import ConanFile
from conan.tools.build import can_run
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout
from conan.tools.files import *


class TestPackageConan(ConanFile):
    settings = "os", "arch", "compiler", "build_type"
    generators = "CMakeDeps"

    def layout(self):
        cmake_layout(self)

    def requirements(self):
        self.requires(self.tested_reference_str)

    def generate(self):
        opts = self.dependencies["boost"].options
        tc = CMakeToolchain(self)
        tc.cache_variables["Boost_USE_STATIC_LIBS"] = not opts.get_safe("shared")
        tc.cache_variables["WITH_CHRONO"] = opts.with_chrono
        tc.cache_variables["WITH_COROUTINE"] = opts.with_coroutine
        tc.cache_variables["WITH_FIBER"] = opts.with_fiber
        tc.cache_variables["WITH_JSON"] = opts.get_safe("with_json", False)
        tc.cache_variables["WITH_LOCALE"] = opts.with_locale
        tc.cache_variables["WITH_NOWIDE"] = opts.get_safe("with_nowide", False)
        tc.cache_variables["WITH_NUMPY"] = opts.numpy
        tc.cache_variables["WITH_PROCESS"] = opts.get_safe("with_process", False)
        tc.cache_variables["WITH_PYTHON"] = opts.with_python
        tc.cache_variables["WITH_RANDOM"] = opts.with_random
        tc.cache_variables["WITH_REGEX"] = opts.with_regex
        tc.cache_variables["WITH_STACKTRACE"] = opts.with_stacktrace
        tc.cache_variables["WITH_STACKTRACE_ADDR2LINE"] = self.dependencies["boost"].conf_info.get("user.boost:stacktrace_addr2line_available", False)
        tc.cache_variables["WITH_STACKTRACE_BACKTRACE"] = opts.get_safe("with_stacktrace_backtrace", False)
        tc.cache_variables["WITH_TEST"] = opts.with_test
        tc.cache_variables["WITH_URL"] = opts.get_safe("with_url", True)
        if opts.namespace != "boost" and not opts.namespace_alias:
            tc.cache_variables["BOOST_NAMESPACE"] = opts.namespace
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def test(self):
        if not can_run(self):
            return
        with chdir(self, self.folders.build_folder):
            # When boost and its dependencies are built as shared libraries,
            # the test executables need to locate them. Typically the
            # `conanrun` env should be enough, but this may cause problems on macOS
            # where the CMake installation has dependencies on Apple-provided
            # system libraries that are incompatible with Conan-provided ones.
            # When `conanrun` is enabled, DYLD_LIBRARY_PATH will also apply
            # to ctest itself. Given that CMake already embeds RPATHs by default,
            # we can bypass this by using the `conanbuild` environment on
            # non-Windows platforms, while still retaining the correct behaviour.
            env = "conanrun" if self.settings.os == "Windows" else "conanbuild"
            self.run(f"ctest --output-on-failure -C {self.settings.build_type}", env=env)
