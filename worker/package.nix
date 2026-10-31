{ pkgs, mixEnv, ... }:

let 
  src = ./.;
  beamPackages = pkgs.beam28Packages.overrideScope (_: prev: { elixir = prev.elixir_1_19; });
  mixNixDeps = pkgs.callPackages ./deps.nix { beamPackages = beamPackages; };
in 
  beamPackages.mixRelease {
    inherit src mixEnv mixNixDeps;
    
    pname = "tornium-worker";
    version = "0.1.0";
    doCheck = false;

    nativeBuildInputs = [ pkgs.rustPackages.cargo ];

    RELEASE_TMP="/run/tornium-worker/_build";
  }
