{ pkgs, ... }:

{
  services.pgbackrest.enable = true;
  services.pgbackrest.repos = {
    b2 = {
      type = "s3";
      bundle = true;
      s3-bucket = "tornium-backups";
      s3-endpoint = "s3.eu-central-003.backblazeb2.com";
      s3-region = "eu-central-003";
      s3-verifyTls = true;

      cipher-type = "aes-256-cbc";
    };
  };

  sops.templates."pgbackrest.env" = {
    content = ''
      PGBACKREST_REPO_CIPHER_PASS="$(cat /run/secrets/pgbackrest/aes_encryption_key)"
      PGBACKREST_REPO_S3_KEY="$(cat /run/secrets/pgbackrest/backblaze_key)"
    '';
    path = "/run/secrets/pgbackrest/.env";
    owner = "pgbackrest";
  };

  systemd.services."postgresql-pgbackrest-backup" = {
    serviceConfig = {
      EnvironmentFile = "/run/secrets/pgbackrest/.env";
    };

    description = "Backup the PostgreSQL database using pgbackrest";
    after = [ "postgresql.service" "network-online.target" ];
    requires = [ "postgresql.service" ];
    wants = [ "network-online.target" ];
    wantedBy = [ "multi-user.target" ];
    reloadTriggers = [
      "/run/secrets/postgres/password"
      "/run/secrets/pgbackrest/aes_encryption_key"
      "/run/secrets/pgbackrest/backblaze_key"
      "/run/secrets/pgbackrest/backblaze_key_id"
    ];

    serviceConfig = {
      Type = "oneshot";
      User = "postgres";
      Group = "postgres";
      ReadOnlyPaths = [ "/run/secrets/pgbackrest/" ];
    };

    script = ''
      set -e

      ${pkgs.pgbackrest}/bin/pgbackrest --stanza=pg1 --type=full backup
    '';
  };

  systemd.timers."postgresql-pgbackrest-backup" = {
    description = "Timer to start the postgresql backup";
    wantedBy = [ "timers.target" ];
    timerConfig = {
      OnCalendar = "daily";
      Persistent = true;
    };
  };
}
