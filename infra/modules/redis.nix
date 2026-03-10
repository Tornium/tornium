{ config, lib, ... }:

{
  users.groups."redis-tornium" = {};
  users.users.redis-tornium = {
    isSystemUser = true;
    group = "redis-tornium";
  };

  sops.secrets."redis/password" = { owner = "redis-tornium"; };

  services.redis.servers.tornium = {
    user = "redis-tornium";
    group = "redis-tornium";
    enable = true;
    bind = "127.0.0.1";
    port = 6379;
    requirePassFile = config.sops.secrets."redis/password".path;
  };

  sops.templates."prometheus-redis-exporter.json" = {
    content = ''
      {
        "redis://127.0.0.1:6379": "${config.sops.placeholder."redis/password"}"
      }
    '';
    owner = "redis-tornium";
  };

  services.prometheus.exporters.redis.enable = true;
  services.prometheus.exporters.redis.listenAddress = "127.0.0.1";
  services.prometheus.exporters.redis.extraFlags = [ "-redis.password-file=${config.sops.templates."prometheus-redis-exporter.json".path}" ];
  services.prometheus.exporters.redis.user = "redis-tornium";
  services.prometheus.exporters.redis.group = "redis-tornium";

  services.prometheus.scrapeConfigs = lib.mkAfter [
    {
      job_name = "Redis";
      static_configs = [
        { targets = [ "127.0.0.1:${toString config.services.prometheus.exporters.redis.port}" ]; }
      ];
      scrape_interval = "15s";
    }
  ];
}
