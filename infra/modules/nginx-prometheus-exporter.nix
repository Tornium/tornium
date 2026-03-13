{ lib, ... }:

{
  services.prometheus.exporters.nginx.enable = true;
  services.prometheus.exporters.nginx.port = 9113;
  services.prometheus.exporters.nginx.scrapeUri = "http://127.0.0.1:8080/status";

  services.prometheus.scrapeConfigs = lib.mkAfter [
    {
      job_name = "NGINX";
      static_configs = [
        { targets = [ "127.0.0.1:9113" ]; }
      ];
      scrape_interval = "15s";
    }
  ];
}
