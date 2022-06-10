# SPDX-FileCopyrightText: 2021 Oxhead Alpha
# SPDX-License-Identifier: LicenseRef-MIT-OA

{ pkgs, nix, ...}:
with pkgs;
mkShell {
  buildInputs = [
    coreutils gnused gh git rename gnupg dput rpm debian-devscripts which util-linux perl
    jq python3 nix
  ];
}
