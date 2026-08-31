{ config, ... }:

let 
  postgresqlDataDir = config.services.postgresql.dataDir;
in {
  sops.templates."postgres-password.env" = {
    content = ''
    PGPASSWORD=${config.sops.placeholder."postgres/replicator_password"}
    '';
    owner = "postgres";
    group = "postgres";
    mode = "0440";
  };

  systemd.services.postgresql-rebuild-replica = {
    description = "Rebuild PostgreSQL replica";

    # This should never be run automaticlly by any other service, so we should set this
    # to an empty list.
    wantedBy = [];

    conflicts = [ "postgesql.service" ];

    serviceConfig = {
      Type = "oneshot";
      User = "postgres";
      Group = "postgres";
      TimeoutStartSec = "2h";

      EnvironmentFile = config.sops.templates."postgres-password.env".path;
      ReadOnlyPaths = [ config.sops.templates."postgres-password.env".path ];
    };
    unitConfig = {
      OnSuccess = [ "postgresql.service" ];
    };

    script = ''
      set -euo pipefail
      
      echo "Wiping existing PostgreSQL data directory: ${postgresqlDataDir}..."
      shopt -s dotglob
      rm -rf -- "${postgresqlDataDir}"/*
      shopt -u dotglob

      echo "Cloning primary database..."
      ${config.services.postgresql.package}/bin/pg_basebackup \
        -h 10.0.0.5 \
        -p ${toString config.services.postgresql.settings.port} \
        -U replicator \
        -D "${postgresqlDataDir}" \
        -F plain \
        -X stream \
        -R -P
    '';
  };
}
