#!/usr/bin/env bash

# Restore the latest pgBackRest backup from B2 on this machine and check it:
#
#   cd infra && nix run .#restore-test -- [options]
#
# Restores into a scratch directory, replays the archived WAL, starts a throwaway PostgreSQL
# instance on it (Unix socket only, WAL archiving off) and runs sanity checks against the data.
#
# Packaged in ../flake.nix, which puts Nix's PostgreSQL 16, pgBackRest, sops and jq first on the
# PATH and sets RESTORE_TEST_CONFIG (a pgBackRest config with only the B2 repository settings) and
# RESTORE_TEST_STANZA. The B2 credentials and encryption key are decrypted from
# secrets/secrets.yaml with sops (using ./.age-key, like colmena, or $SOPS_AGE_KEY_FILE), unless
# PGBACKREST_REPO1_CIPHER_PASS, PGBACKREST_REPO1_S3_KEY and PGBACKREST_REPO1_S3_KEY_SECRET are
# already set.

set -euo pipefail

usage() {
  cat <<'EOF'
Usage: nix run .#restore-test -- [options]

Restores the latest pgBackRest backup from B2 into a scratch directory, replays the archived WAL,
starts a throwaway PostgreSQL (Unix socket only, WAL archiving off) and checks the data.
Downloads the whole backup, and needs free disk of about 1.3x the database size.

Options:
  --dir DIR             working directory (default: ~/.cache/tornium-restore-test)
  --set LABEL           restore this backup instead of the latest (see `pgbackrest info`)
  --keep                keep the restored data directory afterwards
  --quick               skip reading every row with pg_dumpall
  --max-data-lag SECS   fail if the newest restored commit is older than this (default: 3600, 0 = off)
  --process-max N       parallel download/decompress processes (default: 2)
  --secrets FILE        sops file with the pgbackrest secrets (default: ./secrets/secrets.yaml)
  --config FILE         use another repository config instead of production's
  -h, --help            show this help
EOF
}

log() { echo "restore-test: $*"; }
fail() {
  log "ERROR: $*"
  exit 1
}

dir="${XDG_CACHE_HOME:-$HOME/.cache}/tornium-restore-test"
backup_set=latest
keep=0
read_all=1
max_data_lag=3600
secrets=./secrets/secrets.yaml
config="${RESTORE_TEST_CONFIG:?}"
stanza="${RESTORE_TEST_STANZA:?}"
database=Tornium
port=5499
recovery_timeout=10800
free_space_ratio=1.3

while [ $# -gt 0 ]; do
  case "$1" in
    --dir) dir="${2:?--dir needs a value}"; shift 2 ;;
    --set) backup_set="${2:?--set needs a value}"; shift 2 ;;
    --keep) keep=1; shift ;;
    --quick) read_all=0; shift ;;
    --max-data-lag) max_data_lag="${2:?--max-data-lag needs a value}"; shift 2 ;;
    --process-max) export PGBACKREST_PROCESS_MAX="${2:?--process-max needs a value}"; shift 2 ;;
    --secrets) secrets="${2:?--secrets needs a value}"; shift 2 ;;
    --config) config="${2:?--config needs a value}"; shift 2 ;;
    -h | --help) usage; exit 0 ;;
    *) usage >&2; fail "unknown option: $1" ;;
  esac
done

# === Authentication ===
if [ -z "${PGBACKREST_REPO1_CIPHER_PASS:-}" ] || [ -z "${PGBACKREST_REPO1_S3_KEY:-}" ] || [ -z "${PGBACKREST_REPO1_S3_KEY_SECRET:-}" ]; then
  [ -f "$secrets" ] || fail "no credentials in the environment and $secrets not found (run from infra/ or pass --secrets)"

  if [ -z "${SOPS_AGE_KEY_FILE:-}" ] && [ -z "${SOPS_AGE_KEY:-}" ] && [ -f .age-key ]; then
    export SOPS_AGE_KEY_FILE="$PWD/.age-key"
  fi

  secret() { sops --decrypt --extract "[\"pgbackrest\"][\"$1\"]" "$secrets"; }
  log "decrypting pgbackrest credentials from $secrets"

  cipher_pass=$(secret aes_encryption_key) || fail "could not decrypt $secrets (is your age key in .age-key or \$SOPS_AGE_KEY_FILE?)"
  s3_key=$(secret backblaze_key_id) || fail "could not decrypt backblaze_key_id"
  s3_key_secret=$(secret backblaze_key) || fail "could not decrypt backblaze_key"

  export PGBACKREST_REPO1_CIPHER_PASS="${PGBACKREST_REPO1_CIPHER_PASS:-$cipher_pass}"
  export PGBACKREST_REPO1_S3_KEY="${PGBACKREST_REPO1_S3_KEY:-$s3_key}"
  export PGBACKREST_REPO1_S3_KEY_SECRET="${PGBACKREST_REPO1_S3_KEY_SECRET:-$s3_key_secret}"
fi

# === Temporary working directory ===
mkdir -p "$dir"
chmod 0700 "$dir"
dir=$(cd "$dir" && pwd)
log "working in $dir"

