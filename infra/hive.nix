{
  meta = {};

  defaults = { pkgs, ... }: {};

  nodes = {
    tornium-proxy-db = {
      imports = [ ./hosts/proxy-db.nix ];
    };
  };
}
