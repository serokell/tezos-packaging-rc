# SPDX-FileCopyrightText: 2022 Oxhead Alpha
# SPDX-License-Identifier: LicenseRef-MIT-OA

class TezosAccuserPtkathma < Formula
  @all_bins = []

  class << self
    attr_accessor :all_bins
  end
  homepage "https://gitlab.com/tezos/tezos"

  url "https://gitlab.com/tezos/tezos.git", :tag => "v15.0", :shallow => false

  version "v15.0-1"

  build_dependencies = %w[pkg-config coreutils autoconf rsync wget rustup-init]
  build_dependencies.each do |dependency|
    depends_on dependency => :build
  end

  dependencies = %w[gmp hidapi libev libffi]
  dependencies.each do |dependency|
    depends_on dependency
  end
  desc "Daemon for accusing"

  bottle do
    root_url "https://github.com/serokell/tezos-packaging/releases/download/#{TezosAccuserPtkathma.version}/"
    sha256 cellar: :any, big_sur: "acecccb95397cc3433dde8f35d210ea84d855a18cc46fc0023c73535fe438105"
    sha256 cellar: :any, arm64_big_sur: "8076e0a687b089ab8228cf9b0c034e3ec39ecfba6f1f4760c8b8850d60383cae"
  end

  def make_deps
    ENV.deparallelize
    ENV["CARGO_HOME"]="./.cargo"
    # Disable usage of instructions from the ADX extension to avoid incompatibility
    # with old CPUs, see https://gitlab.com/dannywillems/ocaml-bls12-381/-/merge_requests/135/
    ENV["BLST_PORTABLE"]="yes"
    # Here is the workaround to use opam 2.0 because Tezos is currently not compatible with opam 2.1.0 and newer
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

      accuser="#{bin}/octez-accuser-PtKathma"

      accuser_config="$TEZOS_CLIENT_DIR/config"
      mkdir -p "$TEZOS_CLIENT_DIR"

      if [ ! -f "$accuser_config" ]; then
          "$accuser" --endpoint "$NODE_RPC_SCHEME://$NODE_RPC_ADDR" \
                    config init --output "$accuser_config" >/dev/null 2>&1
      else
          "$accuser" --endpoint "$NODE_RPC_SCHEME://$NODE_RPC_ADDR" \
                    config update >/dev/null 2>&1
      fi

      exec "$accuser" --endpoint "$NODE_RPC_SCHEME://$NODE_RPC_ADDR" run
    EOS
    File.write("tezos-accuser-PtKathma-start", startup_contents)
    bin.install "tezos-accuser-PtKathma-start"
    make_deps
    install_template "src/proto_014_PtKathma/bin_accuser/main_accuser_014_PtKathma.exe",
                     "_build/default/src/proto_014_PtKathma/bin_accuser/main_accuser_014_PtKathma.exe",
                     "octez-accuser-PtKathma"
  end

  plist_options manual: "tezos-accuser-PtKathma run"
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
          <string>#{opt_bin}/tezos-accuser-PtKathma-start</string>
          <key>EnvironmentVariables</key>
            <dict>
              <key>TEZOS_CLIENT_DIR</key>
              <string>#{var}/lib/tezos/client</string>
              <key>NODE_RPC_SCHEME</key>
              <string>http</string>
              <key>NODE_RPC_ADDR</key>
              <string>localhost:8732</string>
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
