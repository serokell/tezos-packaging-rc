let 
  linuxPkgs = (import <nixpkgs> { }).forceSystem "x86_64-linux" "x86_64";
  tezosClient = 
    (import ./default.nix { pkgs = linuxPkgs; })
      .tezos-client-babylonnet;
in linuxPkgs.dockerTools.buildImage {
  name = "tezos-client-${toString builtins.currentTime}";
  contents = [ tezosClient ];
}
