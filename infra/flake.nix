{
  description = "Tornium NixOS Infrastructure Mangement";
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    disko.url = "github:nix-community/disko";
    disko.inputs.nixpkgs.follows = "nixpkgs";
    colmena.url = "github:zhaofengli/colmena";
    sops-nix.url = "github:Mic92/sops-nix";
    sops-nix.inputs.nixpkgs.follows = "nixpkgs";
  };
  outputs = { nixpkgs, disko, colmena, sops-nix, ... }:
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
      # overlay that bumps peewee to 4.5.3 to fix a bug with JOINs in previous version not
      # yet in nixpkgs.
      peeweeOverlay = final: prev: {
        pythonPackagesExtensions = prev.pythonPackagesExtensions ++ [
          (pyfinal: pyprev: {
            peewee = pyprev.peewee.overridePythonAttrs (old: rec {
              version = "4.5.3";
              src = prev.fetchFromGitHub {
                owner = "coleifer";
                repo = "peewee";
                tag = version;
                hash = "sha256-hBZITssTdjXg8zqJfvhyI7aHoPKYxnJ0E8AHHrrncT4=";
              };
            });
          })
        ];
      };
    in
      {
      colmenaHive = colmena.lib.makeHive {
        meta = {
          nixpkgs = import nixpkgs {
            system = "x86_64-linux";
            overlays = [ pgbackrestOverlay peeweeOverlay ];
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
