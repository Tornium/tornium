{ config, lib, pkgs, ... }:

let
  pgbackrestDefaults = {
    enable = false;
    primaryHost = "10.0.0.5";
    replicaHost = "10.0.0.4";
  };

  cfg = config.services.postgresql-pgbackrest;
  repo = import ./pgbackrest-repo.nix;
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

    scheduleFullBackup = lib.mkOption {
      type = lib.types.bool;
      # Only the primary (where primaryHost is null) should take the daily backup. Both the primary
      # and the replica import this module, and the stanza is shared, so scheduling it everywhere
      # starts two full backups of the same stanza at 03:30.
      default = cfg.enable && cfg.primaryHost == null;
      defaultText = lib.literalExpression "cfg.enable && cfg.primaryHost == null";
      description = "Run the daily full backup from this host.";
    };
  };

  config = {
    services.pgbackrest.enable = cfg.enable;
    services.pgbackrest.settings = {
      backup-standby = "y";
      archive-async = "y";
      spool-path = "/var/spool/pgbackrest";

      compress-type = "zst";
      compress-level = 3;

      process-max = 5;

      archive-push-queue-max = "20GiB";
    };
    systemd.tmpfiles.rules = [
      "d /var/spool/pgbackrest 0750 postgres postgres -"
    ];

    services.pgbackrest.repos = repo.repos;
    services.pgbackrest.stanzas = {
      ${repo.stanza} = {
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

    systemd.services."postgresql-pgbackrest-daily-full" = lib.mkIf cfg.scheduleFullBackup {
      description = "Service to perform full backups with pgbackrest";
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
    systemd.timers."postgresql-pgbackrest-daily-full" = lib.mkIf cfg.scheduleFullBackup {
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
