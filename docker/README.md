<!--
   - SPDX-FileCopyrightText: 2021 Oxhead Alpha
   - SPDX-License-Identifier: LicenseRef-MIT-OA
   -->

# Building and packaging tezos using docker

The following scripts can be used with `podman` instead of `docker`
as a virtualisation engine. In order to use `podman` you should
set environment variable `USE_PODMAN="True"`.

<!-- TODO #635: extend and clean up this doc -->

## Statically built binaries

Static binaries building using custom alpine image.

[`docker-static-build.sh`](docker-static-build.sh) will build tezos binaries
image defined in [Dockerfile](build/Dockerfile). In order to build them you should specify
`OCTEZ_VERSION` env variable and run the script:
```
export OCTEZ_VERSION="v14.1"
./docker-static-build.sh
```
After that, directory will contain built static binaries.

This script can optionally accept argument to define resulting binaries target architecture.
Currently supported architectures are: `host` and `aarch64`, so that
one can build native binaries for current architecture or build `aarch64` binaries on
`x86_64` machine.

### Compiling for `aarch64` on `x86_64` prerequisites

Docker image defined in [`Dockerfile.aarch64`](build/Dockerfile.aarch64) uses qemu for
compilation on `aarch64`. In particular it uses `qemu-aarch64-static` binary from
[qemu-user-static repo](https://github.com/multiarch/qemu-user-static/).
In order to be able to compile tezos using `aarch64` emulator you'll need to run:
```
docker run --rm --privileged multiarch/qemu-user-static:register --reset
```
This command will register qemu emulator in `binfmt_misc`.

Once this is done you should run the following command to build `aarch64` static tezos binaries:
```
./docker-static-build.sh aarch64
```

### Packages from statically linked binaries

It's possible to create packages (ubuntu/debian & fedora) using already
built binaries. This means that the build step of the package will be reduced
to copying the binaries instead of building again from scratch.

Using Ubuntu/Debian and assuming all Tezos binaries are located in the `binaries` directory:
```sh
cd .. && ./docker/docker-tezos-packages.py --os ubuntu --type binary --binaries-dir binaries
```

Using Fedora and assuming all Tezos binaries are located in the `binaries` directory:
```sh
cd .. && ./docker/docker-tezos-packages.py --os fedora --type binary --binaries-dir binaries
```

The resulting packages will be located in `../out` directory.

## Ubuntu packages

We provide a way to build both binary and source native Ubuntu packages.

[`docker-tezos-packages.py`](docker-tezos-packages.py) script with `ubuntu` argument
will build source or binary packages depending on the passed argument (`source` and `binary` respectively).
This script builds packages inside docker image defined in [Dockerfile-ubuntu](package/Dockerfile-ubuntu).
This script uses [another script](package/package_generator.py), which generates meta information for
tezos packages based on information defined in [meta.json](../meta.json) and current tezos
version defined in [meta.json](../meta.json) and build native ubuntu packages.

To see all available options, run:
```
./docker-tezos-packages.py --help
```

### `.deb` packages

In order to build binary `.deb` packages specify `OCTEZ_VERSION` and
run the following command:
```
export OCTEZ_VERSION="v14.1"
cd .. && ./docker/docker-tezos-packages.py --os ubuntu --type binary
```


It is also possible to specify packages to build with `-p` or `--packages` option. In order to do that run the following:
```
# cd .. && ./docker/docker-tezos-packages.py -os ubuntu --type binary --packages <tezos-binary-1> <tezos-binary-2>
# Example for baker
export OCTEZ_VERSION="v14.1"
cd .. && ./docker/docker-tezos-packages.py --os ubuntu --type binary -p tezos-client tezos-node
```

In order to choose specific ubuntu distribution to build for (see [support policy](../docs/support-policy.md)),
use `-d` or `--distributions` option:
```
export OCTEZ_VERSION="v14.1"
cd .. && ./docker/docker-tezos-packages.py --os ubuntu --type binary -d focal jammy -p tezos-client tezos-node
```

The build can take some time due to the fact that we build tezos and its dependencies
from scratch for each package individually.

Once the build is completed the packages will be located in `../out` directory.

In order to install `.deb` package run the following command:
```
sudo apt install <path to deb file>
```

### Source packages and publishing them on Launchpad PPA

In order to build source packages run the following commands:
```
export OCTEZ_VERSION="v14.1"
cd .. && ./docker/docker-tezos-packages.py --os ubuntu --type source
# you can also build single source package
cd .. && ./docker/docker-tezos-packages.py --os ubuntu --type source --packages tezos-client
```

Once the packages build is complete `../out` directory will contain files required
for submitting packages to the Launchpad.

There are 5 files for each package: `.orig.tar.gz`, `.debian.tar.xz`,
`.dsc`, `.build-info`, `.changes`.

You can test source package building using [`pbuilder`](https://wiki.ubuntu.com/PbuilderHowto).

In order to push the packages to the Launchpad PPA `*.changes` files should should be updated with
the submitter info and signed.

If you want to sign resulted source packages automatically, you can provide signer identity through `--gpg-sign` or `-s` option:
```
export OCTEZ_VERSION="v14.1"
cd .. && ./docker/docker-tezos-packages.py --os ubuntu --type source -d focal jammy -p tezos-client -s <signer_info>
```
For example, `signer_info` can be the following: `Roman Melnikov <roman.melnikov@serokell.io>`

If you want to do it manually, you should update `*.changes` files with the proper signer info run the following:
```
sed -i "s/^Changed-By: .*$/Changed-By: <signer_info>/" ../out/*.changes
```

Once these files are updated, they should be signed using `debsign`.
```
debsign ../out/*.changes
```

If you're not running `dput` on Ubuntu, you'll need to provide a config for it.
Sample config can be found [here](./package/.dput.cf). Put the contents of this config
into `~/.dput.cf`. In case you already have a config, add the following piece
to it for the further convenience:
```
[tezos-serokell]
fqdn        = ppa.launchpad.net
method      = ftp
incoming    = ~serokell/ubuntu/tezos
login       = anonymous

[tezos-rc-serokell]
fqdn        = ppa.launchpad.net
method      = ftp
incoming    = ~serokell/ubuntu/tezos-rc
login       = anonymous
```

Signed files now can be submitted to Launchpad PPA. In order to do that run the following
command for each `.changes` file:
```
dput tezos-serokell ../out/<package>.changes
# or tezos-rc-serokell in case the corresponding upstream version is release-candidate
dput tezos-rc-serokell ../out/<package>.changes
```

#### Updating release in scope of the same upstream version

In case you're uploading the same version of the package but with a different
release number, you'll highly likely have to use the same source archive (`.orig.tar.gz` archive)
that was used for the first release in the scope of the same version, it can be downloaded from
the launchpad package details (e.g. https://launchpad.net/~serokell/+archive/ubuntu/tezos/+sourcefiles/tezos-client/2:7.4-0ubuntu2/tezos-client_7.4.orig.tar.gz).
Otherwise, Launchpad will prohibit the build of the new release.

In order to build new proper source package using existing source archive run the following:
```
cd .. && ./docker/docker-tezos-packages.py --os ubuntu --type source -p tezos-client --sources-dir <path to dir with source archives> -s <signer_info>
```
If the directory contains the correctly named archive (e.g. `tezos-client_15.1a.orig.tar.gz`), it will be used by the build script.
After that, the resulting source package can be uploaded to the Launchpad using the commands
described previously.

## Fedora packages

We provide a way to build both binary(`.rpm`) and source(`.src.rpm`) native Fedora packages.

[`docker-tezos-packages.py`](docker-tezos-packages.py) script with `fedora` argument
will build source or binary packages depending on the passed argument (`source` and `binary` respectively).

To see all available options, run:
```
./docker-tezos-packages.py --help
```

### `.rpm` packages

In order to build binary `.rpm` packages specify `OCTEZ_VERSION` and
run the following command:
```
export OCTEZ_VERSION="v14.1"
cd .. && ./docker/docker-tezos-packages.py --os fedora --type binary
```

It is also possible to specify packages to build with `-p` or `--packages` option. In order to do that run the following:
```
# cd .. && ./docker/docker-tezos-packages.py --os fedora --type binary --packages <tezos-binary-1> <tezos-binary-2>
# Example for baker
export OCTEZ_VERSION="v14.1"
cd .. && ./docker/docker-tezos-packages.py --os fedora --type binary -p tezos-client tezos-node
```

In order to build packages for specific Fedora distribution (see [support policy](../docs/support-policy.md)),
use `-d` or `--distributions` option:
```
export OCTEZ_VERSION="v14.1"
cd .. && ./docker/docker-tezos-packages.py --os fedora -d 36 --type binary -p tezos-baking
```

The build can take some time due to the fact that we build tezos and its dependencies
from scratch for each package individually.

Once the build is completed the packages will be located in `../out` directory.

In order to install `.rpm` package run either of these commands:
```
sudo yum localinstall <path to rpm file>
```
```
sudo dnf install <path to rpm file>
```

### `.src.rpm` packages and publishing them on Copr

In order to build source packages run the following commands:
```
export OCTEZ_VERSION="v14.1"
cd .. && ./docker/docker-tezos-packages.py --os fedora --type source
# you can also build single source package
cd .. && ./docker/docker-tezos-packages.py --os fedora --type source -p tezos-client
```

If you want to sign resulted source packages automatically, you can provide signer identity through `--gpg-sign` or `-s` option:
```
export OCTEZ_VERSION="v14.1"
cd .. && ./docker/docker-tezos-packages.py --os fedora --type source -p tezos-client -s <signer_info>
```
For example, `signer_info` can be the following: `Roman Melnikov <roman.melnikov@serokell.io>`

If you want to sign source packages manually, run:
```
rpm --addsign out/*.src.rpm
```
Note, that in order to sign them, you'll need gpg key to be set up in `~/.rpmmacros`.

Signed package can be submitted to the Copr repository via `copr-cli`.
Read more about setting up `copr-cli` [here](https://developer.fedoraproject.org/deployment/copr/copr-cli.html).

In order to submit source package for building run the following command:
```
copr-cli build @Serokell/Tezos --nowait <path to '.src.rpm' file>
# or @Serokell/Tezos-rc in case the corresponding upstream version is release-candidate
copr-cli build @Serokell/Tezos-rc --nowait <path to '.src.rpm' file>
```
