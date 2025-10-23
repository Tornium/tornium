{ ... }:

{
  services.prometheus.enable = true;
  services.prometheus.port = 9090;
  services.prometheus.scrapeConfigs = [
    {
      job_name = "NGINX";
      static_configs = [
        { targets = [ "127.0.0.1:9113" ]; }
      ];
      scrape_interval = "15s";
    }
  ];

  networking.firewall.extraCommands = ''
    iptables -A INPUT -p tcp -s 10.0.0.0/24 --dport 9090 -j ACCEPT
    iptables -A INPUT -p tcp --dport 9090 -j DROP
  '';
}
