{ pkgs, ... }:

{
  imports = [
    ./users
  ];

  # Clean /tmp on boot
  boot.cleanTmpDir = true;

  # Hard-link identical files together to save storage space
  nix.autoOptimiseStore = true;

  time.timeZone = "UTC";

  networking.firewall.enable = true;

  environment.systemPackages = with pkgs; [
    curl
    gitMinimal
    git
    htop
    vim
  ];

  # Limit the systemd journal to 100 MB of disk or the
  # last 7 days of logs, whichever happens first.
  services.journald.extraConfig = ''
    SystemMaxUse=100M
    MaxFileSec=7day
  '';

  services.openssh.enable = true;
  services.openssh.settings.PasswordAuthentication = false;
  networking.firewall.allowedTCPPorts = [ 22 ];

  users.users.root.openssh.authorizedKeys.keys = [
      "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIP56l+rwxRYqgo50JP920oiI8syFJw9k+nSfe608JjBa webmaster@deek.sh"
  ];
}
