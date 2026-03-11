{ config, pkgs, lib, ... }:

let
  cfg = config.services.tornium-web;
  # src = "/srv/tornium";

  tornium_commons_pkg = pkgs.callPackage ../../commons/package.nix {
    python3Packages = pkgs.python313Packages;
    src = ../../commons;
  };

  tornium_celery_pkg = pkgs.callPackage ../../celery/package.nix {
    python3Packages = pkgs.python313Packages;
    tornium_commons = tornium_commons_pkg;
    python-liquid = pkgs.callPackage ../../celery/python-liquid.nix { python3Packages = pkgs.python313Packages; };
    src = ../../celery;
  };

  tornium_application = pkgs.callPackage ../../application/package.nix {
    python3 = pkgs.python313;
    python3Packages = pkgs.python313Packages;
    tornium_commons = tornium_commons_pkg;
    tornium_celery = tornium_celery_pkg;
    src = ../../application;
  };
in {
  options.services.tornium-web = {
    enable = lib.mkEnableOption "Tornium web service";

    port = lib.mkOption {
      type = lib.types.port;
      default = 5000;
      description = "Port for the web service to listen on.";
    };

    hostname = lib.mkOption {
      type = lib.types.str;
      description = "Bare hostname without scheme (e.g. tornium.com).";
    };

    torn_api_uri = lib.mkOption {
      type = lib.types.str;
      description = "Torn API URL to make API calls against.";
      default = "https://api.torn.com";
    };
  };

  config = lib.mkIf cfg.enable {
    sops.templates."tornium-web-settings.json" = {
      content = ''
        {
          "bot_token": "${config.sops.placeholder."tornium/discord/bot_token"}",
          "bot_application_id": ${config.sops.placeholder."tornium/discord/bot_application_id"},
          "bot_application_public": "${config.sops.placeholder."tornium/discord/bot_application_public"}",
          "bot_client_secret": "${config.sops.placeholder."tornium/discord/bot_client_secret"}",
          "flask_secret": "${config.sops.placeholder."tornium/flask/secret"}",
          "flask_domain": "${cfg.hostname}",
          "flask_admin_passphrase": "${config.sops.placeholder."tornium/flask/admin_passphrase"}",
          "db_dsn": "postgresql://Tornium:${config.sops.placeholder."postgres/password"}@127.0.0.1:5432/Tornium",
          "redis_dsn": "redis://:${config.sops.placeholder."redis/password"}@127.0.0.1",
          "admin_passphrase": "${config.sops.placeholder."tornium/flask/admin_passphrase"}",
          "torn_api_uri": "${cfg.torn_api_uri}",
          "admin_users": [2383326],
          "banned_users": {}
        }
      '';
      owner = "tornium-web";
    };

    users.users.tornium-web = {
      isSystemUser = true;
      group = "tornium";
    };

    systemd.services.tornium-web = {
      description = "Tornium Flask application";
      after = [ "network-online.target" "postgresql.service" ];
      wants = [ "network-online.target" ];

      serviceConfig = {
        Type = "simple";
        User = "tornium-web";
        Group = "tornium";

        Environment = [
          "TORNIUM_SETTINGS_FILE=${config.sops.templates."tornium-web-settings.json".path}"
          "PYTHONPATH=${tornium_application.srcDir}/${pkgs.python313.sitePackages}"
        ];

        WorkingDirectory = "${tornium_application.srcDir}";
        RuntimeDirectory = "tornium";
        RuntimeDirectoryMode = "0755";

        Restart = "on-failure";
        RestartSec = "2s";

        ExecStart = "${tornium_application.gunicornCmd} ${tornium_application.wsgi}";

        NoNewPrivileges = true;
        PrivateTmp = true;
        ProtectSystem = "strict";
        ProtectHome = true;
        LockPersonality = true;
        RestrictSUIDSGID = true;

        ReadWritePaths = [ "/run/tornium" ];
      };
    };
  };
}