data_dir="$dir/data"
socket_dir="$dir/run"
pg_log="$dir/postgresql.log"

# pgBackRest reads its config from PGBACKREST_CONFIG; its lock and log files stay in the working dir.
export PGBACKREST_CONFIG="$config"
export PGBACKREST_LOCK_PATH="$dir/lock"
export PGBACKREST_LOG_PATH="$dir/log"

start_ts=$(date +%s)
backup_label=""
failed_checks=0

cleanup() {
  local rc=$?

  if [ -f "$data_dir/postmaster.pid" ]; then
    log "stopping restored instance"
    pg_ctl stop -D "$data_dir" -m fast -w >/dev/null 2>&1 || pg_ctl stop -D "$data_dir" -m immediate -w >/dev/null 2>&1 || true
  fi

  if [ "$rc" -eq 0 ]; then
    log "PASSED (backup $backup_label, $(($(date +%s) - start_ts))s)"
  else
    if [ -f "$pg_log" ]; then
      log "last lines of the restored instance's log:"
      tail -n 40 "$pg_log" || true
    fi
    log "FAILED"
  fi

  if [ "$keep" != "1" ]; then
    rm -rf "$data_dir"
  fi
  exit "$rc"
}
trap cleanup EXIT

psql_q() {
  # psql_q <sql> [database]
  psql -X -q -A -t -v ON_ERROR_STOP=1 -h "$socket_dir" -p "$port" -U postgres -d "${2:-$database}" -c "$1"
}

# A log left by an earlier --keep run must not be printed as if it came from this one.
rm -f "$pg_log"

# ---- 1. Pick the backup to restore ---------------------------------------------------------------
log "reading repository info for stanza $stanza"

# pgBackRest prints its errors to stdout, so show what was captured if the command itself fails.
if ! info_raw=$(pgbackrest --stanza="$stanza" --output=json info); then
  while IFS= read -r line; do
    log "pgbackrest: $line"
  done <<<"$info_raw"
  fail "pgbackrest info failed"
fi

# With a wrong encryption key, pgBackRest puts the undecryptable bytes into its JSON unescaped,
# which jq rejects. Raw control characters are never valid in JSON, so drop them.
info_json=$(LC_ALL=C tr -d '\000-\037' <<<"$info_raw")

stanza_status=$(jq -r '.[0].status.code' <<<"$info_json")
stanza_message=$(jq -r '.[0].status.message' <<<"$info_json")
if [ "$stanza_status" != "0" ]; then
  # The stanza message is generic ("other"); the per-repository messages say what went wrong.
  while IFS= read -r repo_message; do
    log "repository: $repo_message"
  done < <(jq -r '.[0].repo[]?.status | select(.code != 0) | .message | split("\n")[0]' <<<"$info_json")

  if jq -e 'any(.[0].repo[]?.status.message; test("^\\[FormatError\\] unable to load info file"))' <<<"$info_json" >/dev/null 2>&1; then
    log "the repository files can't be parsed, which usually means PGBACKREST_REPO1_CIPHER_PASS is wrong"
  fi

  fail "stanza status is $stanza_status ($stanza_message)"
fi

if [ "$backup_set" = "latest" ]; then
  backup_json=$(jq -c '.[0].backup | last' <<<"$info_json")
else
  backup_json=$(jq -c --arg set "$backup_set" '.[0].backup[] | select(.label == $set)' <<<"$info_json")
fi

if [ -z "$backup_json" ] || [ "$backup_json" = "null" ]; then
  fail "backup $backup_set not found in the repository"
fi

backup_label=$(jq -r '.label' <<<"$backup_json")
backup_size=$(jq -r '.info.size' <<<"$backup_json")
backup_stop=$(jq -r '.timestamp.stop' <<<"$backup_json")
backup_age=$((start_ts - backup_stop))

if [ "$(jq -r '.error // false' <<<"$backup_json")" = "true" ]; then
  fail "backup $backup_label is flagged with errors in the repository"
fi

log "restoring backup $backup_label ($((backup_size / 1024 / 1024)) MiB, finished $((backup_age / 3600))h ago)"

# ---- 2. Make sure the restore fits ---------------------------------------------------------------
rm -rf "$data_dir"
install -d -m 0700 "$data_dir" "$socket_dir"

free_bytes=$(df --output=avail -B1 "$dir" | tail -n 1 | tr -d ' ')
needed_bytes=$(awk -v s="$backup_size" -v r="$free_space_ratio" 'BEGIN { printf "%.0f", s * r }')
if [ "$free_bytes" -lt "$needed_bytes" ]; then
  fail "not enough free space in $dir: need $((needed_bytes / 1024 / 1024)) MiB, have $((free_bytes / 1024 / 1024)) MiB"
fi

# ---- 3. Restore ----------------------------------------------------------------------------------
# --archive-mode=off makes the restored cluster write archive_mode=off into postgresql.auto.conf so
# it can never push WAL into the production repository (we also force it off on the command line).
restore_args=(--stanza="$stanza" --pg1-path="$data_dir" --archive-mode=off --type=default)
if [ "$backup_set" != "latest" ]; then
  restore_args+=(--set="$backup_set")
