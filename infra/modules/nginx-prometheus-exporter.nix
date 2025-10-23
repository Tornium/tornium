{ ... }:

{
  services.prometheus.exporters.nginx.enable = true;
  services.prometheus.exporters.nginx.port = 9113;
  services.prometheus.exporters.nginx.scrapeUri = "http://127.0.0.1:8080/status";
}
