# Tornium Infrastructure
This describes the reproducible portion of Tornium's infrastructure built on top of NixOS and how servers should be started.

**NOTE:** This infrastructure is built around Tornium's current server infrastructure and may require changes for alternate servers.

# 0. Create Server
Create a server on a cloud provider (or otherwise set up a server). It should have an IPv4 address. Preferably, it should be running Ubuntu.

# 1. Install NixOS
Use [`nix-community/nixos-anywhere`](https://github.com/nix-community/nixos-anywhere) to install NixOS on the server. For Hetzner, the `./flake.nix` is sufficient to handle the hardware configuration. You will need to replace the SSH public key in `./configuration.nix` with yours to be able to sign into the server once NixOS is installed.

Run the following within `/infra` to set up in Hetzner cloud for x86.

```bash
nix run github:nix-community/nixos-anywhere -- deploy --flake ".#hetzner-cloud" --target-host root@{{ host }}
```

