{
  description = "Tornium NixOS Infrastructure Mangement";
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    disko.url = "github:nix-community/disko";
    disko.inputs.nixpkgs.follows = "nixpkgs";
    colmena.url = "github:zhaofengli/colmena";
    sops-nix.url = "github:Mic92/sops-nix";
    sops-nix.inputs.nixpkgs.follows = "nixpkgs";
    tornium_oc_graph.url = "github:Tornium/tornium_oc_graph/feature/nix";
  };
  outputs = { nixpkgs, disko, colmena, sops-nix, tornium_oc_graph, ... }: 
    let
      # overlay that bumps only pgbackrest to 2.58.0
      pgbackrestOverlay = final: prev: {
        pgbackrest = prev.pgbackrest.overrideAttrs (old: rec {
          version = "2.58.0";

          src = prev.fetchFromGitHub {
            owner = "pgbackrest";
            repo = "pgbackrest";
            rev = "release/${version}";
            hash = "sha256-RxvVqThfGnTCWTaM54Job+2HgJ7baf6ciFYTz496aKQ=";
          };
        });
      };
    in
      {
      colmenaHive = colmena.lib.makeHive {
        meta = {
          nixpkgs = import nixpkgs {
            system = "x86_64-linux";
            overlays = [ pgbackrestOverlay tornium_oc_graph.overlays.default ];
          };
        };
        defaults = {
          imports = [
            sops-nix.nixosModules.sops
            disko.nixosModules.disko
          ];
        };

        # List of nodes in the cluster managed by colmena
        tornium-proxy-db = import ./hosts/proxy-db.nix;
        tornium-primary = import ./hosts/primary.nix;
      };

      nixosConfigurations.hetzner-cloud = nixpkgs.lib.nixosSystem {
        system = "x86_64-linux";
        modules = [
          disko.nixosModules.disko
          sops-nix.nixosModules.sops
          ./configuration.nix
        ];
      };
      nixosConfigurations.hetzner-cloud-aarch64 = nixpkgs.lib.nixosSystem {
        system = "aarch64-linux";
        modules = [
          disko.nixosModules.disko
          sops-nix.nixosModules.sops
          ./configuration.nix
        ];
      };
    };
}
