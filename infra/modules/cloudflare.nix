{ lib, ... }:

let
  cloudflareIPsv4 = [
    # IPv4 blocks come from https://www.cloudflare.com/ips-v4/#
    "173.245.48.0/20"
    "103.21.244.0/22"
    "103.22.200.0/22"
    "103.31.4.0/22"
    "141.101.64.0/18"
    "108.162.192.0/18"
    "190.93.240.0/20"
    "188.114.96.0/20"
    "197.234.240.0/22"
    "198.41.128.0/17"
    "162.158.0.0/15"
    "104.16.0.0/13"
    "104.24.0.0/14"
    "172.64.0.0/13"
    "131.0.72.0/22"
  ];
  cloudflareIPsv6 = [
    # IPv6 blocks come from https://www.cloudflare.com/ips-v6/#
    "2400:cb00::/32"
    "2606:4700::/32"
    "2803:f800::/32"
    "2405:b500::/32"
    "2405:8100::/32"
    "2a06:98c0::/29"
    "2c0f:f248::/32"
  ];

  cloudflareIPs = cloudflareIPsv4 ++ cloudflareIPsv6;

  mkNginxRules = directive: lib.concatMapStrings (ip: "${directive} ${ip};\n") cloudflareIPs;
  mkIptablesRules = ports: 
    let
      rules = [
        "iptables -A INPUT -i lo -j ACCEPT"
        "ip6tables -A INPUT -i lo -j ACCEPT"
        "iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT"
        "ip6tables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT"
      ] ++ 
        # Cloudflare IPv4
        (lib.concatMap (ip: map (port: 
          "iptables -A INPUT -p tcp -s ${ip} --dport ${toString port} -j ACCEPT"
        ) ports) cloudflareIPsv4) ++
        # Cloudflare IPv6
        (lib.concatMap (ip: map (port: 
          "ip6tables -A INPUT -p tcp -s ${ip} --dport ${toString port} -j ACCEPT"
        ) ports) cloudflareIPsv6) ++
        # Final Drops
        (lib.concatMap (port: [
          "iptables -A INPUT -p tcp --dport ${toString port} -j DROP"
          "ip6tables -A INPUT -p tcp --dport ${toString port} -j DROP"
        ]) ports);
    in
      lib.concatStringsSep "\n" rules;
in {
  nginxRealIpRules = ''
    real_ip_header CF-Connecting-IP;
    real_ip_recursive on;

    ${mkNginxRules "set_real_ip_from"}
  '';
  firewallRules = mkIptablesRules [80 443];
}
