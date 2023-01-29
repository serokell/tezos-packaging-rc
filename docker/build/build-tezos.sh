#! /usr/bin/env bash

# SPDX-FileCopyrightText: 2021 Oxhead Alpha
# SPDX-License-Identifier: LicenseRef-MIT-OA

# This script builds static tezos binaries. It expects patches required for static building to be
# in parent directory, it also accepts tezos version as an argument.
set -euo pipefail

eval "$(opam env)"
make static
chmod +w octez-*
