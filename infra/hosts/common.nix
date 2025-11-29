{ ... }:

{
  imports = [
    ../common/default.nix
    ../modules/fail2ban-ssh.nix
  ];

  deployment.replaceUnknownProfiles = false;

  boot.loader.grub.device = "/dev/sda";
  fileSystems."/" = {
    device = "/dev/sda1";
  };
}
