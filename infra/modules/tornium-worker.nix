{ config, pkgs, lib, ... }:

# For information on setting up this Elixir worker (and Elixir applications in general), see
# this guide on the nixpkgs git repo: 
# https://github.com/NixOS/nixpkgs/blob/master/doc/languages-frameworks/beam.section.md

let
  cfg = config.services.tornium-worker;

  tornium_worker = pkgs.callPackage ../../worker/package.nix {
    mixEnv = cfg.environment;
  };
in {
  options.services.tornium-worker = {
    enable = lib.mkEnableOption "Tornium Elixir worker";
    environment = lib.mkOption {
      type = lib.types.enum [ "prod" "dev" "test" ];
      description = "Elixir environment to run the elixir worker on";
      default = "prod";
    };
  };

  config = lib.mkIf cfg.enable {
    users.users.tornium-worker = {
      isSystemUser = true;
      group = "tornium";
    };

    environment.systemPackages = with pkgs; [ beam28Packages.elixir_1_19 tornium_worker ];

    sops.templates."tornium-worker.env" = {
      content = ''
      DISCORD_TOKEN=${config.sops.placeholder."tornium/discord/bot_token"}
      MIX_ENV=${cfg.environment}
      RELEASE_COOKIE=${config.sops.placeholder."tornium/worker/cookie"}
      DATABASE_URL=ecto://Tornium:${config.sops.placeholder."postgres/password"}@127.0.0.1:5432/Tornium
      '';
      owner = "tornium";
      group = "tornium";
      mode = "0440";
    };

    systemd.services.tornium-worker = {
      description = "Tornium Elixir worker";
      after = [ "network-online.target" "postgresql.service" ];
      wants = [ "network-online.target" ];
      requires = [ "network-online.target" "postgresql.service" ];
      restartTriggers = [ config.sops.templates."tornium-worker.env".path ];

      environment = {
        RELEASE_TMP = "/run/tornium-worker";
      };

      serviceConfig = {
        Type = "forking";
        User = "tornium-worker";
        Group = "tornium";

        WorkingDirectory = "/run/tornium-worker";
        RuntimeDirectory = "tornium-worker";
        RuntimeDirectoryMode = "0755";

        Restart = "on-failure";
        RestartSec = "2s";

        ExecStart = "${tornium_worker}/bin/tornium daemon";
        ExecStop = "${tornium_worker}/bin/tornium stop";
        ExecReload = "${tornium_worker}/bin/tornium restart";

        NoNewPrivileges = true;
        PrivateTmp = true;
        ProtectSystem = "strict";
        ProtectHome = true;
        LockPersonality = true;
        RestrictSUIDSGID = true;

        ReadWritePaths = [ "/run/tornium-worker" ];
        EnvironmentFile = config.sops.templates."tornium-worker.env".path;
        ReadOnlyPaths = [ config.sops.templates."tornium-worker.env".path ];
      };
    };
  };
}
