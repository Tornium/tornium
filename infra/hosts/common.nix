{ ... }:

{
  imports = [
    ../common/default.nix
    ../modules/fail2ban-ssh.nix
  ];

  deployment.replaceUnknownProfiles = false;

  deployment.keys."sops-age-key.secret" = {
    keyFile = ../age-key.txt;
    destDir = "/run/keys";
    user = "root";
    group = "root";
    permissions = "0600";
  };

  boot.loader.grub.device = "/dev/sda";
  fileSystems."/" = {
    device = "/dev/sda1";
  };
}
