#!/usr/bin/env python3

import ast
import inspect
import io
import os
import re
import sys
import textwrap
from pathlib import Path

import black
from conan import ConanFile
from conans.model.version import Version


def extract_definitions(source):
    lines = source.splitlines(keepends=True)
    tree = ast.parse(source)
    definitions = {}
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            lineno = node.lineno
            if "@" in lines[lineno - 2]:
                lineno -= 1
            definitions[node.name] = {
                "type": type(node).__name__,
                "start_line": lineno,
                "end_line": node.end_lineno,
            }
    return definitions


class ConanFileDetails:
    def __init__(self, conanfile_path):
        conanfile_path = Path(conanfile_path)
        conanfile_source = conanfile_path.read_text(encoding="utf-8")
        conanfile_lines = conanfile_source.splitlines(keepends=True)
        # Formatting the file breaks inspect.getsourcefile()
        # conanfile = _format_source(conanfile)
        sys.path.insert(0, str(conanfile_path.parent))
        eval(compile(conanfile_source, str(conanfile_path), "exec"), globals(), globals())
        conanfile_class = [
            value
            for value in globals().values()
            if inspect.isclass(value) and issubclass(value, ConanFile) and value != ConanFile
        ][0]

        defs = extract_definitions(conanfile_source)
        class_def = defs[conanfile_class.__name__]
        defs = {
            name: details
            for name, details in defs.items()
            if details["start_line"] > class_def["start_line"]
            and details["end_line"] <= class_def["end_line"]
        }

        def get_method_source(method):
            if method not in defs:
                raise ValueError(f"Method {method} not found")
            start_line = defs[method]["start_line"]
            end_line = defs[method]["end_line"]
            return "".join(conanfile_lines[start_line - 1 : end_line])

        attrs = {}
        for attr, value in conanfile_class.__dict__.items():
            if attr.startswith("__"):
                continue
            if hasattr(value, "__call__") or isinstance(value, property):
                continue
            if value is not None:
                attrs[attr] = value

        methods = {}
        for method in defs:
            source = get_method_source(method)
            if f"# TODO: fill in {method}" not in source:
                methods[method] = source

        class_details = extract_definitions(conanfile_source)[conanfile_class.__name__]
        self.head: str = "".join(conanfile_lines[: class_details["start_line"] - 1])
        self.tail: str = "".join(conanfile_lines[class_details["end_line"] :])
        self.class_name: str = conanfile_class.__name__
        self.attrs: dict[str, object] = attrs
        self.methods: dict[str, str] = methods

    def is_method_empty(self, method):
        if method not in self.methods:
            return True
        body = self.methods[method]
        body = re.sub(r"#.*", "", body)
        return re.match(r":\s+pass\s*$", body) is not None

    @property
    def is_header_only(self):
        if self.is_application:
            return False
        if "package_info" in self.methods and 'self.cpp_info.libs = ["' in self.methods["package_info"]:
            return False
        if "package_type" in self.attrs:
            return self.attrs["package_type"] == "header-library"
        if "shared" in self.attrs.get("options", {}) or "fPIC" in self.attrs.get("options", {}):
            return False
        if self.attrs.get("no_copy_source") is True:
            return True
        if "package_id" in self.methods:
            return (
                "self.info.header_only()" in self.methods["package_id"]
                or "self.info.clear()" in self.methods["package_id"]
            )
        return False

    @property
    def is_application(self):
        if "package_info" in self.methods and 'self.cpp_info.libs = ["' in self.methods["package_info"]:
            return False
        if "package_type" in self.attrs:
            return self.attrs["package_type"] == "application"
        if self.build_system is not None:
            return False
        if "shared" in self.attrs.get("options", []) or "fPIC" in self.attrs.get("options", []):
            return False
        if "layout" in self.methods and self.is_method_empty("layout"):
            return True
        if "source" in self.methods and self.is_method_empty("source"):
            return True
        if "build" in self.methods and (
            self.is_method_empty("build")
            or '**self.conan_data["sources"][self.version]' in self.methods["build"]
        ):
            return True
        if "package_id" in self.methods and (
            "del self.info.settings.compiler" in self.methods["package_id"]
            or 'self.info.settings.rm_safe("compiler")' in self.methods["package_id"]
        ):
            return True
        if "package_info" in self.methods and (
            "self.cpp_info.libdirs = []" in self.methods["package_info"]
            or "self.cpp_info.includedirs = []" in self.methods["package_info"]
            or "self.env_info.PATH" in self.methods["package_info"]
        ):
            return True
        return False

    @property
    def generators(self):
        if "generate" not in self.methods:
            return set()
        return set(re.findall(r"(\w+(?:Deps|Toolchain))", self.methods["generate"]))

    @property
    def build_system(self):
        generators = self.generators
        build = self.methods.get("build", "")
        if generators.intersection({"AutotoolsDeps", "AutotoolsToolchain"}) or "Autotools" in build:
            return "Autotools"
        if generators.intersection({"BazelDeps", "BazelToolchain"}) or "Bazel" in build:
            return "Bazel"
        if generators.intersection({"CMakeDeps", "CMakeToolchain"}) or "CMake" in build:
            return "CMake"
        if generators.intersection({"MesonToolchain"}) or "Meson" in build:
            return "Meson"
        if generators.intersection({"MSBuildDeps", "MSBuildToolchain"}) or "MSBuild" in build:
            return "MSBuild"
        if generators.intersection({"XCodeDeps", "XCodeToolchain"}) or "XCode" in build:
            return "XCode"
        return None


