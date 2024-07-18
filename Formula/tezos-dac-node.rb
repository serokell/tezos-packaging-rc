# SPDX-FileCopyrightText: 2021 Oxhead Alpha
# SPDX-License-Identifier: LicenseRef-MIT-OA

class TezosDacNode < Formula
  @all_bins = []

  class << self
    attr_accessor :all_bins
  end
  homepage "https://gitlab.com/tezos/tezos"

  url "https://gitlab.com/tezos/tezos.git", :tag => "octez-v20.2", :shallow => false

  version "v20.2-1"

  build_dependencies = %w[pkg-config coreutils autoconf rsync wget rustup-init cmake opam]
  build_dependencies.each do |dependency|
    depends_on dependency => :build
  end

  dependencies = %w[gmp hidapi libev protobuf sqlite tezos-sapling-params]
  dependencies.each do |dependency|
    depends_on dependency
  end
  desc "A Data Availability Committee Tezos node"

  bottle do
    root_url "https://github.com/serokell/tezos-packaging/releases/download/#{TezosDacNode.version}/"
    sha256 cellar: :any, monterey: "e55b679e40900efafc25e69e8c09b3169c4d46cc4c96b9b167d88a41eef3729f"
    sha256 cellar: :any, arm64_monterey: "033d4ae22759f70249395ce67a3a21ebc3ea295f5f6e3e062fa23e17fa216e94"
  end

  def make_deps
    ENV.deparallelize
    ENV["CARGO_HOME"]="./.cargo"
    # Disable usage of instructions from the ADX extension to avoid incompatibility
    # with old CPUs, see https://gitlab.com/dannywillems/ocaml-bls12-381/-/merge_requests/135/
    ENV["BLST_PORTABLE"]="yes"
    # Force linker to use libraries from the current brew installation.
    # Workaround for https://github.com/serokell/tezos-packaging/issues/700
    ENV["LDFLAGS"] = "-L#{HOMEBREW_PREFIX}/lib"
    # Here is the workaround to use opam 2.0.9 because Tezos is currently not compatible with opam 2.1.0 and newer
    arch = RUBY_PLATFORM.include?("arm64") ? "arm64" : "x86_64"
    system "rustup-init", "--default-toolchain", "1.71.1", "-y"
    system "opam", "init", "--bare", "--debug", "--auto-setup", "--disable-sandboxing"
    system ["source .cargo/env",  "make build-deps"].join(" && ")
  end

  def install_template(dune_path, exec_path, name)
    bin.mkpath
    self.class.all_bins << name
    system ["eval $(opam env)", "dune build #{dune_path}", "cp #{exec_path} #{name}"].join(" && ")
    bin.install name
    ln_sf "#{bin}/#{name}", "#{bin}/#{name.gsub("octez", "tezos")}"
  end

  def install
    make_deps
    install_template "src/bin_dac_node/main_dac.exe",
                     "_build/default/src/bin_dac_node/main_dac.exe",
                     "octez-dac-node"
  end
end
