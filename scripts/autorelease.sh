#!/usr/bin/env nix-shell
#!nix-shell -p gitAndTools.hub git rename -i bash
# SPDX-FileCopyrightText: 2019 TQ Tezos <https://tqtezos.com/>
#
# SPDX-License-Identifier: MPL-2.0

# Project name, inferred from repository name
project=$(basename "$(pwd)")

# The directory in which artifacts will be created
TEMPDIR=$(mktemp -d)
assets_dir=$TEMPDIR/assets

# Build release.nix
nix-build release.nix -o "$TEMPDIR"/"$project" --arg timestamp "$(date +\"%Y%m%d%H%M\")"
mkdir -p "$assets_dir"
# Move archive with binaries and tezos license to assets
cp "$TEMPDIR"/"$project"/*.tar.gz "$assets_dir"
cp "$TEMPDIR"/"$project"/LICENSE "$assets_dir"
# Unpack binaries
tar -C "$assets_dir" -xvzf "$TEMPDIR"/"$project"/binaries-*.tar.gz

# Delete release
hub release delete auto-release

# Update the tag
git fetch # So that the script can be run from an arbitrary checkout
git tag -f auto-release
git push --force --tags

# Combine all assets
assets=()
for file in $assets_dir/*; do
    echo $file
    assets+=("-a" $file)
done

# Create release
hub release create "${assets[@]}" -F "$TEMPDIR"/"$project"/*-release-notes.md --prerelease auto-release