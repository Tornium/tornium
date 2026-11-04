{ lib, modulesPath, ... }:

{
  imports = [
    (modulesPath + "/profiles/qemu-guest.nix")
    ../common/default.nix
    ../modules/fail2ban-ssh.nix
    ../disk-config.nix
  ];

  deployment.replaceUnknownProfiles = false;

  deployment.keys."sops-age-key.secret" = {
    # The CWD must be ./infra and the AGE private key must be at .age-key
    keyCommand = [ "cat" ".age-key" ];
    destDir = "/run/keys";
    user = "root";
    group = "root";
    permissions = "0600";
  };
}
