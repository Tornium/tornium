{ pkgs, ... }:

{
  systemd.services."postgresql-apply-password" = {
    description = "Apply PostgreSQL user passwords from runtime secrets";
    after = [ "postgresql.service" ];
    requires = [ "postgresql.service" ];
    wantedBy = [ "multi-user.target" ];
    reloadTriggers = [
      "/run/secrets/postgres/password"
      "/run/secrets/postgres/admin_password"
    ];
    path = [ pkgs.postgresql_16 ];

    serviceConfig = {
      Type = "oneshot";
      User = "postgres";
      Group = "postgres";
      ReadOnlyPaths = [ "/run/secrets/postgres/" ];
    };

    script = ''
      set -e

      if [ -f /run/secrets/postgres/password ]; then
        PW="$(cat /run/secrets/postgres/password)"
        echo "ALTER ROLE \"Tornium\" WITH PASSWORD '$PW';" | psql
      fi

      if [ -f /run/secrets/postgres/replicator_password ]; then
        PW="$(cat /run/secrets/postgres/replicator_password)"
        echo "ALTER ROLE \"replicator\" WITH PASSWORD '$PW';" | psql
      fi

      if [ -f /run/secrets/postgres/admin_password ]; then
        PW="$(cat /run/secrets/postgres/admin_password)"
        echo "ALTER ROLE \"tiksan\" WITH PASSWORD '$PW';" | psql
        echo "ALTER ROLE \"postgres\" WITH PASSWORD '$PW';" | psql
      fi
    '';
  };
}
