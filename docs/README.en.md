# 🧹 Cleaner — user guide (English)

**Languages:** [Polski](README.pl.md) · **English** · [日本語](README.ja.md)

![Cleaner screenshot](screenshot-en.png)

## 1. What does Cleaner do? 🤔

Your computer keeps lots of old stuff it does not need anymore — like toys you stopped playing with.
**Cleaner** finds that stuff and tidies it up, so you get free space back. It can clean:

- 📦 old downloaded update files (APT cache, outdated packages),
- 🧩 helper packages nobody uses anymore (autoremove — your kernels are protected!),
- 🗒️ leftover settings of removed programs (“rc” packages),
- 📦 unused Flatpak pieces,
- 📜 old system diary entries (logs older than 2 weeks),
- 🖼️ small picture previews (thumbnails),
- 🦊 Firefox cache (your logins/cookies stay!),
- 🗑️ the Trash.

It also shows the 15 biggest things in `~/.cache` (just to look, it deletes nothing there).

## 2. What do you need? 🧰

- A computer with **Linux Mint 22**, **Ubuntu 24.04**, or another **Debian‑based** Linux.
- Internet (to download things).
- Your own password (the one you use to log in).

## 3. Open the terminal 🖥️

The terminal is a window where you type commands.

1. Press **Ctrl + Alt + T** together.
2. A window with a blinking cursor appears. 🎉

Tip: to paste into the terminal use **Ctrl + Shift + V** (not just Ctrl + V).

## 4. What is `sudo`? 🔑

Some jobs are “grown‑up jobs” — only the boss of the computer (called **root**) may do them.
`sudo` means: *“Please, do this as the boss.”*

- The computer then asks for **your password**.
- ⚠️ When you type it, **nothing shows up** — no dots, no stars. That is normal! Just type it and press **Enter**.

## 5. Install the things Cleaner needs 🧱

Copy this line, paste it in the terminal, press **Enter**:

```bash
sudo apt update && sudo apt install -y python3 python3-gi gir1.2-gtk-3.0 flatpak
```

- `python3` — the language Cleaner is written in.
- `python3-gi` + `gir1.2-gtk-3.0` — make the windows and buttons.
- `flatpak` — optional, only needed to clean Flatpak apps.

Want the Japanese screen to look right? Add Japanese letters (fonts):

```bash
sudo apt install -y fonts-noto-cjk
```

(The installer also checks Python + GTK itself and installs them if missing.)

## 6. Download Cleaner ⬇️

**Way A — with git** (needs `sudo apt install -y git`):

```bash
cd ~
git clone https://github.com/SebMaliszewski/linux-cleaner.git
```


**Way B — ZIP file:**

1. On the project page click **Code → Download ZIP**.
2. Open your **Downloads** folder, right‑click the ZIP, choose **Extract here**.
3. Rename the folder to `linux-cleaner` (for example from `linux-cleaner-main`) and move it to your home folder.

## 7. Install Cleaner 🛠️

```bash
cd ~/linux-cleaner && sudo ./install.sh
```

Type your password (nothing shows — normal 🙂) and press Enter. At the end you see **Done.**

⚠️ Run it with `sudo` from **your own** account — not as root, not with `sudo su`. The installer remembers *you* as the person allowed to use the helper.

### What is the “root helper”? 🤖

Cleaner itself is a normal app with normal powers. For the grown‑up jobs (APT, system Flatpak, logs) it calls a tiny helper program that may act as the boss — but it knows **only 7 exact jobs** and nothing else. Like a robot with only 7 buttons.

### What does `install.sh` put where? 📂

| What | Where |
|---|---|
| the app | `/opt/mint-cleaner/mint-cleaner.py` |
| the root helper | `/usr/local/sbin/mint-cleaner-helper` |
| permission rule | `/etc/sudoers.d/mint-cleaner` |
| menu entry | `/usr/share/applications/mint-cleaner.desktop` |
| icon | `/usr/share/icons/hicolor/scalable/apps/mint-cleaner.svg` |

The permission rule lets **only you** run **only these 7 exact commands** without a password:
`apt-clean`, `apt-autoclean`, `apt-autoremove-strict`, `apt-autoremove-standard`, `rc-purge`, `flatpak-system`, `journal-vacuum`.

### Why is it safe? 🛡️

- 🔒 **No password is saved anywhere.**
- Only 7 fixed commands, no extra words allowed, no wildcards.
- The app and helper belong to root, so other programs cannot secretly change them.
- The rule file is checked with `visudo` before it is used.

## 8. How to use it ▶️

1. Open the menu and start **Cleaner** (or type `python3 /opt/mint-cleaner/mint-cleaner.py`).
2. Tick ✅ the things you want to clean. The ▶ button on a card runs only that one.
3. **Preview** switch is **ON** at the start → 👀 Cleaner only *shows* what it would delete. **Nothing is deleted.**
4. Happy? Turn **Preview OFF** → the button becomes **red** 🔴. Click it to really clean.
5. Watch the terminal box: at the end you see how much space you got back. 🎉

**Language:** click **PL | EN | JP** at the top. It changes right away.

**Kernel protection** (the kernel is the heart of Linux ❤️):

- **Protect all kernels** (default) — if cleaning would remove *any* kernel, Cleaner stops and removes nothing. Safest.
- **Standard** — old kernels may be removed, but the kernel you are using **right now** is never removed.

## 9. Update 🔄

```bash
cd ~/linux-cleaner && git pull && sudo ./install.sh
```

(ZIP users: download the new ZIP, extract it, then run `sudo ./install.sh` in the new folder.)

## 10. Uninstall 👋

```bash
cd ~/linux-cleaner && sudo ./uninstall.sh
```

Also delete your settings (`~/.config/mint-cleaner`):

```bash
cd ~/linux-cleaner && sudo ./uninstall.sh --purge-config
```

## 11. Something went wrong? 🩹

- 🟨 **Yellow bar “Root helper is not installed”** → the helper is missing. Run `cd ~/linux-cleaner && sudo ./install.sh` and start Cleaner again. (Preview still works.)
- 🦊 **“Firefox is running … Skipped.”** → close Firefox completely and try again.
- ⛔ **“Permission denied”** when starting `./install.sh` → you are not in the right folder or forgot `sudo`. Try `cd ~/linux-cleaner && sudo bash ./install.sh`.
- ✗ **“not permitted — install the helper”** → run the installer again from your own account.
- **“Refusing: run via sudo from the user account…”** → you ran it as root. Log in as yourself and use `sudo ./install.sh`.
- **“BLOCKED … kernel”** → kernel protection did its job, nothing was removed. That’s good! 👍
- **Japanese shows as boxes □□□** → `sudo apt install -y fonts-noto-cjk`, then restart Cleaner.
- **`No module named 'gi'`** → run the command from step 5 again.

---
MIT License © 2026 Sebastian Maliszewski
