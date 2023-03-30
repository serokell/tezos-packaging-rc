#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2022 Oxhead Alpha
# SPDX-License-Identifier: LicenseRef-MIT-OA

import os
import sys
import shlex
import shutil
import subprocess
from typing import Optional
import package.util.build as build
import package.util.sign as sign
import package.util.upload as upload

sys.path.append("docker")
from supported_versions import ubuntu_versions, fedora_versions

parser = build.parser
parser.add_argument(
    "--gpg-sign",
    "-s",
    help="provide an identity to sign packages",
    type=str,
)
# --upload will perform upload to regular repositories
# --upload epel will upload for epel-x86_64 chroot on copr
parser.add_argument(
    "--upload",
    help="upload packages to the specified repository",
    default=None,
    const="regular",
    nargs="?",
)

args = parser.parse_args()

artifacts = build.main(args)

if args.gpg_sign:
    sign.main(sign.Arguments(args.output_dir, artifacts, args.gpg_sign))

    if args.upload:
        upload.main(upload.Arguments(args.output_dir, artifacts, args.upload))

if not args.gpg_sign and args.upload:
    raise Exception("You have to sign packages before uploading them.")