def _format_source(source):
    mode = black.Mode(
        target_versions={black.TargetVersion.PY311},
        line_length=110,
        magic_trailing_comma=True,
        preview=True,
    )
    try:
        return black.format_file_contents(source, fast=False, mode=mode)
    except black.report.NothingChanged:
        pass
    except Exception:
        print("Failed to format source", file=sys.stderr)
        print(source, file=sys.stderr)
        raise
    return source


def _indent(text, level=1):
    return textwrap.indent(text, "    " * level)


def tidy_conanfile(conanfile_path, write=True):
    conanfile_path = Path(conanfile_path)
    details = ConanFileDetails(conanfile_path)

    warnings = []

    def warn(msg):
        rel_conanfile_path = str(conanfile_path).split(f"recipes{os.sep}", 1)[-1]
        print(f"Warning: {msg} in {rel_conanfile_path}", file=sys.stderr)
        warnings.append(msg)

    is_header_only = details.is_header_only
    is_application = details.is_application
    assert not (is_header_only and is_application)

    # tuple of (attr, is_required)
    attr_order = [
        ("name", True),
        ("description", True),
        ("license", True),
        ("url", True),
        ("homepage", True),
        ("topics", True),
        ("package_type", True),
        ("settings", True),
        ("options", not is_header_only and not is_application),
        ("default_options", not is_header_only and not is_application),
        ("options_description", False),
        ("no_copy_source", is_header_only),
        ("provides", False),
        ("deprecated", False),
    ]
    expected_attrs = {attr for attr, is_required in attr_order}
    disallowed_attrs = [
        "version",
        "user",
        "channel",
        "author",
        "requires",
        "build_requires",
        "tool_requires",
        "test_requires",
        "python_requires",
        "python_requires_extend",
        "exports",
        "exports_sources",
        "conan_data",
        "info",
        "package_id_embed_mode",
        "package_id_non_embed_mode",
        "package_id_unknown_mode",
        "generators",
        "build_policy",
        "win_bash",
        "win_bash_run",
        "source_folder",
        "export_sources_folder",
        "build_folder",
        "package_folder",
        "recipe_folder",
        "folders",
        "cpp",
        "layouts",
        "cpp_info",
        "buildenv_info",
        "runenv_info",
        "conf_info",
        "dependencies",
        "conf",
        "revision_mode",
        "upload_policy",
        "required_conan_version",
        "short_paths",
        "source_subfolder",
        "_source_subfolder",
        "build_subfolder",
        "_build_subfolder",
    ]

    def prepend_to_method(method, prepend):
        return method.replace("self):\n", f"self):\n{_indent(prepend, 2)}\n", 1)

    if is_header_only:
        details.attrs["package_type"] = "header-library"
        details.attrs["no_copy_source"] = True
        if "header-only" not in details.attrs["topics"]:
            details.attrs["topics"] = tuple(list(details.attrs["topics"]) + ["header-only"])
        if "package_info" not in details.methods:
            details.methods["package_info"] = _indent(
                "def package_info(self):\n    self.cpp_info.bindirs = []\n    self.cpp_info.libdirs = []\n"
            )
        elif "self.cpp_info.bindirs = []" not in details.methods["package_info"]:
            details.methods["package_info"] = prepend_to_method(
                details.methods["package_info"], "self.cpp_info.bindirs = []\nself.cpp_info.libdirs = []\n"
            )
        if "package_id" in details.methods:
            details.methods["package_id"] = details.methods["package_id"].replace(
                "self.info.header_only()", "self.info.clear()"
            )
        else:
            details.methods["package_id"] = _indent("def package_id(self):\n    self.info.clear()\n")
    elif is_application:
        details.attrs["package_type"] = "application"
        if "no_copy_source" in details.attrs:
            del details.attrs["no_copy_source"]
        if details.build_system is None and "pre-built" not in details.attrs["topics"]:
            details.attrs["topics"] = tuple(list(details.attrs["topics"]) + ["pre-built"])
        if "package_info" not in details.methods:
            details.methods["package_info"] = "    def package_info(self):\n" + _indent(
                (
                    "self.cpp_info.frameworkdirs = []\n"
                    "self.cpp_info.libdirs = []\n"
                    "self.cpp_info.resdirs ="
                    " []\nself.cpp_info.includedirs = []\n"
                ),
                2,
            )
        else:
            for d in ["frameworkdirs", "libdirs", "resdirs", "includedirs"][::-1]:
                if f"self.cpp_info.{d} = []" not in details.methods["package_info"]:
                    details.methods["package_info"] = prepend_to_method(
                        details.methods["package_info"], f"self.cpp_info.{d} = []"
                    )
        if "package_id" not in details.methods or "settings.compiler" not in details.methods["package_id"]:
            details.methods["package_id"] = _indent(
                "def package_id(self):\n"
                "    del self.info.settings.compiler\n"
                "    del self.info.settings.build_type"
            )
        if details.is_method_empty("build") and not details.is_method_empty("source"):
            details.methods["build"] = details.methods["source"].replace("def source", "def build")
            del details.methods["source"]
    else:
        if "package_type" not in details.attrs:
            details.attrs["package_type"] = "library"
        if "options" not in details.attrs:
            details.attrs["options"] = {}
            details.attrs["default_options"] = {}
        if "shared" not in details.attrs["options"]:
            details.attrs["options"]["shared"] = [True, False]
            details.attrs["default_options"]["shared"] = False
        if "fPIC" not in details.attrs["options"]:
            details.attrs["options"]["fPIC"] = [True, False]
            details.attrs["default_options"]["fPIC"] = True
    details.attrs["settings"] = ("os", "arch", "compiler", "build_type")
    details.attrs["url"] = "https://github.com/conan-io/conan-center-index"

    def reorder_opts(opts):
        new_opts = {}
        if "shared" in opts:
            new_opts["shared"] = opts["shared"]
            del opts["shared"]
        if "fPIC" in opts:
            new_opts["fPIC"] = opts["fPIC"]
            del opts["fPIC"]
        new_opts.update(opts)
        return new_opts

    if "options" in details.attrs:
        details.attrs["options"] = reorder_opts(details.attrs["options"])
        details.attrs["default_options"] = reorder_opts(details.attrs["default_options"])

    result = io.StringIO()

    head = re.sub(r"required_conan_version.+", "", details.head)
    result.write(head)
    if is_header_only:
        min_conan_version = "1.52.0"
    elif is_application:
        min_conan_version = "1.47.0"
    else:
        min_conan_version = "1.53.0"
    if m := re.search(r'required_conan_version = ">=(\d+\.\d+\.\d+)"', details.head):
        cur_min = m.group(1)
        if Version(cur_min) > Version(min_conan_version):
            min_conan_version = cur_min
    result.write(f'\nrequired_conan_version = ">={min_conan_version}"\n')

    result.write(f"class {details.class_name}(ConanFile):\n")

    for attr, is_required in attr_order:
        if attr in details.attrs:
            if attr == "package_type":
                result.write("\n")
            value = details.attrs[attr]
            # Add a comma for formatting with black
            src = re.sub(r"}$", ",}", repr(value))
            result.write(f"    {attr} = {src}\n")
        elif is_required:
            warn(f"Missing required attribute '{attr}'")
    result.write("\n")
    for attr, value in details.attrs.items():
        if attr in expected_attrs:
            continue
        if attr in disallowed_attrs:
            warn(f"Disallowed attribute '{attr} = {repr(value)}'")
            continue

    methods = details.methods
    methods_order = [
        ("_min_cppstd", False),
        ("_minimum_cpp_standard", False),
        ("_compilers_minimum_version", False),
        ("_minimum_compiler_version", False),
        ("_settings_build", False),
        ("_is_mingw", False),
        ("export", False),
        ("export_sources", False),
        ("config_options", not (is_header_only or is_application)),
        ("configure", not (is_header_only or is_application)),
        ("layout", True),
        ("requirements", False),
        ("package_id", is_header_only),
        ("validate", False),
        ("validate_build", False),
        ("build_requirements", False),
        ("system_requirements", False),
        ("source", not is_application),
        ("generate", not (is_header_only or is_application)),
        ("_patch_sources", False),
        ("build", not is_header_only),
        ("test", False),
        ("_extract_license", False),
        ("_create_cmake_module_alias_targets", False),
        ("package", True),
        ("_module_file_rel_path", False),
        ("_variable_file_rel_path", False),
        ("package_info", True),
    ]
    expected_methods = {method for method, is_required in methods_order}

    if "layout" not in methods:
        if details.build_system is None:
            methods["layout"] = _indent("def layout(self):\n    pass\n")
        elif details.build_system == "CMake":
            methods["layout"] = _indent('def layout(self):\n    cmake_layout(self, src_folder="src")\n')
        else:
            methods["layout"] = _indent('def layout(self):\n    basic_layout(self, src_folder="src")\n')

    if "_minimum_compilers_version" in methods:
        methods["_compilers_minimum_version"] = methods["_minimum_compilers_version"]
        del methods["_minimum_compilers_version"]

    if details.build_system == "CMake":
        if details.is_method_empty("generate"):
            methods["generate"] = _indent(
                "def generate(self):\n    tc = CMakeToolchain(self)\n    tc.generate()\n"
            )
        if "CMakeToolchain" not in methods["generate"]:
            methods["generate"] = prepend_to_method(
                methods["generate"], "tc = CMakeToolchain(self)\ntc.generate()\n"
            )
        if not details.is_method_empty("requirements") and "CMakeDeps" not in methods["generate"]:
            methods["generate"] += _indent("tc = CMakeDeps(self)\ntc.generate()\n", 2)

    unexpected_method_groups = {}
    cur_group = []
    for method in methods:
        if method not in expected_methods:
            warn(f"Unexpected method '{method}'")
            cur_group.append(method)
        else:
            if cur_group:
                unexpected_method_groups[method] = cur_group
                cur_group = []

    def add_method(method_name):
        result.write(methods[method_name])
        result.write("\n")

    result.write("\n")
    for method, is_required in methods_order:
        if method in methods:
            for m in unexpected_method_groups.get(method, []):
                add_method(m)
            add_method(method)
        elif is_required:
            if method == "config_options" and (
                "configure" in methods and "self.settings.os" in methods.get("validate", "")
            ):
                continue
            warn(f"Missing required method '{method}'")
            if method == "config_options":
                result.write(_indent("def config_options(self):\n", 1))
                result.write(_indent('if self.settings.os == "Windows":\n    del self.options.fPIC\n', 2))
            elif method == "configure":
                result.write(_indent("def configure(self):\n", 1))
                result.write(_indent('if self.options.shared:\n    self.options.rm_safe("fPIC")\n', 2))
            else:
                result.write(_indent(f"def {method}(self):\n    # TODO: fill in {method}()\n    pass\n"))
    if cur_group:
        for method in cur_group:
            add_method(method)

    result.write("\n")
    result.write(details.tail)

    processed_source = result.getvalue()
    processed_source = re.sub(r"^# Warnings:\n(?:# +.+\n)+", "", processed_source)
    if warnings:
        w = "\n".join(f"#   {warning}" for warning in warnings)
        processed_source = f"# Warnings:\n{w}\n\n{processed_source}"
    processed_source = _format_source(processed_source)
    processed_source = processed_source.replace(
        'settings = ("os", "arch", "compiler", "build_type")',
        'settings = "os", "arch", "compiler", "build_type"',
    )
    processed_source = processed_source.replace("\n\n\nrequired_conan_version", "\n\nrequired_conan_version")

    if write:
        conanfile_path.write_text(processed_source)
    else:
        print(processed_source, end="")


if __name__ == "__main__":
    conanfile_path = sys.argv[1]
    tidy_conanfile(conanfile_path, write=True)
