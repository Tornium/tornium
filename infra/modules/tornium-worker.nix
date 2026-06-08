{ config, pkgs, lib, ... }:

# For information on setting up this Elixir worker (and Elixir applications in general), see
# this guide on the nixpkgs git repo: 
# https://github.com/NixOS/nixpkgs/blob/master/doc/languages-frameworks/beam.section.md

let
  cfg = config.services.tornium-worker;

  tornium_worker = pkgs.callPackage ../../worker/package.nix {
    mixEnv = cfg.environment;
  };

  min_beam_port = 40000;
  max_beam_port = 40100;
in {
  options.services.tornium-worker = {
    enable = lib.mkEnableOption "Tornium Elixir worker";
    environment = lib.mkOption {
      type = lib.types.enum [ "prod" "dev" "test" ];
      description = "Elixir environment to run the elixir worker on";
      default = "prod";
    };
    node = lib.mkOption {
      type = lib.types.str;
      description = "Name of the Elixir node";
    };
    db_ip = lib.mkOption {
      type = lib.types.str;
      description = "IP address of the database";
      default = "10.0.0.5";
    };
  };

  config = lib.mkIf cfg.enable {
    users.users.tornium-worker = {
      isSystemUser = true;
      group = "tornium";
    };

    # We want to wrap the tornium command to inject the environment variables provided by the
    # tornium-worker.env file such that it can connect to the production instance of the worker.
    # The command itself is provided by the mix build.
    # See https://github.com/NixOS/nixpkgs/blob/master/doc/languages-frameworks/beam.section.md#example-of-creating-a-service-for-an-elixir---phoenix-project-example-of-creating-a-service-for-an-elixir---phoenix-project
    environment.systemPackages = lib.mkAfter [
      (pkgs.writeShellScriptBin "tornium" ''
        set -a
        . ${config.sops.templates."tornium-worker.env".path}
        set +a

        exec ${tornium_worker}/bin/tornium "$@"
      '')
    ];

    # ELIXIR_ERL_OPTIONS needs to be set to limit the port range BEAM would use for node-to-node communication. See
    # https://elixirforum.com/t/cannot-set-port-range-for-node-node-connections-kernel-inet-dist-listen-min-max
    # https://elixirforum.com/t/is-ssl-dist-optfile-the-way-to-secure-cluster-of-beam-nodes-how-to-secure-connections-of-publicly-exposed-beam-nodes-and-epmd
    # https://mix.hexdocs.pm/main/Mix.Tasks.Release.html#module-vm-args-and-env-sh-env-bat
    sops.templates."tornium-worker.env" = {
      content = ''
      DISCORD_TOKEN=${config.sops.placeholder."tornium/discord/bot_token"}
      MIX_ENV=${cfg.environment}
      RELEASE_COOKIE=${config.sops.placeholder."tornium/worker/cookie"}
      RELEASE_NODE=${cfg.node}
      RELEASE_DISTRIBUTION=name
      DATABASE_URL=ecto://Tornium:${config.sops.placeholder."postgres/password"}@${cfg.db_ip}:5432/Tornium
      LOCAL_ONLY=0
      ELIXIR_ERL_OPTIONS="-kernel inet_dist_listen_min ${builtins.toString min_beam_port} inet_dist_listen_max ${builtins.toString max_beam_port}"
      '';
      owner = "tornium";
      group = "tornium";
      mode = "0440";
    };

    systemd.services.tornium-worker = {
      description = "Tornium Elixir worker";
      after = [ "network-online.target" ];
      wants = [ "network-online.target" ];
      requires = [ "network-online.target" ];
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

    # EPMD requires port 4369 for node discovery. Then we want to set the port range for the private
    # network to access the other Elixir nodes.
    networking.firewall.extraCommands = lib.mkAfter ''
      iptables -I INPUT 1 -p tcp -s 127.0.0.1 --dport 4369 -j ACCEPT
      iptables -I INPUT 2 -p tcp -s 10.0.0.0/24 --dport 4369 -j ACCEPT
      iptables -I INPUT 3 -p tcp --dport 4369 -j DROP

      iptables -I INPUT 4 -p tcp -s 10.0.0.0/24 --dport ${builtins.toString min_beam_port}:${builtins.toString max_beam_port} -j ACCEPT
      iptables -I INPUT 5 -p tcp --dport ${builtins.toString min_beam_port}:${builtins.toString max_beam_port} -j DROP
    '';

    services.prometheus.scrapeConfigs = lib.mkAfter [
      {
        job_name = "Tornium Worker";
        static_configs = [
          { targets = [ "127.0.0.1:4021" ]; }
        ];
        scrape_interval = "15s";
      }
    ];
  };
}
