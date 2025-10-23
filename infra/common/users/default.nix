{ config, pkgs, ... }:

{
  users.users.tiksan = {
    isNormalUser = true;
    openssh.authorizedKeys.keys = [
      "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIP56l+rwxRYqgo50JP920oiI8syFJw9k+nSfe608JjBa webmaster@deek.sh"
    ];
  };

  # Use the SSH public key(s) of tiksan for the root user
  # users.users.root.openssh.authorizedKeys = config.users.users.tiksan.openssh.authorizedKeys.keys;
}
