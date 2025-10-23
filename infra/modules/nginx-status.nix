{ ... }:

{
  services.nginx = {
    enable = true;
    recommendedProxySettings = true;
    recommendedTlsSettings = true;

    virtualHosts."nginx-status" = {
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
}
