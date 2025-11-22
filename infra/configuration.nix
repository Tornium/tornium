{
  modulesPath,
  lib,
  pkgs,
  ...
} @ args:
{
  imports = [
    (modulesPath + "/installer/scan/not-detected.nix")
    (modulesPath + "/profiles/qemu-guest.nix")
    ./disk-config.nix
  ];
  boot.loader.grub = {
    # no need to set devices, disko will add all devices that have a EF02 partition to the list already
    # devices = [ ];
    efiSupport = true;
    efiInstallAsRemovable = true;
  };
  services.openssh.enable = true;
  services.openssh.settings.PasswordAuthentication = false;
  networking.firewall.allowedTCPPorts = [ 22 ];

  environment.systemPackages = map lib.lowPrio [
    pkgs.curl
    pkgs.gitMinimal
  ];

  users.users.root.openssh.authorizedKeys.keys = [
      "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIP56l+rwxRYqgo50JP920oiI8syFJw9k+nSfe608JjBa webmaster@deek.sh"
  ];

  system.stateVersion = "24.05";

  # This is added to the server by colmena in ./hosts/common.nix
  sops.age.keyFile = "/run/keys/sops-age-key.secret";
  sops.defaultSopsFile = ./secrets/secrets.yaml;
  sops.defaultSopsFormat = "yaml";

  # ---- SECRETS ---- #
  sops.secrets."example_key" = {};
}
