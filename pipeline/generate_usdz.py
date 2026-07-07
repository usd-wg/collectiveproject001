#!/bin/env python

import os
import sys
import subprocess
from pathlib import Path
sys.dont_write_bytecode = True


def startswith_any(what, tokens):
    for t in tokens:
        if what.startswith(t):
            return True
    return False


def endswith_any(what, tokens):
    for t in tokens:
        if what.endswith(t):
            return True
    return False


def contains_any(what, tokens):
    for t in tokens:
        if t in what:
            return True
    return False


def generate_archive(output_usdz, archive_content, default_layer, exclude_startswith=[], exclude_endswith=[], exclude_contains=[]):
    args = [
        "usdzip",
        "-r",
        output_usdz,
        str(default_layer),
    ]

    for file in list(Path(archive_content).rglob('*')):
        file_path = str(file)
        if file.is_dir() or file.samefile(Path(default_layer)):
            continue
        
        if startswith_any(file_path, [".git", "pipeline"] + exclude_startswith):
            continue

        if endswith_any(file_path, [".md", ".usdz", ".tga", ".tx", ".rat"] + exclude_endswith):
            continue

        if contains_any(file_path, ["usdrecord_renders", "host_usd_export", "host_wip", "odie_grunge"] + exclude_contains):
            continue

        args.append(file_path)

    subprocess.run(args, shell=True)

generate_archive(
    output_usdz="collectiveproject001_shot_s001_001_index.usdz",
    archive_content=".",
    default_layer="shots/s001_001/index.usda"
)

generate_archive(
    output_usdz="collectiveproject001_odie_proxy_only.usdz",
    archive_content="assets/odie/proxy",
    default_layer="assets/odie/proxy/index.usda"
)

generate_archive(
    output_usdz="collectiveproject001_odie_render_only.usdz",
    archive_content="assets/odie/render",
    default_layer="assets/odie/render/index.usda"
)
