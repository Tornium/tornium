{ ... }:

{
  # systemd.services.nginx-prometheus-exporter = {
  #   description = "Nginx Prometheus Exporter";
  #   after = [ "network.target" "nginx.service" ];
  #   wants = [ "nginx.service" ];
  #   wantedBy = [ "multi-user.target" ];

  #   serviceConfig = {
  #     ExecStart = "${pkgs.nginx_exporter}/bin/nginx-prometheus-exporter \
  #     -nginx.scrape-uri http://127.0.0.1:8080/status";
  #     Restart = "always";
  #   };
  # };

  services.prometheus.exporters.nginx.enable = true;
  services.prometheus.exporters.nginx.port = 9113;
  services.prometheus.exporters.nginx.scrapeUri = "http://127.0.0.1:8080/status";
}
