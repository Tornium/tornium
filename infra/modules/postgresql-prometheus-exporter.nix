{ config, lib, ... }:

{
  sops.templates."prometheus-postgres-exporter.env" = {
    content = ''
      DATA_SOURCE_NAME=postgresql://Tornium:${config.sops.placeholder."postgres/password"}@localhost:5432/Tornium?sslmode=disable
    '';
    owner = config.services.prometheus.exporters.postgres.user;
  };

  services.prometheus.exporters.postgres.enable = true;
  services.prometheus.exporters.postgres.environmentFile = config.sops.templates."prometheus-postgres-exporter.env".path;

  services.prometheus.scrapeConfigs = lib.mkAfter [
    {
      job_name = "PostgreSQL";
      static_configs = [
        { targets = [ "127.0.0.1:${toString config.services.prometheus.exporters.postgres.port}" ]; }
      ];
      scrape_interval = "5s";
    }
  ];
}
