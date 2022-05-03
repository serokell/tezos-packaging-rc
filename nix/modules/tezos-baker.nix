# SPDX-FileCopyrightText: 2021 Oxhead Alpha
# SPDX-License-Identifier: LicenseRef-MIT-OA

{config, lib, pkgs, ...}:

with lib;

let
  tezos-baker-pkgs = {
    "012-Psithaca" =
      "${pkgs.ocamlPackages.tezos-baker-012-Psithaca}/bin/tezos-baker-012-Psithaca";
    "013-PtJakart" =
      "${pkgs.ocamlPackages.tezos-baker-013-PtJakart}/bin/tezos-baker-013-PtJakart";
  };
  tezos-client = "${pkgs.ocamlPackages.tezos-client}/bin/tezos-client";
  cfg = config.services.tezos-baker;
  common = import ./common.nix { inherit lib; inherit pkgs; };
  instanceOptions = types.submodule ( {...} : {
    options = common.daemonOptions // {

      enable = mkEnableOption "Tezos baker service";

      bakerSecretKey = mkOption {
        type = types.nullOr types.str;
        default = null;
        description = ''
          Secret key stat will be imported as 'bakerAccountAlias' before
          starting the baker daemon.
        '';
      };

      bakerAccountAlias = mkOption {
        type = types.str;
        default = "";
        description = ''
          Alias for the tezos-baker account.
        '';
      };

      liquidityBakingToggleVote = mkOption {
        type = types.enum [ "on" "of" "pass" ];
        default = "pass";
        description = "Vote to continue (option "on") or end (option "off") the liquidity baking subsidy. Or choose to pass (option "pass")";
      };

    };
  });

in {
  options.services.tezos-baker = {
    instances = mkOption {
      type = types.attrsOf instanceOptions;
      description = "Configuration options";
      default = {};
    };
  };
  config =
    let baker-start-script = node-cfg:
      let
        voting-option = if node-cfg.baseProtocol == "012-Psithaca"
          then if node-cfg.liquidityBakingToggleVote == "off" then "--liquidity-baking-escape-vote" else ""
          else "--liquidity-baking-toggle-vote ${node-cfg.liquidityBakingToggleVote}";
      in ''
        ${tezos-baker-pkgs.${node-cfg.baseProtocol}} -d "$STATE_DIRECTORY/client/data" \
        -E "http://localhost:${toString node-cfg.rpcPort}" \
        run with local node "$STATE_DIRECTORY/node/data" ${voting-option} ${node-cfg.bakerAccountAlias}
      '';
        baker-prestart-script = node-cfg: if node-cfg.bakerSecretKey != null then ''
          ${tezos-client} -d "$STATE_DIRECTORY/client/data" import secret key "${node-cfg.bakerAccountAlias}" ${node-cfg.bakerSecretKey} --force
          '' else "";
    in common.genDaemonConfig {
      instancesCfg = cfg.instances;
      service-name = "baker";
      service-pkgs = tezos-baker-pkgs;
      service-start-script = baker-start-script;
      service-prestart-script = baker-prestart-script;
    };
}
