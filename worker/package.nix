{ pkgs, mixEnv, ... }:

let 
  src = ./.;
  beamPackages = pkgs.beam28Packages.extend (_: prev: { elixir = prev.elixir_1_19; });
  mixNixDeps = pkgs.callPackages ./deps.nix { beamPackages = beamPackages; };
in 
  beamPackages.mixRelease {
    inherit src;
    
    pname = "tornium-worker";
    version = "0.1.0";
    mixEnv = mixEnv;
    doCheck = false;

    nativeBuildInputs = [
      pkgs.rustPackages.cargo
      (builtins.attrValues mixNixDeps)
    ];

    RELEASE_TMP="/run/tornium-worker/_build";
  }
