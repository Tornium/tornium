{ config, lib, ... }:

let 
  inherit (config.services.tornium-web) gunicornSocket;
in
{
  imports = [
    ./node-prometheus-exporter.nix
    ./tornium-web.nix
  ];

  services.prometheus.enable = true;
  services.prometheus.port = 9090;
  services.prometheus.scrapeConfigs = [];

  # We need to ensure that the prometheus service can connect to the Gunicorn socket
  # for pulling metrics from the Flask server.
  systemd.services.prometheus.serviceConfig.ReadWritePaths = lib.optionals config.services.tornium-web.enable [ gunicornSocket ];
  users.users.prometheus.extraGroups = lib.optionals config.services.tornium-web.enable [ "nginx" ];
  # TODO: We need to give the socket a seperate group to avoid giving prometheus the nginx group.

  networking.firewall.extraCommands = lib.mkAfter ''
    iptables -A INPUT -p tcp -s 10.0.0.0/24 --dport 9090 -j ACCEPT
    iptables -A INPUT -p tcp --dport 9090 -j DROP
  '';
}
