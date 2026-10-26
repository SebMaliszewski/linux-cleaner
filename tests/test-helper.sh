#!/bin/bash
# Non-root tests of mint-cleaner-helper using fake apt lists (no real removals).
set -u
H="$(cd "$(dirname "$0")/.." && pwd)/mint-cleaner-helper"
T=$(mktemp -d); trap 'rm -rf "$T"' EXIT
[ "$(id -u)" -ne 0 ] || { echo "run as normal user"; exit 1; }
fail=0
t() { # expected_rc description cmd...
  local exp="$1" d="$2"; shift 2; local out rc
  out=$("$@" 2>&1); rc=$?
  if [ "$rc" -eq "$exp" ]; then echo "PASS [$rc] $d"; else echo "FAIL [got $rc want $exp] $d"; fail=1; fi
  printf '%s\n' "$out" | sed 's/^/      | /'
}
K=6.8.0-45-generic
printf 'libfoo1\nlibbar2\n' > "$T/clean"
printf 'libfoo1\nlinux-image-6.8.0-40-generic\nlinux-modules-6.8.0-40-generic\nlinux-headers-6.8.0-40\nlinux-headers-6.8.0-40-generic\n' > "$T/old"
printf 'libfoo1\nlinux-image-6.8.0-40-generic\nlinux-image-6.8.0-45-generic\n' > "$T/running"
printf 'linux-headers-6.8.0-45\n' > "$T/runhdr"
: > "$T/empty"
F() { MINT_CLEANER_FAKE_APT_LIST="$T/$1" MINT_CLEANER_FAKE_KREL=$K "$H" "${@:2}"; }
t 64 "no args"                 "$H"
t 64 "two args"                "$H" apt-clean extra
t 64 "unknown subcommand"      "$H" 'rm -rf /'
t 64 "old name w/o mode"       "$H" apt-autoremove
t 64 "injection attempt"       "$H" 'apt-clean;id'
t 77 "apt-clean needs root"    "$H" apt-clean
t 77 "journal needs root"      "$H" journal-vacuum
t 0  "strict: empty list"           F empty apt-autoremove-check-strict
t 0  "strict: no kernels"           F clean apt-autoremove-check-strict
t 3  "strict: old kernels blocked"  F old   apt-autoremove-check-strict
t 3  "strict run: blocked"          F old   apt-autoremove-strict
t 0  "standard: old kernels allowed"   F old apt-autoremove-check-standard
t 0  "standard run (test mode, no-op)" F old apt-autoremove-standard
t 3  "standard: running kernel blocked" F running apt-autoremove-check-standard
t 3  "standard run: running blocked"    F running apt-autoremove-standard
t 3  "standard: running common headers blocked" F runhdr apt-autoremove-check-standard
t 0  "strict run, no kernels (test mode, no-op)" F clean apt-autoremove-strict
t 0  "real (non-fake) check-strict via apt-get -s" "$H" apt-autoremove-check-strict
t 77 "real run w/o root refused" "$H" apt-autoremove-standard
if [ $fail -eq 0 ]; then echo "ALL TESTS PASSED"; else echo "SOME TESTS FAILED"; exit 1; fi
