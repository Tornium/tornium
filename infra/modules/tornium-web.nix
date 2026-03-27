{ config, pkgs, lib, ... }:

let
  cfg = config.services.tornium-web;
  cloudflare = import ./cloudflare.nix { inherit lib; };

  tornium_commons_pkg = pkgs.callPackage ../../commons/package.nix {
    python3Packages = pkgs.python313Packages;
    tornium_oc_graph = pkgs.python313Packages.tornium_oc_graph;
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
    users.users.tornium-web = {
      isSystemUser = true;
      group = "tornium";
    };

    sops.templates."tornium-settings.json" = {
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
      owner = "tornium";
      group = "tornium";
      mode = "0440";
    };

    systemd.services.tornium-web = {
      description = "Tornium Flask application";
      after = [ "network-online.target" "postgresql.service" "tornium-celery.service" ];
      wants = [ "network-online.target" ];
      restartTriggers = [ config.sops.templates."tornium-settings.json".path ];

      serviceConfig = {
        Type = "simple";
        User = "tornium-web";
        Group = "tornium";

        Environment = [
          "RESULT_BACKEND_CELERY=file"
          "RESULT_FILE_CELERY=/run/tornium-celery"
          "TORNIUM_OC_GRAPH_LIB=${pkgs.python313Packages.tornium_oc_graph.outPath}/lib/python3.13/site-packages/tornium_oc_graph/libtornium_oc_graph_core.so"
          "TORNIUM_SETTINGS_FILE=${config.sops.templates."tornium-settings.json".path}"
          "PYTHONPATH=${tornium_application.srcDir}/${pkgs.python313.sitePackages}"
        ];

        WorkingDirectory = "${tornium_application.srcDir}";
        RuntimeDirectory = "tornium-web";
        RuntimeDirectoryMode = "0775";

        Restart = "on-failure";
        RestartSec = "2s";

        ExecStart = "${tornium_application.gunicornCmd} --workers 8 --bind unix:/run/tornium-web/gunicorn.sock ${tornium_application.wsgi}";

        NoNewPrivileges = true;
        PrivateTmp = true;
        ProtectSystem = "strict";
        ProtectHome = true;
        LockPersonality = true;
        RestrictSUIDSGID = true;

        ReadWritePaths = [ "/run/tornium-web" "/run/tornium-celery" ];
      };
    };

    systemd.sockets.tornium-web = {
      description = "UNIX socket for tornium-web.service";
      partOf = [ "tornium-web.service" ];

      listenStreams = ["/run/tornium-web/gunicorn.sock"];
    };

    services.nginx.virtualHosts."tornium-web" = {
      serverName = "tornium.com www.tornium.com";
      onlySSL = true;
      listen = [
        {
          addr = "0.0.0.0";
          port = 443;
          ssl = true;
        }
        {
          addr = "[::]";
          port = 443;
          ssl = true;
        }
      ];

      sslCertificate = config.sops.secrets."nginx/cloudflare_origin_cert".path;
      sslCertificateKey = config.sops.secrets."nginx/cloudflare_origin_key".path;

      locations."/" = {
        proxyPass = "http://unix:/run/tornium-web/gunicorn.sock";
        recommendedProxySettings = false;

        extraConfig = ''
          keepalive_timeout 30;

          proxy_buffering off;
          proxy_request_buffering off;
          proxy_set_header Host $host;
          proxy_set_header X-Real-IP $remote_addr;
          proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
          proxy_set_header X-Forwarded-Proto $scheme;

          ${cloudflare.nginxRealIpRules}
        '';
      };

      extraConfig = ''
        charset utf-8;
      '';
    };

    networking.firewall.allowedTCPPorts = lib.mkAfter [ 443 ];
    networking.firewall.extraCommands = cloudflare.firewallRules;

    environment.systemPackages = lib.mkAfter [
      (pkgs.writeShellScriptBin "tornium-gunicornc" ''
        set -euo pipefail

        export RESULT_BACKEND_CELERY=file
        export RESULT_FILE_CELERY=/run/tornium-celery
        export TORNIUM_OC_GRAPH_LIB="${pkgs.python313Packages.tornium_oc_graph.outPath}/lib/python3.13/site-packages/tornium_oc_graph/libtornium_oc_graph_core.so"
        export TORNIUM_SETTINGS_FILE="${config.sops.templates."tornium-settings.json".path}"
        export PYTHONPATH="${tornium_application.srcDir}/${pkgs.python313.sitePackages}"

        cd "${tornium_application.srcDir}"
        exec ${tornium_application.gunicornCmd} "$@"
      '')
    ];
  };
}
