{ ... }:

{
  imports = [
    ./common.nix
    ../modules/nginx.nix
    ../modules/nginx-prometheus-exporter.nix
    ../modules/postgresql.nix
    # ../modules/postgresql-pgbackrest.nix
    ../modules/redis.nix
    ../modules/tornium-web.nix
    ../modules/tornium-celery.nix
    ../modules/tornium-celery-beat.nix
    ../modules/tornium-worker.nix
    ../modules/prometheus.nix
    ../common/default.nix
    ../common/users/default.nix
  ];

  # This needs to be overriden from the boot device in ./common.nix as the Hetzner volume will take up sda
  boot.loader.grub.device = "/dev/sdb";
  fileSystems."/" = {
    device = "/dev/sdb1";
  };

  networking.hostName = "tornium-primary";

  services.nginx.enable = true;
  services.tornium-nginx.enable-proxy = true;
  services.tornium-nginx.enable-proxy-gateway = true;
  services.tornium-nginx.enable-status = true;

  services.prometheus.enable = true;

  services.tornium-web.enable = true;
  services.tornium-web.hostname = "tornium.com";

  services.tornium-celery.enable = true;
  services.tornium-celery-beat.enable = true;

  services.tornium-worker.enable = true;
  services.tornium-worker.environment = "prod";

  deployment.tags = ["tornium-primary" "prod" "db" "prometheus"];
}
