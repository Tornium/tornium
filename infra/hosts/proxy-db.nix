{ ... }:

{
  imports = [
    ./common.nix
    ../modules/nginx.nix
    ../modules/nginx-prometheus-exporter.nix
    ../modules/postgresql-replica.nix
    # ../modules/postgresql-pgbackrest.nix
    ../modules/prometheus.nix
    ../common/default.nix
    ../common/users/default.nix
  ];

  networking.hostName = "tornium-proxy-db";

  services.nginx.enable = true;
  services.tornium-nginx.enable-proxy = true;

  services.prometheus.enable = true;

  deployment.tags = ["tornium-proxy-db" "prod" "proxy" "db" "prometheus"];
}
