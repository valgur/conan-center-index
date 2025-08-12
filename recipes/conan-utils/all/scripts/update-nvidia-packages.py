#!/usr/bin/env python3
import concurrent
import re
import textwrap
from hashlib import sha256
from pathlib import Path

import requests
import yaml
from conan.tools.scm import Version
from tqdm.auto import tqdm

script_dir = Path(__file__).parent
recipes_root = script_dir.parent.parent.parent


conanfile_version_ranges = {
    "cudnn/v8": (None, "9.0"),
    "cudnn/all": ("9.0", None),
}
conanfile_policies = {
    "cudnn/v8": "latest",
    "cuda-gdb/all": "latest",
    "cuobjdump/all": "latest",
    "cuxxfilt/all": "latest",
    "nvdisasm/all": "latest",
    "nvprof/all": "latest",
    "nvprune/all": "latest",
}


def find_conanfiles():
    return sorted(f for f in recipes_root.rglob("**/conanfile.py") if not f.parent.name.startswith("test_"))


def get_redist_urls(conandata_path):
    urls = set()
    conandata = yaml.safe_load(conandata_path.read_text(encoding="utf-8"))
    for _, info in conandata["sources"].items():
        urls.add(info["url"].rsplit("/", 1)[0])
    return urls


def find_nvidia_redist_json_packages():
    packages = {}
    pattern = re.compile(r'download_cuda_package\(self, "(\S+)"')
    for conanfile in find_conanfiles():
        content = conanfile.read_text(encoding="utf-8")
        if "download_cuda_package" not in content:
            continue
        conan_pkg_name = conanfile.parent.parent.name
        match conan_pkg_name:
            case "cuda-crt":
                nv_pkg_names = ["nvcc", "cuda-crt"]
            case "nvvm":
                nv_pkg_names = ["nvcc", "nvvm"]
            case "nvptxcompiler":
                nv_pkg_names = ["nvcc", "nvptxcompiler"]
            case "culibos":
                nv_pkg_names = ["cudart", "culibos"]
            case "cudnn":
                nv_pkg_names = ["cudnn"]
            case _:
                m = pattern.search(content)
                if not m:
                    raise ValueError(f"Could not determine NVIDIA package name in {conanfile}")
                nv_pkg_names = [m.group(1)]
        packages[conan_pkg_name] = {
            "nv_packages": nv_pkg_names,
            "urls": get_redist_urls(conanfile.parent / "conandata.yml"),
        }
    return packages


def _fetch_and_process_redist_file(url, relevant_nv_packages, hashes, url_dates):
    r = requests.get(url)
    r.raise_for_status()
    hashes[url] = sha256(r.content).hexdigest()
    redist_info = r.json()
    url_dates[url] = redist_info.get("release_date", None)
    results = []
    for nv_pkg_name, package_info in redist_info.items():
        if not isinstance(package_info, dict) or "version" not in package_info:
            continue
        version = package_info["version"]
        if nv_pkg_name in relevant_nv_packages:
            conan_pkg = relevant_nv_packages[nv_pkg_name]
            results.append((conan_pkg, version, url))
    return results


def _process_base_url(base_url, redist_conan_packages):
    r = requests.get(base_url)
    r.raise_for_status()
    redist_files = re.findall(r"redistrib_[^'>]+\.json", r.text)
    relevant_nv_packages = {}
    for conan_pkg, info in redist_conan_packages.items():
        if base_url in info["urls"]:
            for nv_pkg_name in info["nv_packages"]:
                relevant_nv_packages[nv_pkg_name] = conan_pkg
    return [(f"{base_url}/{redist_file}", relevant_nv_packages) for redist_file in redist_files]


def find_all_redist_package_versions(redist_conan_packages):
    versions = {}
    hashes = {}
    url_dates = {}
    base_urls = sorted(set().union(*(info["urls"] for info in redist_conan_packages.values())))
    redist_urls = []
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [
            executor.submit(_process_base_url, base_url, redist_conan_packages) for base_url in base_urls
        ]
        for future in tqdm(
            concurrent.futures.as_completed(futures), total=len(futures), desc="Processing base URLs"
        ):
            redist_urls.extend(future.result())
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [
            executor.submit(_fetch_and_process_redist_file, url, relevant, hashes, url_dates)
            for url, relevant in redist_urls
        ]
        for future in tqdm(
            concurrent.futures.as_completed(futures), total=len(futures), desc="Fetching redist files"
        ):
            for conan_pkg, version, url in future.result():
                if conan_pkg not in versions:
                    versions[conan_pkg] = {}
                if version not in versions[conan_pkg]:
                    versions[conan_pkg][version] = []
                versions[conan_pkg][version].append((url_dates[url], url))
    return versions, hashes


def _select_versions(versions_dict, version_range=None, policy="latest_minor"):
    if policy not in ["latest", "latest_major", "latest_minor"]:
        raise ValueError(f"Unknown version policy: {policy}")
    groups = {}
    for ver, info in versions_dict.items():
        ver = Version(ver)
        if version_range:
            if version_range[0] is not None and ver < version_range[0]:
                continue
            if version_range[1] is not None and ver >= version_range[1]:
                continue
        if policy == "latest_minor":
            key = (int(ver.major.value), int(ver.minor.value))
        elif policy == "latest_major":
            key = int(ver.major.value)
        else:
            key = None
        if key not in groups:
            groups[key] = []
        groups[key].append((ver, info))
    selected = []
    for group in groups.values():
        ver, info = sorted(group)[-1]
        # Select the newest URL if the same version exists in multiple
        url = sorted(info)[-1][1]
        selected.append((ver, url))
    return sorted(selected, reverse=True)


def _update_conandata(path, versions, hashes):
    parts = ["sources:"]
    for ver, url in versions:
        parts.append(textwrap.indent(f'"{ver}":\n  url: "{url}"\n  sha256: "{hashes[url]}"', "  "))
    content = path.read_text(encoding="utf-8")
    content, n = re.subn(r"sources:(?:\n  .+)+", "\n".join(parts), content)
    assert n > 0, f"{path} failed"
    path.write_text(content, encoding="utf-8")


def _update_config_yml(path, versions):
    parts = ["versions:"]
    for ver, folder in versions:
        parts.append(textwrap.indent(f'"{ver}":\n  folder: {folder}', "  "))
    path.write_text("\n".join(parts) + "\n", encoding="utf-8")


def update_all_conandata(all_versions, hashes):
    for pkg, versions in tqdm(sorted(all_versions.items()), desc="Updating conandata"):
        pkg_versions = []
        for conanfile in recipes_root.joinpath(pkg).rglob("conanfile.py"):
            if conanfile.parent.name.startswith("test_"):
                continue
            rel_path = str(conanfile.parent.relative_to(recipes_root))
            selected_versions = _select_versions(
                versions,
                conanfile_version_ranges.get(rel_path),
                conanfile_policies.get(rel_path, "latest_minor"),
            )
            _update_conandata(conanfile.parent.joinpath("conandata.yml"), selected_versions, hashes)
            pkg_versions += [(ver, conanfile.parent.name) for ver, _ in selected_versions]
        pkg_versions = sorted(set(pkg_versions), reverse=True)
        _update_config_yml(recipes_root / pkg / "config.yml", pkg_versions)


if __name__ == "__main__":
    redist_conan_packages = find_nvidia_redist_json_packages()
    all_versions, hashes = find_all_redist_package_versions(redist_conan_packages)
    update_all_conandata(all_versions, hashes)
