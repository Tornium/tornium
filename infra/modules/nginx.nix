{ config, lib, ... }:

let
  cfg = config.services.tornium-nginx;

  proxyGatewayConfig  = {
    services.nginx.upstreams."backend" = {
      servers = {
        "10.0.0.2:80" = {};
        "127.0.0.1:80" = {};
        "10.0.0.4:80" = {};
      };
      extraConfig = ''
        random;
        keepalive 10;
      '';
    };

    services.nginx.appendHttpConfig = ''
      limit_req_zone $binary_remote_addr zone=global:1m rate=2000r/m;
    '';

    services.nginx.virtualHosts."api-proxy-gateway" = {
      # We need to open this to all interfaces as we don't know the IP of the node.
      listen = [ { addr = "0.0.0.0"; port = 80; } ];

      locations."/" = {
        proxyPass = "http://backend";

        # Manually adding a host header is required to prevent CF from blocking the request
        # due to a Host header mismatch.
        extraConfig = ''
          proxy_set_header Host api.torn.com;
          add_header X-Proxy $upstream_addr;

          access_log /dev/null;
          
          limit_req zone=global burst=2000 nodelay;
          limit_req_status 429;

          proxy_read_timeout 5s;
          proxy_connect_timeout 5s;
          allow 10.0.0.0/24;
          allow 127.0.0.1;
          deny all;
        '';
      };
    };
  };
  proxyConfig = {
    services.nginx.virtualHosts."api-proxy" = {
      listen = [ { addr = "127.0.0.1"; port = 80; } ];
      locations."/" = {
        proxyPass = "https://api.torn.com";
        extraConfig = ''
          access_log /dev/null;
          proxy_read_timeout 5s;
          proxy_connect_timeout 5s;
        '';
      };
    };
  };
  statusConfig = {
    services.nginx.virtualHosts."nginx-status" = {
      listen = [ { addr = "127.0.0.1"; port = 8080; } ];

      locations."/status" = {
        extraConfig = ''
          stub_status;

          allow 127.0.0.1;
          deny all;
        '';
      };
    };
  };
in {
  options.services.tornium-nginx = {
    enable-proxy-gateway = lib.mkEnableOption "Tornium API proxy gateway";
    enable-proxy = lib.mkEnableOption "Tornium API proxy";
    enable-status = lib.mkEnableOption "NGINX Prometheus exporter";
  };

  # TODO: Block requests not proxied by CF
  config = lib.mkMerge [
    {
      services.nginx = {
        enable = true;
        recommendedProxySettings = true;
        recommendedTlsSettings = true;
      };

      networking.firewall.allowedTCPPorts = [ 80 ];
    }

    (lib.mkIf cfg.enable-proxy-gateway proxyGatewayConfig)
    (lib.mkIf cfg.enable-proxy proxyConfig)
    (lib.mkIf cfg.enable-status statusConfig)
  ];

}
