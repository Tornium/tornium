{ config, lib, ... }:

{
  services.prometheus.exporters.node.enable = true;

  services.prometheus.scrapeConfigs = lib.mkAfter [
    {
      job_name = "Node";
      static_configs = [
        { targets = [ "127.0.0.1:${toString config.services.prometheus.exporters.node.port}" ]; }
      ];
      scrape_interval = "15s";
    }
  ];
}
