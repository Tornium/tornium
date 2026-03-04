{ config, pkgs, ... }:

{
  services.pgbackrest.enable = true;
  services.pgbackrest.settings = {
    backup-standby = "y";
    start-fast = "y";
    delta = "y";
  };
  services.pgbackrest.repos = {
    b2 = {
      type = "s3";
      bundle = true;
      s3-bucket = "tornium-backups";
      s3-uri-style = "path";
      s3-endpoint = "s3.eu-central-003.backblazeb2.com";
      s3-region = "eu-central-003";
      storage-verify-tls = true;

      cipher-type = "aes-256-cbc";

      path = "/var/lib/pgbackrest";
    };
  };
  services.pgbackrest.stanzas = {
    pg1 = {
      settings = {
        recovery-option = "primary_conninfo=10.0.0.3 user=replicator";
      };
      instances = {
        pg1.host = "10.0.0.3";
        pg1.user = "postgres";
        pg1.path = "/var/lib/postgresql/16/main";
        localhost.database = "Tornium";
        localhost.user = "postgres";
        localhost.path = "/var/lib/postgresql/16/replica";
      };
    };
  };

  sops.templates."pgbackrest.env" = {
    content = ''
      PGBACKREST_REPO1_CIPHER_PASS="${config.sops.placeholder."pgbackrest/aes_encryption_key"}"
      PGBACKREST_REPO1_S3_KEY="${config.sops.placeholder."pgbackrest/backblaze_key_id"}"
      PGBACKREST_REPO1_S3_KEY_SECRET="${config.sops.placeholder."pgbackrest/backblaze_key"}"
    '';
    owner = "pgbackrest";
  };

  programs.ssh.extraConfig = ''
    Host 10.0.0.3
      User postgres
      IdentityFile /etc/ssh/pgbackrest_ed25519
      IdentitiesOnly yes
  '';

  systemd.services."postgresql-pgbackrest-backup" = {
    path = [ pkgs.pgbackrest ];

    description = "Backup the PostgreSQL database using pgbackrest";
    after = [ "postgresql.service" "network-online.target" ];
    requires = [ "postgresql.service" ];
    wants = [ "network-online.target" ];
    wantedBy = [ "multi-user.target" ];
    reloadTriggers = [
      "/run/secrets/postgres/password"
      config.sops.templates."pgbackrest.env".path
      "/run/secrets/pgbackrest/backblaze_key"
      "/run/secrets/pgbackrest/backblaze_key_id"
    ];

    serviceConfig = {
      Type = "oneshot";
      User = "postgres";
      Group = "postgres";
      EnvironmentFile = config.sops.templates."pgbackrest.env".path;
      ReadOnlyPaths = [ config.sops.templates."pgbackrest.env".path ];
    };

    script = ''
      set -e

      pgbackrest --stanza=pg1 stanza-create
      pgbackrest --stanza=pg1 --type=full backup
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
