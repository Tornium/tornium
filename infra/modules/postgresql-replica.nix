{ pkgs, ... }:

{
  imports = [
    ./postgresql-password-service.nix
  ];

  services.postgresql.enable = true;
  services.postgresql.package = pkgs.postgresql_16;
  services.postgresql.settings = {
    wal_level = "replica";
    max_wal_senders = "10";
    max_replication_slots = "10";
    wal_keep_size = "1GB";
    primary_conninfo = "host=10.0.0.3 port=5432 user=replicator";
    hot_standby = "on";
  };
  services.postgresql.ensureDatabases = [ "Tornium" ];
  services.postgresql.ensureUsers = [
    {
      name = "Tornium";
      ensureDBOwnership = true;
      ensureClauses = { superuser = true; };
    }
    {
      name = "replicator";
      ensureClauses = { replication = true; };
    }
  ];
  services.postgresql.authentication = pkgs.lib.mkOverride 10 ''
    # Allow local superuser
    # type database user auth-method
    local all postgres peer
    local all Tornium scram-sha-256

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
