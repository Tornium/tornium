{config, pkgs, lib, ... }:

let
  cfg = config.services.tornium-celery;

  tornium_commons_pkg = pkgs.callPackage ../../commons/package.nix {
    python3Packages = pkgs.python313Packages;
    src = ../../commons;
  };

  tornium_celery = pkgs.callPackage ../../celery/package.nix {
    python3Packages = pkgs.python313Packages;
    tornium_commons = tornium_commons_pkg;
    python-liquid = pkgs.callPackage ../../celery/python-liquid.nix { python3Packages = pkgs.python313Packages; };
    src = ../../celery;
  };
in {
  options.services.tornium-celery = {
    enable = lib.mkEnableOption "Tornium Celery workers";
    concurrency = lib.mkOption {
      type = lib.types.int;
      default = 24;
      description = "Number of Celery workers running";
    };
  };

  config = lib.mkIf cfg.enable {
    users.users.tornium-celery = {
      isSystemUser = true;
      group = "tornium";
    };

    systemd.services.tornium-celery = {
      description = "Tornium Celery workers";
      after = [ "network-online.target" "postgresql.service" ];
      wants = [ "network-online.target" ];
      restartTriggers = [ config.sops.templates."tornium-settings.json".path ];

      serviceConfig = {
        # Type = "forking";
        User = "tornium-celery";
        Group = "tornium";

        Environment = [
          "TORNIUM_SETTINGS_FILE=${config.sops.templates."tornium-settings.json".path}"
          "PYTHONPATH=${tornium_celery.srcDir}/${pkgs.python313.sitePackages}"
        ];

        WorkingDirectory = "${tornium_celery.srcDir}/tornium_celery";
        RuntimeDirectory = "tornium-celery";
        RuntimeDirectoryMode = "0755";

        Restart = "on-failure";
        RestartSec = "2s";

        # ExecStart = "${tornium_celery.pythonEnv}/bin/celery -A celery_app multi start tornium-celery -c ${toString cfg.concurrency} -Q api,quick,default --loglevel=INFO --pidfile=/var/run/tornium-celery/%n.pid --max-tasks-per-child=200 --logfile=/dev/null";
        # ExecStop = "${tornium_celery.pythonEnv}/bin/celery -A celery_app multi stop --pidfile=/var/run/tornium-celery/%n.pid";
        # ExecReload = "${tornium_celery.pythonEnv}/bin/celery -A celery_app multi restart tornium-celery -c ${toString cfg.concurrency} -Q api,quick,default --loglevel=INFO --pidfile=/var/run/tornium-celery/%n.pid --max-tasks-per-child=200 --logfile=/dev/null";

        Type = "simple";
        ExecStart = "${tornium_celery.pythonEnv}/bin/celery -A celery_app worker -c ${toString cfg.concurrency} --queues=api,quick,default --loglevel=INFO --max-tasks-per-child=200";

        NoNewPrivileges = true;
        PrivateTmp = true;
        ProtectSystem = "strict";
        ProtectHome = true;
        LockPersonality = true;
        RestrictSUIDSGID = true;

        ReadWritePaths = [ "/run/tornium-celery" ];
      };
    };
  };
}
