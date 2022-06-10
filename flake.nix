# SPDX-FileCopyrightText: 2022 Oxhead Alpha
# SPDX-License-Identifier: LicenseRef-MIT-OA

{
  description = "The tezos-packaging flake";

  inputs = {
    nixpkgs.url = "github:serokell/nixpkgs/be220b2dc47092c1e739bf6aaf630f29e71fe1c4";

    flake-utils.url = "github:numtide/flake-utils";

    serokell-nix.url = "github:serokell/serokell.nix/46d762e5107d10ad409295a7f668939c21cc048d";

    flake-compat.url = "github:edolstra/flake-compat";
    flake-compat.flake = false;

    opam-nix.url = "github:tweag/opam-nix/44b97c71a379bb9517135600c7d5e83d941e65d9";

    opam-repository.url = "gitlab:tezos/opam-repository/845375388d477153b36344f69a23a1b34b2bf82e";
    opam-repository.flake = false;

    tezos.url = "gitlab:tezos/tezos/cb9f439e58c761e76ade589d1cdbd2abb737dc68";
    tezos.flake = false;

    nix.url = "github:nixos/nix";
  };

  outputs = inputs@{ self, nixpkgs, flake-utils, serokell-nix, nix, ... }: {

      nixosModules = {
        tezos-node = import ./nix/modules/tezos-node.nix;
        tezos-accuser = import ./nix/modules/tezos-accuser.nix;
        tezos-baker = import ./nix/modules/tezos-baker.nix;
        tezos-signer = import ./nix/modules/tezos-signer.nix;
      };

    } // flake-utils.lib.eachSystem [
      "x86_64-linux"
    ] (system:
    let

      ocaml-overlay = callPackage ./nix/build/ocaml-overlay.nix {};

      pkgs = import nixpkgs {
        inherit system;
        overlays = [
          serokell-nix.overlay
          ocaml-overlay
          (_: _: { inherit serokell-nix; })
        ];
      };

      callPackage = pkg: input:
        import pkg (inputs // { inherit sources protocols meta pkgs; } // input);

      protocols = pkgs.lib.importJSON ./protocols.json;

      meta = pkgs.lib.importJSON ./meta.json;

      sources = { inherit (inputs) tezos opam-repository; };

      binaries = callPackage ./nix {};

      tezos-release = callPackage ./release.nix {};

    in rec {

      legacyPackages = pkgs;

      inherit tezos-release;

      apps.tezos-client = {
        type = "app";
        program = "${packages.tezos-client}/bin/tezos-client";
      };

      packages = binaries // { default = packages.binaries; };

      devShells = {
        buildkite = callPackage ./.buildkite/shell.nix {};
        autorelease = callPackage ./scripts/shell.nix {
          nix = nix.packages.${system}.default;
        };
        autorelease-macos = callPackage ./scripts/macos-shell.nix {};
      };

      checks = {
        tezos-nix-binaries = callPackage ./tests/tezos-nix-binaries.nix {};
        tezos-modules = callPackage ./tests/tezos-modules.nix {};
      };

      binaries-test = callPackage ./tests/tezos-binaries.nix {};

    });
}