fi
pgbackrest "${restore_args[@]}" restore

# The restored postgresql.conf is the production one (on NixOS it pointed into /nix/store), and the
# production pg_hba.conf lives outside the data directory. Replace both with minimal local-only ones.
# pgBackRest restores the /nix/store symlink as a file that keeps the store's read-only mode, so
# remove the old files rather than writing over them.
rm -f "$data_dir/postgresql.conf" "$data_dir/pg_hba.conf" "$data_dir/pg_ident.conf"
cat >"$data_dir/postgresql.conf" <<EOF
# Written by the pgBackRest restore test; replaces the production configuration from the backup.
listen_addresses = ''
port = $port
unix_socket_directories = '$socket_dir'
hba_file = '$data_dir/pg_hba.conf'
ident_file = '$data_dir/pg_ident.conf'
archive_mode = off
hot_standby = off
max_connections = 20
shared_buffers = 128MB
logging_collector = off
EOF
printf 'local all all trust\n' >"$data_dir/pg_hba.conf"
: >"$data_dir/pg_ident.conf"

# ---- 4. Start it and replay WAL ------------------------------------------------------------------
# Settings passed with -c override anything restored into postgresql.auto.conf (e.g. ALTER SYSTEM).
# hot_standby=off keeps clients out until replay is done and skips the "insufficient parameter
# settings" checks, so the throwaway instance can run with much smaller limits than production.

pg_opts="-c listen_addresses='' -c port=$port -c unix_socket_directories='$socket_dir'"
pg_opts+=" -c hba_file='$data_dir/pg_hba.conf' -c ident_file='$data_dir/pg_ident.conf'"
pg_opts+=" -c archive_mode=off -c archive_command='' -c hot_standby=off -c primary_conninfo=''"
pg_opts+=" -c shared_preload_libraries=''"

log "starting restored instance and replaying archived WAL (timeout ${recovery_timeout}s)"
pg_ctl start -D "$data_dir" -l "$pg_log" -w -t "$recovery_timeout" -o "$pg_opts" >/dev/null ||
  fail "restored instance failed to start"

# pg_ctl can return before WAL replay is finished, so wait for the end of recovery explicitly.
deadline=$((SECONDS + recovery_timeout))
until [ "$(psql_q 'SELECT pg_is_in_recovery()' postgres 2>/dev/null)" = "f" ]; do
  pg_ctl status -D "$data_dir" >/dev/null 2>&1 || fail "restored instance exited during WAL replay"
  [ "$SECONDS" -lt "$deadline" ] || fail "WAL replay did not finish within ${recovery_timeout}s"
  sleep 5
done
grep -q "archive recovery complete" "$pg_log" || fail "recovery finished but the log has no 'archive recovery complete'"
log "WAL replay finished and the instance was promoted"

# ---- 5. Sanity checks ----------------------------------------------------------------------------
last_xact=$(psql_q "SELECT COALESCE(floor(EXTRACT(EPOCH FROM pg_last_xact_replay_timestamp()))::bigint::text, '')" postgres)
if [ -n "$last_xact" ]; then
  data_lag=$((start_ts - last_xact))
  [ "$data_lag" -ge 0 ] || data_lag=0
  log "newest restored commit is from $(date -u -d "@$last_xact" '+%F %T UTC') (${data_lag}s before the test started)"
  if [ "$max_data_lag" -gt 0 ] && [ "$data_lag" -gt "$max_data_lag" ]; then
    log "CHECK FAILED: data lag ${data_lag}s exceeds ${max_data_lag}s - is WAL archiving keeping up?"
    failed_checks=$((failed_checks + 1))
  fi
else
  log "no transactions were replayed from WAL"
  if [ "$max_data_lag" -gt 0 ]; then
    log "CHECK FAILED: no WAL replayed, so the data lag cannot be checked"
    failed_checks=$((failed_checks + 1))
  fi
fi

psql_q "SELECT 1" >/dev/null || fail "cannot connect to database $database"

# check <name> <SQL returning a single boolean>
check() {
  local result
  if result=$(psql_q "$2" 2>&1) && [ "$result" = "t" ]; then
    log "check ok: $1"
  else
    log "CHECK FAILED: $1 -> ${result:-<no output>}"
    failed_checks=$((failed_checks + 1))
  fi
}
check "user table has rows" 'SELECT count(*) > 0 FROM "user"'
check "faction table has rows" 'SELECT count(*) > 0 FROM faction'
check "server table has rows" 'SELECT count(*) > 0 FROM server'

if [ "$read_all" = "1" ]; then
  log "reading every table with pg_dumpall"

  if pg_dumpall -h "$socket_dir" -p "$port" -U postgres >/dev/null; then
    log "check ok: pg_dumpall read all data"
  else
    log "CHECK FAILED: pg_dumpall could not read all data"
    failed_checks=$((failed_checks + 1))
  fi
fi

[ "$failed_checks" -eq 0 ] || fail "$failed_checks check(s) failed"
