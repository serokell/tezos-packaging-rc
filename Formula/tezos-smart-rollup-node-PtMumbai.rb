#!/usr/bin/env ruby

# SPDX-FileCopyrightText: 2023 Oxhead Alpha
# SPDX-License-Identifier: LicenseRef-MIT-OA

class TezosSmartRollupNodePtmumbai < Formula
  @all_bins = []

  class << self
    attr_accessor :all_bins
  end
  homepage "https://gitlab.com/tezos/tezos"

  url "https://gitlab.com/tezos/tezos.git", :tag => "v16.0", :shallow => false

  version "v16.0-1"

  build_dependencies = %w[pkg-config coreutils autoconf rsync wget rustup-init cmake]
  build_dependencies.each do |dependency|
    depends_on dependency => :build
  end

  dependencies = %w[gmp hidapi libev libffi tezos-sapling-params]
  dependencies.each do |dependency|
    depends_on dependency
  end
  desc "Tezos smart contract rollup node for PtMumbai"

  bottle do
    root_url "https://github.com/serokell/tezos-packaging/releases/download/#{TezosSmartRollupNodePtmumbai.version}/"
    sha256 cellar: :any, big_sur: "2101bfcd3dcfba00841669ccdf65c810bbcd44f18d37c44c53719084a9d54df4"
    sha256 cellar: :any, arm64_big_sur: "eaa4b04881734e8d08e7b537ea4ce3850b925e66dc505b427b108ed377907817"
    sha256 cellar: :any, big_sur: "9593ee16dba5552eebcc4ccb0a54c87e68cdd2fbae16d6be3696fc1e8ef0a20b"
    sha256 cellar: :any, arm64_big_sur: "e288980b2592adb8ba13310efb6661e8907bffd3be831cc4e080d802d99ae24d"
    sha256 cellar: :any, monterey: "6198f9242da9d6c27ef4dfb077e78bf5aae7e0f2ebabd3cb4cb7033f3d7ee52d"
  end

  def make_deps
    ENV.deparallelize
    ENV["CARGO_HOME"]="./.cargo"
    # Disable usage of instructions from the ADX extension to avoid incompatibility
    # with old CPUs, see https://gitlab.com/dannywillems/ocaml-bls12-381/-/merge_requests/135/
    ENV["BLST_PORTABLE"]="yes"
    # Here is the workaround to use opam 2.0.9 because Tezos is currently not compatible with opam 2.1.0 and newer
    arch = RUBY_PLATFORM.include?("arm64") ? "arm64" : "x86_64"
    system "curl", "-L", "https://github.com/ocaml/opam/releases/download/2.0.9/opam-2.0.9-#{arch}-macos", "--create-dirs", "-o", "#{ENV["HOME"]}/.opam-bin/opam"
    system "chmod", "+x", "#{ENV["HOME"]}/.opam-bin/opam"
    ENV["PATH"]="#{ENV["HOME"]}/.opam-bin:#{ENV["PATH"]}"
    system "rustup-init", "--default-toolchain", "1.60.0", "-y"
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
    startup_contents =
      <<~EOS
      #!/usr/bin/env bash

      set -euo pipefail

      node="#{bin}/octez-smart-rollup-node-PtMumbai"

      "$node" init "$ROLLUP_MODE" config \
          for "$ROLLUP_ALIAS" \
          --rpc-addr "$ROLLUP_NODE_RPC_ENDPOINT" \
          --force

      "$node" --endpoint "$NODE_RPC_SCHEME://$NODE_RPC_ADDR" \
          run "$ROLLUP_MODE" for "$ROLLUP_ALIAS"
      EOS
    File.write("tezos-smart-rollup-node-PtMumbai-start", startup_contents)
    bin.install "tezos-smart-rollup-node-PtMumbai-start"
    make_deps
    install_template "src/proto_016_PtMumbai/bin_sc_rollup_node/main_sc_rollup_node_016_PtMumbai.exe",
                     "_build/default/src/proto_016_PtMumbai/bin_sc_rollup_node/main_sc_rollup_node_016_PtMumbai.exe",
                     "octez-smart-rollup-node-PtMumbai"
  end
  plist_options manual: "tezos-smart-rollup-node-PtMumbai run for"
  def plist
    <<~EOS
      <?xml version="1.0" encoding="UTF-8"?>
      <!DOCTYPE plist PUBLIC "-//Apple Computer//DTD PLIST 1.0//EN"
      "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
      <plist version="1.0">
        <dict>
          <key>Label</key>
          <string>#{plist_name}</string>
          <key>Program</key>
          <string>#{opt_bin}/tezos-smart-rollup-node-PtMumbai-start</string>
          <key>EnvironmentVariables</key>
            <dict>
              <key>TEZOS_CLIENT_DIR</key>
              <string>#{var}/lib/tezos/client</string>
              <key>NODE_RPC_ENDPOINT</key>
              <string>http://localhost:8732</string>
              <key>ROLLUP_NODE_RPC_ENDPOINT</key>
              <string>127.0.0.1:8472</string>
              <key>ROLLUP_MODE</key>
              <string>observer</string>
              <key>ROLLUP_ALIAS</key>
              <string>rollup</string>
          </dict>
          <key>RunAtLoad</key><true/>
          <key>StandardOutPath</key>
          <string>#{var}/log/#{name}.log</string>
          <key>StandardErrorPath</key>
          <string>#{var}/log/#{name}.log</string>
        </dict>
      </plist>
    EOS
  end
  def post_install
    mkdir "#{var}/lib/tezos/client"
  end
end
