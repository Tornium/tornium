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
    }
  ];
}
