# The pgBackRest stanza and B2 repository, shared by ./postgresql-pgbackrest.nix (the servers) and
# the restore test in ../flake.nix (`nix run .#restore-test`), so a dev machine restores from
# exactly the repository production writes to.
#
# This is a plain attribute set, not a NixOS module: import it with `import ./pgbackrest-repo.nix`.
#
# `repos` is in the format of services.pgbackrest.repos. Credentials are never set here: they come
# from the PGBACKREST_REPO1_CIPHER_PASS, PGBACKREST_REPO1_S3_KEY and PGBACKREST_REPO1_S3_KEY_SECRET
# environment variables (see sops.templates."pgbackrest.env" in ./postgresql-pgbackrest.nix).

{
  stanza = "tornium";

  repos = {
    b2 = {
      type = "s3";
      block = "y";
      bundle = "y";
      s3-bucket = "tornium-backups";
      s3-uri-style = "path";
      s3-endpoint = "s3.eu-central-003.backblazeb2.com";
      s3-region = "eu-central-003";
      storage-verify-tls = true;

      cipher-type = "aes-256-cbc";

      path = "/";
      retention-full = 3;
    };
  };
}
