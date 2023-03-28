#! /usr/bin/env python3
# SPDX-FileCopyrightText: 2023 Oxhead Alpha
# SPDX-License-Identifier: LicenseRef-MIT-OA

import os
import re
import sys
import subprocess
import argparse
from dataclasses import dataclass
from typing import List, Optional

sys.path.append("docker")
from supported_versions import fedora_versions

parser = argparse.ArgumentParser()
parser.add_argument(
    "--directory",
    "-d",
    help="provide a directory with packages to upload",
    default=f"{os.path.join(os.getcwd(), '.')}",
    type=os.path.abspath,
)
parser.add_argument(
    "--artifacts",
    "-p",
    help="provide a list of files to upload",
    nargs="+",
    default=[],
    required=False,
)
parser.add_argument(
    "--upload",
    help="upload packages to the specified repository",
    default=None,
    const="regular",
    nargs="?",
)


@dataclass
class Arguments:
    directory: str
    artifacts: List[str]
    destination: str


def fill_args(args) -> Arguments:
    return Arguments(
        directory=args.directory,
        artifacts=args.artifacts,
        destination=args.upload,
    )


def main(args: Optional[Arguments] = None):

    if args is None:
        args = fill_args(parser.parse_args())

    with open("dput.cfg", "w") as dput_cfg:
        dput_cfg.write(
            f"""
[DEFAULT]
login	 = *
method = ftp
hash = md5
allow_unsigned_uploads = 0
allow_dcut = 0
run_lintian = 0
run_dinstall = 0
check_version = 0
scp_compress = 0
post_upload_command	=
pre_upload_command =
passive_ftp = 1
default_host_main	=
allowed_distributions	= (?!UNRELEASED)

[tezos-serokell]
fqdn      = ppa.launchpad.net
method    = ftp
incoming  = ~serokell/ubuntu/tezos
login     = anonymous

[tezos-rc-serokell]
fqdn        = ppa.launchpad.net
method      = ftp
incoming    = ~serokell/ubuntu/tezos-rc
login       = anonymous
    """
        )

    octez_version = os.getenv("OCTEZ_VERSION", None)

    if re.search("v.*-rc[0-9]*", octez_version):
        launchpad_ppa = "tezos-rc-serokell"
        copr_project = "@Serokell/Tezos-rc"
    else:
        launchpad_ppa = "tezos-serokell"
        copr_project = "@Serokell/Tezos-test"

    source_packages_path = args.directory

    if args.artifacts:
        packages = args.artifacts
    else:
        packages = list(
            map(
                lambda x: os.path.join(source_packages_path, x),
                os.listdir(source_packages_path),
            )
        )

    for f in filter(lambda x: x.endswith(".changes"), packages):
        subprocess.call(
            f"execute-dput -c dput.cfg {launchpad_ppa} {os.path.join(source_packages_path, f)}",
            shell=True,
        )

    destination = args.destination

    if destination == "epel":
        chroots = ["epel-x86_64"]
    elif destination == "regular":
        archs = ["x86_64", "aarch64"]
        chroots = [
            f"fedora-{version}-{arch}" for version in fedora_versions for arch in archs
        ]

    chroots = " ".join(f"-r {chroot}" for chroot in chroots)

    for f in filter(lambda x: x.endswith(".src.rpm"), packages):
        subprocess.call(
            f"copr-cli build {chroots} --nowait {copr_project} {f}",
            shell=True,
        )


if __name__ == "__main__":
    main()
