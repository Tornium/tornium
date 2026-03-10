{ ... }:

{
  services.prometheus.enable = true;
  services.prometheus.port = 9090;
  services.prometheus.scrapeConfigs = [];

  networking.firewall.extraCommands = ''
    iptables -A INPUT -p tcp -s 10.0.0.0/24 --dport 9090 -j ACCEPT
    iptables -A INPUT -p tcp --dport 9090 -j DROP
  '';
}
