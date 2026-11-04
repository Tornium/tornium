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

      forAllSystems = f: nixpkgs.lib.genAttrs [ "x86_64-linux" "aarch64-linux" "aarch64-darwin" ] (
        system: f (import nixpkgs { inherit system; overlays = [ pgbackrestOverlay ]; })
      );
    in {
      packages = forAllSystems (pkgs: 
        let
          inherit (pkgs) lib;
          repo = import ./modules/pgbackrest-repo.nix;

          # A pgBackRest config with only the repository settings. The hosts' pgbackrest.conf also
          # names the production pg1/pg2 hosts and sets primary_conninfo, neither of which may apply
          # to a test restore. Rendered the way services.pgbackrest does: repoN-* numbered by
          # attribute order (so PGBACKREST_REPO1_* lines up) and booleans as y/n.
          repoSettings = lib.concatMapAttrs (name: settings:
            let index = 1 + lib.lists.findFirstIndex (n: n == name) null (lib.attrNames repo.repos);
            in lib.mapAttrs' (option: value: lib.nameValuePair "repo${toString index}-${option}"
              (if value == true then "y" else if value == false then "n" else value)) settings
          ) repo.repos;

          restoreTestConfig = pkgs.writeText "pgbackrest-restore-test.conf" (lib.generators.toINI { } {
            global = repoSettings // {
              log-level-console = "info";
              log-level-file = "off";
              process-max = 2;
            };

            ${repo.stanza} = { };
          });
        in {
          restore-test = pkgs.writeShellApplication {
            name = "tornium-restore-test";
            runtimeInputs = with pkgs; [ pgbackrest postgresql_16 sops jq coreutils gawk gnugrep ];
            runtimeEnv = {
              RESTORE_TEST_CONFIG = restoreTestConfig;
              RESTORE_TEST_STANZA = repo.stanza;
            };
            text = builtins.readFile ./scripts/restore-test.sh;
          };

      });

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
