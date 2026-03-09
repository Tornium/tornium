{ ... }:

{
  imports = [
    ./common.nix
    ../modules/nginx-proxy.nix
    ../modules/nginx-prometheus-exporter.nix
    ../modules/nginx-status.nix
    ../modules/postgresql.nix
    # ../modules/postgresql-pgbackrest.nix
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
  services.prometheus.enable = true;

  deployment.tags = ["tornium-primary" "prod" "db" "prometheus"];
}
