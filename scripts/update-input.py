#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2022 Oxhead Alpha
# SPDX-License-Identifier: LicenseRef-MIT-OA

import argparse
import re
import json
from subprocess import call

with open("flake.lock") as f:
    lock = json.load(f)["nodes"]

parser = argparse.ArgumentParser()
parser.add_argument("flake", type=str)
parser.add_argument("rev", type=str)

args = parser.parse_args()

with open("flake.nix", "r") as flake_nix:
    lines = flake_nix.readlines()
with open("flake.nix", "w") as flake_nix:
    for line in lines:
        name = args.flake
        meta = lock[name]["locked"]
        pattern = (
            rf'{name}\.url[ ]*=[ ]*"{meta["type"]}:{meta["owner"]}\/{meta["repo"]}.*$'
        )
        res = (
            f'{name}.url = "{meta["type"]}:{meta["owner"]}/{meta["repo"]}/{args.rev}";'
        )
        flake_nix.write(re.sub(pattern, res, line))

call(["nix", "flake", "lock", "--update-input", args.flake])
