{
  meta = {};

  defaults = { pkgs, ... }: {};

  nodes = {
    tornium-proxy-db = {
      imports = [ ./hosts/proxy-db.nix ];
    };
    tornium-primary = {
      imports = [ ./hosts/primary.nix ];
    };
  };
}
