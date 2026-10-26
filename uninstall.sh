#!/bin/bash
# Mint Cleaner uninstaller.  Usage:  sudo ./uninstall.sh [--purge-config]
set -euo pipefail
NAME=mint-cleaner
[ "$(id -u)" -eq 0 ] || { echo "Run with sudo:  sudo $0" >&2; exit 1; }
for p in /etc/sudoers.d/$NAME /usr/local/sbin/$NAME-helper /usr/share/applications/$NAME.desktop \
         /usr/share/icons/hicolor/scalable/apps/$NAME.svg /opt/$NAME/mint-cleaner.py /opt/$NAME/LICENSE; do
  if [ -e "$p" ]; then rm -f -- "$p" && echo "removed $p"; fi
done
rm -rf -- /opt/$NAME/__pycache__
if rmdir /opt/$NAME 2>/dev/null; then echo "removed /opt/$NAME"; fi
gtk-update-icon-cache -q -t /usr/share/icons/hicolor 2>/dev/null || true
update-desktop-database -q /usr/share/applications 2>/dev/null || true
if [ "${1:-}" = --purge-config ] && [ -n "${SUDO_USER:-}" ] && [ "$SUDO_USER" != root ]; then
  H=$(getent passwd "$SUDO_USER" | cut -d: -f6)
  [ -n "$H" ] && [ -d "$H/.config/$NAME" ] && rm -rf -- "$H/.config/$NAME" && echo "removed $H/.config/$NAME"
fi
echo "Mint Cleaner uninstalled."
