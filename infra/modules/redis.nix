{ config, ... }:

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
}
