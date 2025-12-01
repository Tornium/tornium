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
  outputs = { nixpkgs, disko, colmena, sops-nix, ... }: {
    colmenaHive = colmena.lib.makeHive {
      meta = {
        nixpkgs = import nixpkgs {
          system = "x86_64-linux";
          overlays = [];
        };
      };
      defaults = {
        imports = [
          sops-nix.nixosModules.sops
          disko.nixosModules.disko
        ];
      };
      tornium-proxy-db = import ./hosts/proxy-db.nix;
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
