{ config, lib, pkgs, ... }:

let
  pgbackrestDefaults = {
    enable = false;
    primaryHost = "10.0.0.5";
    replicaHost = "10.0.0.4";
  };

  cfg = config.services.postgresql-pgbackrest;
in {
  options.services.postgresql-pgbackrest = {
    enable = lib.mkEnableOption {
      default = pgbackrestDefaults.enable;
      description = "Enable pgbackrest repository host";
    };

    primaryHost = lib.mkOption {
      type = lib.types.nullOr lib.types.str;
      default = pgbackrestDefaults.primaryHost;
      description = "IP of the primary PostgreSQL host (or null)";
    };

    replicaHost = lib.mkOption {
      type = lib.types.nullOr lib.types.str;
      default = pgbackrestDefaults.replicaHost;
      description = "IP of the replica PostgreSQL host (or null)";
    };
  };

  config = {
    services.pgbackrest.enable = cfg.enable;
    services.pgbackrest.settings = {
      backup-standby = "y";
      # archive-async = "y";

      compress-type = "zst";
      compress-level = 3;

      process-max = 5;
    };
    services.pgbackrest.repos = {
      b2 = {
        type = "s3";
        block = "y";
        bundle = "y";
        s3-bucket = "tornium-backups";
        s3-uri-style = "path";
        s3-endpoint = "s3.eu-central-003.backblazeb2.com";
        s3-region = "eu-central-003";
        storage-verify-tls = true;

        cipher-type = "aes-256-cbc";

        path = "/";
        retention-full = 3;
      };
    };
    services.pgbackrest.stanzas = {
      tornium = {
        settings = {
          recovery-option = "primary_conninfo=host=${pgbackrestDefaults.primaryHost} user=replicator";
        };

        instances = {
          primary.host = cfg.primaryHost;
          primary.host-cmd = "pgbackrest";
          primary.user = "postgres";
          primary.path = "/var/lib/postgresql/16";

          replica.host = cfg.replicaHost;
          replica.host-cmd = "pgbackrest";
          replica.user = "postgres";
          replica.path = "/var/lib/postgresql/16/replica";
        };
      };
    };

    systemd.services."postgresql-pgbackrest-daily-full" = {
      description = "Service to perform full backups with pgbackrest";
      wantedBy = [ "multi-user.target" ];
      after = [ "network.target" ];
      requires = [ "postgresql.service" ];
      path = [ pkgs.pgbackrest ];

      serviceConfig = {
        Type = "oneshot";
        EnvironmentFile = config.sops.templates."pgbackrest.env".path;

        User = "postgres";
        Group = "postgres";

        ExecStart = "${pkgs.pgbackrest}/bin/pgbackrest --type=full --stanza=tornium backup";
      };
    };
    systemd.timers."postgresql-pgbackrest-daily-full" = {
      description = "Timer to start the daily full backup with pgbackrest";
      wantedBy = [ "timers.target" ];

      timerConfig = {
        OnCalendar = "*-*-* 03:30:00";
        Persistent = true;
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
      Host ${pgbackrestDefaults.primaryHost} ${pgbackrestDefaults.replicaHost}
        User postgres
        IdentityFile /etc/ssh/pgbackrest_ed25519
        IdentitiesOnly yes
    '';

    environment.systemPackages = [
      (pkgs.writeShellScriptBin "pgbackrest" ''
        set -a
        source ${config.sops.templates."pgbackrest.env".path}
        set +a

        exec ${pkgs.pgbackrest}/bin/pgbackrest "$@"
      '')
    ];
  };
}
