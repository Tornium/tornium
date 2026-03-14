{ config, lib, pkgs, ...}:

let 
  cfg = config.services.tornium-celery-exporter;

  prometheus_client_021 = pkgs.python313Packages.buildPythonPackage rec {
    pname = "prometheus_client";
    version = "0.21.1";
    pyproject = true;

    src = pkgs.python313Packages.fetchPypi {
      inherit pname version;
      hash = "sha256-JSUFpyKsBLBFa+BcBfdfRddgwpEf/EXyoGvK7Z864/s=";
    };

    nativeBuildInputs = [ pkgs.python313Packages.setuptools ];
  };

  pyjwt_29 = pkgs.python313Packages.buildPythonPackage rec {
    pname = "pyjwt";
    version = "2.9.0";
    pyproject = true;

    src = pkgs.python313Packages.fetchPypi {
      inherit pname version;
      hash = "sha256-fh5bVsxzVDKnNpy/oO/lD6ET6+zcBK5pIt66i4RYLQw=";
    };

    nativeBuildInputs = [ pkgs.python313Packages.setuptools ];
  };

  redis_5 = pkgs.python313Packages.buildPythonPackage rec {
    pname = "redis";
    version = "5.3.0";
    pyproject = true;

    src = pkgs.python313Packages.fetchPypi {
      inherit pname version;
      hash = "sha256-jWnS3eEaEtyF0Nv1xFV3pa8EjiRW9wd9h601wcgcMQ4=";
    };

    nativeBuildInputs = [ pkgs.python313Packages.setuptools ];
    propagatedBuildInputs = [ pyjwt_29 ];
  };

  celery_exporter = pkgs.python313Packages.buildPythonPackage rec {
    pname = "prometheus_exporter_celery";
    version = "0.11.2";
    pyproject = true;

    src = pkgs.python313Packages.fetchPypi {
      inherit pname version;
      hash = "sha256-SCt9BrfN9MiM3RHNgC+e/Ao3cC4oZid9vFTUbQt8KBA=";
    };

    nativeBuildInputs = with pkgs.python313Packages; [ poetry-core ];
    propagatedBuildInputs = with pkgs.python313Packages; [
      flask
      arrow
      celery
      click
      loguru
      pretty-errors
      prometheus_client_021
      redis_5
      timy
      waitress
    ];
  };

  pythonEnv = pkgs.python313.withPackages (ps: [
    celery_exporter
  ]);
in {
  options.services.tornium-celery-exporter = {
    enable = lib.mkEnableOption "Tornium Celery Prometheus exporter";
    port = lib.mkOption {
      type = lib.types.port;
      default = 9808;
      description = "Port for celery-exporter Prometheus metrics endpoint";
    };
  };

  config = lib.mkIf cfg.enable {
    sops.templates."tornium-celery-exporter.env" = {
      content = ''
        CE_BROKER_URL=redis://:${config.sops.placeholder."redis/password"}@127.0.0.1
      '';
      owner = "tornium";
      group = "tornium";
      mode = "0440";
    };

    systemd.services.tornium-celery-exporter = {
      description = "Tornium Celery Prometheus exporter";
      after = [ "network-online.target" "tornium-celery.service" "redis-tornium.service" ];
      wants = [ "network-online.target" ];
      requires = [ "tornium-celery.service" "redis-tornium.service" ];
      restartTriggers = [ config.sops.templates."tornium-celery-exporter.env".path ];

      serviceConfig = {
        Type = "simple";
        User = "tornium-celery";
        Group = "tornium";

        EnvironmentFile = config.sops.templates."tornium-celery-exporter.env".path;
        ExecStart = ''${pkgs.bash}/bin/bash -c "${pythonEnv}/bin/python3.13 -c \"from src.cli import cli; cli()\" --broker-url=$CE_BROKER_URL"'';

        Restart = "on-failure";
        RestartSec = "2s";

        NoNewPrivileges = true;
        PrivateTmp = true;
        ProtectSystem = "strict";
        ProtectHome = true;
        LockPersonality = true;
        RestrictSUIDSGID = true;

        WorkingDirectory = "${celery_exporter}/lib/python3.13/site-packages/src";
        RuntimeDirectory = "tornium-celery-exporter";
        RuntimeDirectoryMode = "0775";
      };
    };

    services.prometheus.scrapeConfigs = lib.mkAfter [
      {
        job_name = "Tornium Celery Exporter";
        static_configs = [
          { targets = [ "127.0.0.1:${toString cfg.port}" ]; }
        ];
        scrape_interval = "5s";
      }
    ];
  };
}
