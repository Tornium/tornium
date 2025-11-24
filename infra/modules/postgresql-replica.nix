{ pkgs, ... }:

{
  imports = [
    ./postgresql-password-service.nix
  ];

  services.postgresql.enable = true;
  services.postgresql.package = pkgs.postgresql_16;
  services.postgresql.ensureDatabases = [ "Tornium" ];
  services.postgresql.ensureUsers = [
    {
      name = "Tornium";
      ensureDBOwnership = true;
    }
    {
      name = "tiksan";
      ensureClauses = { superuser = true; };
    }
  ];
  services.postgresql.authentication = pkgs.lib.mkOverride 10 ''
    # Allow local superuser
    # type database user auth-method
    local all tiksan scram-sha-256
    local all postgres peer

    # Allow local IPv4 and IPv6 loopback
    # type database user address auth-method
    host Tornium Tornium 127.0.0.1/32 scram-sha-256
    host Tornium Tornium ::1/128 scram-sha-256

    # Allow 10.0.0.0/24
    # host Tornium Tornium 10.0.0.0/24 scram-sha-256

    # Reject all external requests
    host all all 0.0.0.0/0 reject
    host all all ::/0 reject
  '';
}
