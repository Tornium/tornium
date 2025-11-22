{ ... }:

{
  services.postgresql = {
    enable = true;
    ensureDatabases = [ "Tornium" ];
  };
}
