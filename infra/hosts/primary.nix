{ ... }:

{
  imports = [
    ./common.nix
    ../modules/nginx.nix
    ../modules/nginx-prometheus-exporter.nix
    ../modules/postgresql.nix
    ../modules/postgresql-pgbackrest.nix
    ../modules/postgresql-pgbackrest-exporter.nix
    ../modules/redis.nix
    ../modules/tornium-web.nix
    ../modules/tornium-celery.nix
    ../modules/tornium-celery-beat.nix
    ../modules/tornium-celery-exporter.nix
    ../modules/tornium-worker.nix
    ../modules/prometheus.nix
    ../common/default.nix
    ../common/users/default.nix
  ];

  services.nginx.enable = true;
  services.tornium-nginx.enable-proxy = true;
  services.tornium-nginx.enable-proxy-gateway = true;
  services.tornium-nginx.enable-status = true;

  services.postgresql-pgbackrest.enable = true;
  services.postgresql-pgbackrest.primaryHost = null;

  services.prometheus.exporters.pgbackrest.enable = true;
  services.prometheus.exporters.pgbackrest.logLevel = "debug";

  services.prometheus.enable = true;

  services.tornium-web.enable = true;
  services.tornium-web.hostname = "tornium.com";

  services.tornium-celery.enable = true;
  services.tornium-celery-beat.enable = true;
  services.tornium-celery-exporter.enable = true;

  services.tornium-worker.enable = true;
  services.tornium-worker.environment = "prod";
  services.tornium-worker.node = "tornium@10.0.0.5";
  services.tornium-worker.db_ip = "127.0.0.1";

  disko.devices.disk.disk1.device = "/dev/disk/by-id/scsi-0QEMU_QEMU_HARDDISK_113406207";

  deployment.tags = ["tornium-primary" "prod" "db" "prometheus"];
}
