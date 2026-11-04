# Tornium Infrastructure
This describes the reproducible portion of Tornium's infrastructure built on top of NixOS and how servers should be started, updated, et al.

**NOTE:** This infrastructure is built around Tornium's current server infrastructure and may require changes for alternate servers.

# Database Backups
The PostgreSQL database is backed up with pgBackrest, under the `tornium` stanza, to the `tornium-backups` Backblaze B2 bucket. This is done with a daily full backup at 03:30 UTC and continuous WAL archiving.

To manually validate the backups, run the following commands on the primary node:
- Force WAL switch and confirms the WAL file reaches B2: `sudo -u postgres pgbackrest --stanza=tornium check`
- Lists the backups and their WAL ranges: `sudo -u postgres pgbackrest --stanza=tornium info`
- Re-reads and checksums the B2 bucket: `sudo -u postgres pgbackrest --stanza=tornium verify`

## Restore Test
To prove the backups can actually be restored, run the restore test from a development machine. It will restore the latest backup from B2 into a temporary directory, replay the archived WAL, start a temporary PostgreSQL database, and check the data. It can run on any Linux or Apple Silicon machine with Nix. Run it from `infra/` as a normal user (PostgreSQL won't run as root). It will decrypt the B2 credentials from `secrets/secrets.yaml` with your `.age-key`, the same key colmena uses.

```sh
nix run .#restore-test
nix run .#restore-test -- --set 20261101-033001F --quick --keep
nix run .#restore-test -- --help
```

This downloads the whole backup from B2 and will need about 1.3× the database size of free drive space. The restored instance only listens on a private Unix socket, so it shoudln't interfere with a local PostgreSQL.

# Creating a New Server
## 0. Create Server
Create a server on a cloud provider (or otherwise set up a server). It should have an IPv4 address. Preferably, it should be running Ubuntu.

## 1. Install NixOS
Use [`nix-community/nixos-anywhere`](https://github.com/nix-community/nixos-anywhere) to install NixOS on the server. For Hetzner, the `./flake.nix` is sufficient to handle the hardware configuration. You will need to replace the SSH public key in `./configuration.nix` with yours to be able to sign into the server once NixOS is installed.

Run the following within `/infra` to set up in Hetzner cloud for x86.

```bash
nix run github:nix-community/nixos-anywhere -- deploy --flake ".#hetzner-cloud" --target-host root@{{ host }}
```

## 2. Deploying the Host
TODO

```sh
colmena build
colmena apply
```

# Updating an Existing Server
An existing server that's already been setup can be updated with Colmena:
```sh
colmena build
colmena apply
```

## Updating the Secrets File
The secrets file can be configured in the `$EDITOR` assuming there is one of the keys in `./.sops.yaml` in the system.
```sh
nix-shell -p sops --run "sops secrets/secrets.yaml"
```

# Internal Network
`10.0.0.2` => tornium-proxy-1
`10.0.0.4` => tornium-proxy-db
`10.0.0.5` => tornium-primary
