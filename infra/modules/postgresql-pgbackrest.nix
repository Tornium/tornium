{ config, pkgs, ... }:

{
  services.pgbackrest.enable = true;
  services.pgbackrest.settings = {
    backup-standby = "y";
    start-fast = "y";
    compress-type = "gz";
    repo1-retention-full = 1;
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
    tornium = {
      settings = {
        recovery-option = "primary_conninfo=host=10.0.0.3 user=replicator";
      };
      instances = {
        localhost.database = "Tornium";
        localhost.user = "postgres";
        localhost.path = "/var/lib/postgresql/16/replica";

        pg2.host = "10.0.0.3";
        pg2.host-cmd = "pgbackrest";
        pg2.user = "postgres";
        pg2.path = "/var/lib/postgresql/16/main";
      };
    };
  };

  sops.templates."pgbackrest.env" = {
    content = ''
      PGBACKREST_REPO1_CIPHER_PASS="${config.sops.placeholder."pgbackrest/aes_encryption_key"}"
      PGBACKREST_REPO1_S3_KEY="${config.sops.placeholder."pgbackrest/backblaze_key_id"}"
      PGBACKREST_REPO1_S3_KEY_SECRET="${config.sops.placeholder."pgbackrest/backblaze_key"}"
    '';
    owner = "postgres";
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
    # requires = [ "postgresql.service" ];
    wants = [ "network-online.target" ];
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

      pgbackrest --stanza=tornium stanza-create
      pgbackrest --stanza=tornium --type=full --backup-standby backup
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

  environment.systemPackages = [
    (pkgs.writeShellScriptBin "pgbackrest" ''
      export $(cat ${config.sops.templates."pgbackrest.env".path} | xargs)
      exec ${pkgs.pgbackrest}/bin/pgbackrest "$@"
    '')
  ];
}
