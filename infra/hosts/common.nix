{ ... }:

{
  imports = [
    ../common/default.nix
  ];

  deployment.replaceUnknownProfiles = false;

  boot.loader.grub.device = "/dev/sda";
  fileSystems."/" = {
    device = "/dev/sda1";
  };
}
