<!--
   - SPDX-FileCopyrightText: 2022 Oxhead Alpha
   -
   - SPDX-License-Identifier: LicenseRef-MIT-OA
   -->

# Tezos packaging

[![Build status](https://badge.buildkite.com/e899e9e54babcd14139e3bd4381bad39b5d680e08e7b7766d4.svg?branch=master)](https://buildkite.com/serokell/tezos-packaging)

This repo provides various forms of distribution for [Tezos](http://tezos.gitlab.io/) executables based on the [Octez](https://gitlab.com/tezos/tezos) implementation.

See the [official documentation](http://tezos.gitlab.io/introduction/howtouse.html)
for information about the binaries, their usage, and concepts about the Tezos networks.

See the [versioning doc](./docs/versioning.md) for information about the versioning
policy for the provided forms of distribution.

## Set up a node and/or baking on Ubuntu

The simplest procedure to set up a node and/or baking instance is provided for Ubuntu.

These commands will install everything necessary and start an interactive
setup wizard:
```
sudo add-apt-repository -yu ppa:serokell/tezos
sudo apt-get install -y tezos-baking
tezos-setup
```
> :warning: Since [#570](https://github.com/serokell/tezos-packaging/pull/570), this wizard was renamed from `tezos-setup-wizard`.


Read [the dedicated article](./docs/baking.md) to find out more about the setup,
the binaries, and the services used.

For setting up experimental transaction rollup node, see [this doc](./docs/tx-rollup.md).

### Voting on Ubuntu

An interactive voting wizard is provided for Ubuntu. After setting up a baking instance
on mainnet, you can vote by running:

```bash
tezos-vote
```
> :warning: Since [#570](https://github.com/serokell/tezos-packaging/pull/570), this wizard was renamed from `tezos-voting-wizard`.


Read the [documentation on voting](./docs/voting.md) to find out more details about
voting on custom networks.

## Installing Tezos

`tezos-packaging` supports several native distribution methods for convenience:

- [**Ubuntu**](./docs/ubuntu.md)
- [**Debian**](./docs/ubuntu.md#debian)
- [**Raspberry Pi OS**](./docs/ubuntu.md#raspberry)
- [**Fedora**](./docs/fedora.md)
- [**macOS**](./docs/macos.md)
- [**Windows using WSL**](./docs/windows.md)

The information about supported versions of the aforementioned OSes is available in the [support policy doc](./docs/support-policy.md).

Additionally, prebuilt **static binaries** can be downloaded directly from the
[latest release](https://github.com/serokell/tezos-packaging/releases/latest)
for other linux distros.

You can also use `systemd` services to run some of these static Tezos binaries
in the background.
For more information about these services, refer to [this doc](./docs/systemd.md#generic-linux).

## Build Instructions

This repository provides two distinct ways for building and packaging tezos binaries:
* [Docker-based](./docker/README.md)
* [Nix-based](./nix/README.md)

## Release process

Please see the [release workflow doc](./docs/release-workflow.md) for more information about the details of the `tezos-packaging`
releasing process.

## For Contributors

Please see [CONTRIBUTING.md](.github/CONTRIBUTING.md) for more information.

## About Serokell

This repository is maintained with ❤️ by [Serokell](https://serokell.io/).
The names and logo for Serokell are trademark of Serokell OÜ.

We love open source software! See [our other projects](https://serokell.io/community?utm_source=github)
or [hire us](https://serokell.io/hire-us?utm_source=github) to design, develop and grow your idea!
