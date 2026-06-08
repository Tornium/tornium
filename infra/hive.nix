{
  meta = {};

  defaults = { pkgs, ... }: {};

  nodes = {
    tornium-proxy-db = {
      networking.hostName = "tornium-proxy-db";

      imports = [ ./hosts/proxy-db.nix ];
    };
    tornium-primary = {
      networking.hostName = "tornium-primary";

      imports = [ ./hosts/primary.nix ];
    };
  };
}
