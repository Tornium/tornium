{ config, pkgs, lib, ... }:

# Based upon https://github.com/taalbubbl/nix-files/blob/b4a403bcc7b9474ce201a97e3e67d9a2cbee7e7f/modules/pgbackrest-exporter.nix

let 
  cfg = config.services.prometheus.exporters.pgbackrest;

  pgbackrest-exporter = pkgs.buildGoModule rec {
    pname = "pgbackrest-exporter";
    version = "0.24.0";

    src = pkgs.fetchFromGitHub {
      owner = "woblerr";
      repo = "pgbackrest_exporter";
      rev = "v${version}";
      hash = "sha256-TXqq3kymJpzBtSlu+578BDysvEAe4T1uyKVyEyidTEc=";
    };

    vendorHash = null;

    meta = with lib; {
      description = "Prometheus exporter for pgBackRest";
      homepage = "https://github.com/woblerr/pgbackrest_exporter";
      license = licenses.mit;
      mainProgram = "pgbackrest_exporter";
    };
  };
in {
  options.services.prometheus.exporters.pgbackrest = {
    enable = lib.mkEnableOption "Enable the pgBackRest Prometheus exporter";

    port = lib.mkOption {
      type = lib.types.port;
      default = 9854;
      description = "Port on which to expose metrics.";
    };

    listenAddress = lib.mkOption {
      type = lib.types.str;
      default = "0.0.0.0";
      description = "Address on which to expose metrics.";
    };

    telemetryPath = lib.mkOption {
      type = lib.types.str;
      default = "/metrics";
      description = "HTTP path under which to expose metrics.";
    };

    collectInterval = lib.mkOption {
      type = lib.types.int;
      default = 30;
      description = "Metrics collection interval in seconds.";
    };

    backrestConfig = lib.mkOption {
      type = lib.types.nullOr lib.types.path;
      default = null;
      example = "/etc/pgbackrest/pgbackrest.conf";
      description = "Full path to the pgBackRest configuration file.";
    };

    backrestConfigIncludePath = lib.mkOption {
      type = lib.types.nullOr lib.types.path;
      default = null;
      description = "Full path to additional pgBackRest configuration files.";
    };

    stanzaInclude = lib.mkOption {
      type = lib.types.listOf lib.types.str;
      default = [ ];
      example = [ "main" ];
      description = "Stanzas to collect metrics for. Empty = all stanzas.";
    };

    stanzaExclude = lib.mkOption {
      type = lib.types.listOf lib.types.str;
      default = [ ];
      description = "Stanzas to exclude from metric collection.";
    };

    backupType = lib.mkOption {
      type = lib.types.nullOr (lib.types.enum [ "full" "incr" "diff" ]);
      default = null;
      description = "Restrict collection to a specific backup type.";
    };

    databaseCount = lib.mkOption {
      type = lib.types.bool;
      default = false;
      description = "Expose number of databases in backups. Requires pgBackRest >= v2.41.";
    };

    databaseParallelProcesses = lib.mkOption {
      type = lib.types.int;
      default = 1;
      description = "Parallel processes for database count collection.";
    };

    databaseCountLatest = lib.mkOption {
      type = lib.types.bool;
      default = false;
      description = "Expose number of databases in latest backups. Requires pgBackRest >= v2.41.";
    };

    referenceCount = lib.mkOption {
      type = lib.types.bool;
      default = false;
      description = "Expose number of references to other backups.";
    };

    verboseWal = lib.mkOption {
      type = lib.types.bool;
      default = false;
      description = "Expose WALMin/WALMax as additional metric labels.";
    };

    logLevel = lib.mkOption {
      type = lib.types.enum [ "debug" "info" "warn" "error" ];
      default = "info";
      description = "Log level.";
    };

    logFormat = lib.mkOption {
      type = lib.types.enum [ "logfmt" "json" ];
      default = "logfmt";
      description = "Log output format.";
    };

    extraFlags = lib.mkOption {
      type = lib.types.listOf lib.types.str;
      default = [ ];
      description = "Additional flags passed verbatim to pgbackrest_exporter.";
    };
  };

  config = lib.mkIf cfg.enable {
    systemd.services.pgbackrest-exporter = {
      description = "Prometheus exporter for pgBackRest";
      wantedBy = [ "multi-user.target" ];
      after = [ "network.target" ];
      restartTriggers = [ config.sops.templates."pgbackrest.env".path ];

      path = [ pkgs.pgbackrest ];

      serviceConfig = {
        EnvironmentFile = config.sops.templates."pgbackrest.env".path;

        ExecStart = 
          let
            args =
              [
                "--web.listen-address=${cfg.listenAddress}:${toString cfg.port}"
                "--web.telemetry-path=${cfg.telemetryPath}"
                "--collect.interval=${toString cfg.collectInterval}"
                "--log.level=${cfg.logLevel}"
                "--log.format=${cfg.logFormat}"
                "--backrest.database-parallel-processes=${toString cfg.databaseParallelProcesses}"
              ]
              ++ lib.optionals (cfg.backrestConfig != null) [ "--backrest.config=${cfg.backrestConfig}" ]
              ++ lib.concatMap (s: [ "--backrest.stanza-include=${s}" ]) cfg.stanzaInclude
              ++ lib.concatMap (s: [ "--backrest.stanza-exclude=${s}" ]) cfg.stanzaExclude
              ++ lib.optionals (cfg.backupType != null) [ "--backrest.backup-type=${cfg.backupType}" ]
              ++ lib.optionals cfg.databaseCount [ "--backrest.database-count" ]
              ++ lib.optionals cfg.databaseCountLatest [ "--backrest.database-count-latest" ]
              ++ lib.optionals cfg.referenceCount [ "--backrest.reference-count" ]
              ++ lib.optionals cfg.verboseWal [ "--backrest.verbose-wal" ]
              ++ cfg.extraFlags;
          in
          "${pgbackrest-exporter}/bin/pgbackrest_exporter ${lib.escapeShellArgs args}";

        Restart = "on-failure";
        RestartSec = "5s";
        
        User = "postgres";
        Group = "postgres";

        BindReadOnlyPaths = [
          # Required for the exporter and pgbackrest binaries to run on NixOS
          "/nix/store"
          
          # Required for Go/system to resolve the 'postgres' user and DNS
          "/etc/passwd"
          "/etc/group"
          "/etc/nsswitch.conf"
          "/etc/resolv.conf"

          # Required for pgBackRest to function (ADJUST THESE TO YOUR SETUP)
          "/etc/pgbackrest/pgbackrest.conf"    # Your config location
          "/var/lib/pgbackrest"     # Your backup repository path
        ];
        
        # TODO: Limit access of the exporter to the file system
        ProtectSystem = "strict";
        ProtectHome = true;
        PrivateTmp = true;
      };
    };

    services.prometheus.scrapeConfigs = lib.mkAfter [
      {
        job_name = "PostgreSQL pgBackRest Exporter";
        static_configs = [
          { targets = [ "127.0.0.1:${toString cfg.port}" ]; }
        ];
        scrape_interval = "15s";
      }
    ];
  };
}
