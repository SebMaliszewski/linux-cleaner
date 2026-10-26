#!/bin/bash
# Mint Cleaner installer.  Usage:  sudo ./install.sh
set -euo pipefail
NAME=mint-cleaner
APPDIR=/opt/$NAME
HELPER=/usr/local/sbin/$NAME-helper
SUDOERS=/etc/sudoers.d/$NAME
DESKTOP=/usr/share/applications/$NAME.desktop
ICON=/usr/share/icons/hicolor/scalable/apps/$NAME.svg
SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

[ "$(id -u)" -eq 0 ] || { echo "Run with sudo:  sudo $0" >&2; exit 1; }
USR="${SUDO_USER:-}"
if [ -z "$USR" ] || [ "$USR" = root ]; then
  echo "Refusing: run via sudo from the user account that should use the app (SUDO_USER is empty/root)." >&2; exit 1
fi
[[ "$USR" =~ ^[a-z_][a-z0-9_-]*[$]?$ ]] || { echo "Refusing: unusual user name '$USR'." >&2; exit 1; }
id "$USR" >/dev/null 2>&1 || { echo "Unknown user $USR" >&2; exit 1; }
command -v visudo >/dev/null || { echo "visudo not found" >&2; exit 1; }

# 0) dependencies: Python GObject + GTK 3 (needed by the app)
gtk_ok() { python3 -c 'import gi; gi.require_version("Gtk","3.0")' >/dev/null 2>&1; }
command -v python3 >/dev/null || { echo "python3 not found. Install it:  sudo apt install python3" >&2; exit 1; }
if ! gtk_ok; then
  if command -v apt-get >/dev/null; then
    echo "Missing dependency: python3-gi / gir1.2-gtk-3.0 -> installing with apt-get..."
    apt-get update || echo "WARNING: apt-get update failed, trying install anyway" >&2
    apt-get install -y python3-gi gir1.2-gtk-3.0 || { echo "Could not install python3-gi gir1.2-gtk-3.0" >&2; exit 1; }
    gtk_ok || { echo "GTK 3 for Python still not importable after install" >&2; exit 1; }
  else
    echo "Missing dependency: Python GObject + GTK 3 (python3-gi, gir1.2-gtk-3.0) and apt-get is not available. Install them with your package manager and re-run." >&2
    exit 1
  fi
fi
command -v flatpak >/dev/null || echo "Note: flatpak not found - Flatpak cleaning will be unavailable (optional: sudo apt install flatpak)."

for f in mint-cleaner.py mint-cleaner-helper data/mint-cleaner.svg data/mint-cleaner.desktop.in; do
  [ -f "$SRC/$f" ] || { echo "Missing $SRC/$f" >&2; exit 1; }
done
bash -n "$SRC/mint-cleaner-helper"
python3 -m py_compile "$SRC/mint-cleaner.py"

echo "Installing $NAME for user: $USR"
# 1) app (root-owned, user cannot modify it)
install -d -o root -g root -m 0755 "$APPDIR"
install -o root -g root -m 0755 "$SRC/mint-cleaner.py" "$APPDIR/mint-cleaner.py"
install -o root -g root -m 0644 "$SRC/LICENSE" "$APPDIR/LICENSE" 2>/dev/null || true
# 2) helper (atomic replace)
install -o root -g root -m 0755 "$SRC/mint-cleaner-helper" "$HELPER.new"
mv -f "$HELPER.new" "$HELPER"
# 3) sudoers drop-in: only the fixed subcommands, validated, atomic move
TMP=$(mktemp /etc/sudoers.d/.$NAME.XXXXXX)
trap 'rm -f "$TMP"' EXIT
CMDS=""
for c in apt-clean apt-autoclean apt-autoremove-strict apt-autoremove-standard rc-purge flatpak-system journal-vacuum; do
  CMDS+="${CMDS:+, }$HELPER $c"
done
printf '# Managed by %s install.sh\n%s ALL=(root) NOPASSWD: %s\n' "$NAME" "$USR" "$CMDS" > "$TMP"
chown root:root "$TMP"; chmod 0440 "$TMP"
visudo -cf "$TMP" >/dev/null
mv -f "$TMP" "$SUDOERS"; trap - EXIT
visudo -c >/dev/null || { echo "visudo -c failed, removing $SUDOERS" >&2; rm -f "$SUDOERS"; exit 1; }
# 4) icon + launcher (system-wide)
install -D -o root -g root -m 0644 "$SRC/data/mint-cleaner.svg" "$ICON"
sed "s|@EXEC@|/usr/bin/python3 $APPDIR/mint-cleaner.py|" "$SRC/data/mint-cleaner.desktop.in" > "$DESKTOP.new"
chmod 0644 "$DESKTOP.new"; mv -f "$DESKTOP.new" "$DESKTOP"
gtk-update-icon-cache -q -t /usr/share/icons/hicolor 2>/dev/null || true
update-desktop-database -q /usr/share/applications 2>/dev/null || true
echo "Done. Installed: $APPDIR, $HELPER, $SUDOERS, $DESKTOP, $ICON"
echo "Start from the menu (\"Cleaner\" / \"Czyściciel\" / \"クリーナー\") or: python3 $APPDIR/mint-cleaner.py"
