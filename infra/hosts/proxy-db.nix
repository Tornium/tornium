{ ... }:

{
  imports = [
    ./common.nix
    ../modules/nginx-proxy.nix
    ../modules/nginx-prometheus-exporter.nix
    ../modules/nginx-status.nix
    ../modules/postgresql-replica.nix
    ../modules/prometheus.nix
    ../common/default.nix
    ../common/users/default.nix
  ];

  networking.hostName = "tornium-proxy-db";

  services.nginx.enable = true;
  services.prometheus.enable = true;

  deployment.tags = ["prod" "proxy" "db" "prometheus"];
}
