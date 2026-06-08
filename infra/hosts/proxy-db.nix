{ ... }:

{
  imports = [
    ./common.nix
    ../modules/nginx.nix
    ../modules/nginx-prometheus-exporter.nix
    ../modules/postgresql-replica.nix
    # ../modules/postgresql-pgbackrest.nix
    ../modules/prometheus.nix
    ../modules/tornium-worker.nix
    ../common/default.nix
    ../common/users/default.nix
  ];

  services.nginx.enable = true;
  services.tornium-nginx.enable-proxy = true;

  services.prometheus.enable = true;

  services.tornium-worker.enable = true;
  services.tornium-worker.environment = "prod";
  services.tornium-worker.node = "tornium@10.0.0.4";

  deployment.tags = ["tornium-proxy-db" "prod" "proxy" "db" "prometheus"];
}
