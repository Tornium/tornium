{config, pkgs, lib, ... }:

let
  cfg = config.services.tornium-celery-beat;

  tornium_commons_pkg = pkgs.callPackage ../../commons/package.nix {
    python3Packages = pkgs.python313Packages;
    tornium_oc_graph = pkgs.python313Packages.tornium_oc_graph;
    src = ../../commons;
  };

  tornium_celery = pkgs.callPackage ../../celery/package.nix {
    python3Packages = pkgs.python313Packages;
    tornium_commons = tornium_commons_pkg;
    python-liquid = pkgs.callPackage ../../celery/python-liquid.nix { python3Packages = pkgs.python313Packages; };
    src = ../../celery;
  };
in {
  options.services.tornium-celery-beat = {
    enable = lib.mkEnableOption "Tornium Celery workers";
  };

  config = lib.mkIf cfg.enable {
    users.users.tornium-celery = {
      isSystemUser = true;
      group = "tornium";
    };

    systemd.services.tornium-celery-beat = {
      description = "Tornium Celery scheduler";
      after = [ "network-online.target" "postgresql.service" "tornium-celery.service" ];
      wants = [ "network-online.target" ];
      restartTriggers = [ config.sops.templates."tornium-settings.json".path ];

      serviceConfig = {
        Type = "simple";
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

        ExecStart = "${tornium_celery.pythonEnv}/bin/celery -A celery_app beat -s /run/tornium-celery/celerybeat-schedule";

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
