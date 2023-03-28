#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2023 Oxhead Alpha
# SPDX-License-Identifier: LicenseRef-MIT-OA

import argparse
import os
import shutil
from dataclasses import dataclass
from typing import Optional, List
from package.util.build import call

parser = argparse.ArgumentParser()
parser.add_argument(
    "--directory",
    "-d",
    help="provide a directory with packages to sign",
    default=f"{os.path.join(os.getcwd(), '.')}",
    type=os.path.abspath,
)
parser.add_argument(
    "--artifacts",
    "-p",
    help="provide a list of files to sign",
    nargs="+",
    default=[],
    required=False,
)
parser.add_argument(
    "--identity",
    "-i",
    help="provide an identity to sign packages",
    type=str,
)


@dataclass
class Arguments:
    directory: str
    artifacts: List[str]
    identity: str


def fill_args(args) -> Arguments:
    return Arguments(
        directory=args.directory,
        artifacts=args.packages,
        identity=args.identity,
    )


def main(args: Optional[Arguments] = None):

    if args is None:
        args = fill_args(parser.parse_args())

    artifacts = args.artifacts

    if not artifacts:
        artifacts = (
            os.path.join(args.directory, x) for x in os.listdir(args.directory)
        )

    identity = args.identity

    gpg = shutil.which("gpg")

    for f in artifacts:
        if f.endswith(".changes"):
            call(f"sed -i 's/^Changed-By: .*$/Changed-By: {identity}/' {f}")
            call(f"debsign {f}")
        elif f.endswith(".src.rpm"):
            call(
                f'rpmsign --define="%_gpg_name {identity}" --define="%__gpg {gpg}" --addsign {f}'
            )


if __name__ == "__main__":
    main()
