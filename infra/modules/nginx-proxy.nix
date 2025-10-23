{ ... }:

{
  services.nginx = {
    enable = true;
    recommendedProxySettings = true;
    recommendedTlsSettings = true;

    virtualHosts."api-proxy-gateway" = {
      # We need to open this to all interfaces as we don't know the IP of the node.
      listen = [ { addr = "0.0.0.0"; port = 80; } ];

      locations."/" = {
        proxyPass = "https://api.torn.com";

        # Manually adding a host header is required to prevent CF from blocking the request
        # due to a Host header mismatch.
        extraConfig = ''
          proxy_set_header Host api.torn.com;

          proxy_read_timeout 5s;
          proxy_connect_timeout 5s;
          allow 10.0.0.0/24;
          allow 127.0.0.1;
          deny all;
        '';
      };
    };
  };

  networking.firewall.allowedTCPPorts = [ 80 ];
}
