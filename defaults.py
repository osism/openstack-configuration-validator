#!/usr/bin/env python3

# Based on https://gitlab.com/yaook/operator/-/blob/devel/generate_default_policies.py
# Apache License Version 2.0, Copyright (c) 2021 The Yaook Authors

import os
import pathlib
import subprocess  # nosec
import sys
import yaml


def _writefile(modulename: str):
    basepath = pathlib.Path(OUTPUT)
    result = subprocess.run(  # nosec
        [
            "oslopolicy-policy-generator",
            "--namespace", modulename,
            "--output-file", basepath / "default_policies.yaml"
        ],
        capture_output=True,
    )
    if result.returncode:
        msg = f"Failed to generate the default policy file for {modulename}. "
        msg += f"stdout: {result.stdout}"
        msg += f"stderr: {result.stderr}"
        raise Exception(msg)


def generate_policy_file(modulename: str):
    _writefile(modulename)


if __name__ == '__main__':
    DEFAULTS = os.environ.get("DEFAULTS", "/defaults.py")
    NAMESPACES = os.environ.get("NAMESPACES", "/namespaces.yml")
    OUTPUT = os.environ.get("OUTPUT", "/output")

    with open(NAMESPACES) as fp:
        data = yaml.safe_load(fp)
        POLICY_NAMESPACES = data.keys()

    if len(sys.argv) != 2:
        for module in POLICY_NAMESPACES:
            # This is to work around oslo config that does not expect to have
            # multiple overlapping configs (e.g. glance and nova) in the same
            # python process. Without this the same config key is defined
            # multiple times (from an oslo.config perspecitve)
            subprocess.run(  # nosec
                [sys.executable, DEFAULTS, module]
            )
    else:
        print("Generating default policy file for: %s" % sys.argv[1])
        generate_policy_file(sys.argv[1])
