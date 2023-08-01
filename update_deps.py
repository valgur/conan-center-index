#!/usr/bin/env python3
# suppress distutils warning
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

import datetime
import re
import subprocess
import sys
from pathlib import Path
from distutils.version import LooseVersion
from conan.tools.scm import Version
import yaml

recipes_dir = Path(__file__).parent.absolute() / "recipes"

def _get_config_versions(config_path):
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
    return list(config["versions"])

def find_latest_version(config_path):
    config_versions = _get_config_versions(config_path)
    # If all versions are in a standard format, sort by version only
    if all(re.fullmatch(r"[\d.]+", v) for v in config_versions):
        return sorted([(LooseVersion(v), v) for v in config_versions], reverse=True)[0][1]
    # Otherwise, sort by commit date, then version
    versions = []
    blame = subprocess.run(["git", "blame", "-e", config_path], capture_output=True, text=True).stdout
    for line in blame.splitlines():
        line = line.split("#")[0].strip()
        if "versions" in line or "folder" in line or line[-1] != ":":
            continue
        # 815109b9a45 (SpaceIm           2022-11-08 20:49:32 +0100 26)   "1.3.5":
        m = re.match(r'^\w+ (?:\S+ )?\(.+\s+(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} [+-]\d{4}) +\d+\) +"?([^"]+)"?:', line)
        if not m:
            print("  Matching failed:", line, file=sys.stderr)
            continue
        date = datetime.datetime.strptime(m.group(1), "%Y-%m-%d %H:%M:%S %z").timestamp()
        version = m.group(2)
        version_sort = LooseVersion(version.replace("cci.", ""))
        versions.append((date, version_sort, version))
    return sorted(versions, reverse=True)[0][-1]


def main(conanfile_path):
    content = Path(conanfile_path).read_text()
    deps = re.findall(r'"([a-z0-9_.-]+)/([a-z0-9_.-]+)"', content)
    for dep, current_version in deps:
        if dep in ["lib", "include", "bin", "src", "share",
                   "etc", "doc", "res", "cmake", ".", ".."]:
            # probably matched a path
            continue
        if len(parts := current_version.rsplit(".")) >= 2:
            if len(parts[0]) >= 4 and len(parts[-1]) <= 3 and parts[-1].isalpha():
                # probably matched a path
                continue
        print(f"  Processing {dep}")
        if current_version in ["system", "cci.latest"]:
            continue
        config_path = recipes_dir / dep / "config.yml"
        if not config_path.exists():
            print(f"  ERROR: {config_path} does not exist", file=sys.stderr)
            continue
        if dep == "openssl":
            latest = "[>=1.1 <4]"
        elif dep == "cmake":
            v = Version(current_version)
            latest = f"[>={v.major}.{v.minor}]"
        else:
            latest = find_latest_version(config_path)
        if latest != current_version:
            content = content.replace(f'"{dep}/{current_version}"', f'"{dep}/{latest}"')
    Path(conanfile_path).write_text(content)


if __name__ == "__main__":
    main(sys.argv[1])
