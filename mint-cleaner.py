#!/usr/bin/env python3
"""Mint Cleaner (Czyściciel / クリーナー) — GTK3 system cleaner for Linux Mint / Debian / Ubuntu.
Copyright (c) 2026 Sebastian Maliszewski — MIT License."""
import os, sys, glob, json, locale, shlex, subprocess, threading
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib, Gdk, Pango

NAME = "mint-cleaner"
HOME = os.path.expanduser("~")
HERE = os.path.dirname(os.path.abspath(__file__))
HELPER = f"/usr/local/sbin/{NAME}-helper"
LOCAL_HELPER = os.path.join(HERE, f"{NAME}-helper")
CHECK_HELPER = HELPER if os.path.exists(HELPER) else LOCAL_HELPER   # check-* needs no root
INSTALLER = os.path.join(HERE, "install.sh")
CONF_DIR = os.path.join(os.environ.get("XDG_CONFIG_HOME") or os.path.join(HOME, ".config"), NAME)
CONF = os.path.join(CONF_DIR, "config.json")
Q = shlex.quote
LANGS = ("pl", "en", "ja")

# ---------------------------------------------------------------- translations
S = {
 "app_title":   {"pl": "Czyściciel", "en": "Cleaner", "ja": "クリーナー"},
 "subtitle":    {"pl": "sprzątanie systemu", "en": "system cleanup", "ja": "システムのクリーンアップ"},
 "preview":     {"pl": "Podgląd", "en": "Preview", "ja": "プレビュー"},
 "run_sel":     {"pl": "Wyczyść zaznaczone", "en": "Clean selected", "ja": "選択項目を削除"},
 "prev_sel":    {"pl": "Podgląd zaznaczonych", "en": "Preview selected", "ja": "選択項目をプレビュー"},
 "run_one":     {"pl": "Uruchom tylko to zadanie", "en": "Run only this task", "ja": "このタスクだけ実行"},
 "terminal":    {"pl": "Wyjście terminala", "en": "Terminal output", "ja": "ターミナル出力"},
 "clear":       {"pl": "Wyczyść", "en": "Clear", "ja": "クリア"},
 "disk":        {"pl": "<b>/</b>  wolne: <b>{a}</b> z {s}  (zajęte {p})",
                 "en": "<b>/</b>  free: <b>{a}</b> of {s}  ({p} used)",
                 "ja": "<b>/</b>  空き: <b>{a}</b> / {s}（使用率 {p}）"},
 "freed":       {"pl": "Zwolniono: {x}", "en": "Freed: {x}", "ja": "解放: {x}"},
 "kprot":       {"pl": "Ochrona jądra:", "en": "Kernel protection:", "ja": "カーネル保護:"},
 "k_strict":    {"pl": "Chroń wszystkie jądra", "en": "Protect all kernels", "ja": "すべてのカーネルを保護"},
 "k_standard":  {"pl": "Standard", "en": "Standard", "ja": "標準"},
 "k_strict_tip":{"pl": "Autoremove zostanie odrzucony, jeśli na liście jest jakikolwiek pakiet linux-image/modules/headers.",
                 "en": "Autoremove is refused if the list contains any linux-image/modules/headers package.",
                 "ja": "削除リストに linux-image/modules/headers パッケージが含まれている場合、autoremove を中止します。"},
 "k_standard_tip":{"pl": "Pozwala apt usunąć stare jądra, ale nigdy aktualnie działającego ({k}).",
                 "en": "Lets apt remove old kernels, but never the running one ({k}).",
                 "ja": "古いカーネルの削除は許可しますが、実行中のカーネル（{k}）は削除しません。"},
 "banner":      {"pl": "<b>Pomocnik root nie jest zainstalowany</b> — zadania systemowe (APT, rc, Flatpak systemowy, dziennik) nie zadziałają; podgląd działa.\nZainstaluj w terminalu:  <tt>{cmd}</tt>  i uruchom aplikację ponownie.",
                 "en": "<b>Root helper is not installed</b> — system tasks (APT, rc, system Flatpak, journal) will not work; preview still works.\nInstall from a terminal:  <tt>{cmd}</tt>  and restart the app.",
                 "ja": "<b>root ヘルパーがインストールされていません</b>。システム関連のタスク（APT・rc・システム Flatpak・ジャーナル）は実行できません（プレビューは利用できます）。\nターミナルで <tt>{cmd}</tt> を実行してから、アプリを再起動してください。"},
 "h_preview":   {"pl": "PODGLĄD (nic nie jest usuwane)", "en": "PREVIEW (nothing is deleted)", "ja": "プレビュー（何も削除しません）"},
 "h_clean":     {"pl": "CZYSZCZENIE", "en": "CLEANING", "ja": "クリーンアップ"},
 "h_after":     {"pl": "df -h / po:", "en": "df -h / after:", "ja": "df -h /（実行後）:"},
 "session_freed":{"pl": "Zwolniono w tej sesji: {x}", "en": "Freed in this run: {x}", "ja": "今回解放した容量: {x}"},
 "done":        {"pl": "✓ gotowe", "en": "✓ done", "ja": "✓ 完了"},
 "exit":        {"pl": "✗ kod wyjścia {rc}", "en": "✗ exit code {rc}", "ja": "✗ 終了コード {rc}"},
 "error":       {"pl": "błąd: {e}", "en": "error: {e}", "ja": "エラー: {e}"},
 "noperm":      {"pl": "✗ brak uprawnień — zainstaluj pomocnika: {cmd}", "en": "✗ not permitted — install the helper: {cmd}", "ja": "✗ 権限がありません。ヘルパーをインストールしてください: {cmd}"},
 "empty":       {"pl": "pusto — nic do usunięcia", "en": "empty — nothing to delete", "ja": "空です。削除するものはありません"},
 "ff_running":  {"pl": "UWAGA: Firefox działa — czyszczenie zostanie pominięte.", "en": "NOTE: Firefox is running — cleaning will be skipped.", "ja": "注意: Firefox が起動中のため、削除はスキップされます。"},
 "ff_skip":     {"pl": "Firefox jest uruchomiony — zamknij go i spróbuj ponownie. Pominięto.", "en": "Firefox is running — close it and try again. Skipped.", "ja": "Firefox が起動中です。終了してから再度お試しください。スキップしました。"},
 "ff_none":     {"pl": "Brak cache2.", "en": "No cache2 found.", "ja": "cache2 はありません。"},
 "ff_ok":       {"pl": "Cache Firefoksa usunięty (ciasteczka zostają).", "en": "Firefox cache deleted (cookies kept).", "ja": "Firefox のキャッシュを削除しました（Cookie は残ります）。"},
 "th_ok":       {"pl": "Miniatury usunięte.", "en": "Thumbnails deleted.", "ja": "サムネイルを削除しました。"},
 "th_none":     {"pl": "Brak miniatur.", "en": "No thumbnails.", "ja": "サムネイルはありません。"},
 "tr_ok":       {"pl": "Kosz opróżniony.", "en": "Trash emptied.", "ja": "ゴミ箱を空にしました。"},
 "tr_none":     {"pl": "Kosz jest pusty.", "en": "Trash is empty.", "ja": "ゴミ箱は空です。"},
 "info_only":   {"pl": "(tylko informacja — nic nie jest usuwane)", "en": "(information only — nothing is deleted)", "ja": "（情報表示のみ。何も削除しません）"},
 "debs":        {"pl": "plików .deb:", "en": ".deb files:", "ja": ".deb ファイル数:"},
 "no_debs":     {"pl": "brak paczek .deb w cache — nic do usunięcia", "en": "no .deb packages in cache — nothing to delete", "ja": "キャッシュに .deb パッケージはありません"},
 "no_rc":       {"pl": "brak resztek", "en": "no leftovers", "ja": "残留設定はありません"},
 "sys":         {"pl": "== system ==", "en": "== system ==", "ja": "== システム =="},
 "user":        {"pl": "== użytkownik ==", "en": "== user ==", "ja": "== ユーザー =="},
 "lang_tip":    {"pl": "Język interfejsu", "en": "Interface language", "ja": "表示言語"},
}
TASK_TXT = {
 "apt-clean":     ({"pl": "Cache pakietów APT", "en": "APT package cache", "ja": "APT パッケージキャッシュ"},
                   {"pl": "apt clean — usuwa pobrane paczki .deb z /var/cache/apt.", "en": "apt clean — removes downloaded .deb files from /var/cache/apt.", "ja": "apt clean — /var/cache/apt にダウンロード済みの .deb ファイルを削除します。"}),
 "apt-autoclean": ({"pl": "Stare paczki APT", "en": "Outdated APT packages", "ja": "古い APT パッケージ"},
                   {"pl": "apt autoclean — usuwa tylko nieaktualne paczki z cache.", "en": "apt autoclean — removes only outdated packages from the cache.", "ja": "apt autoclean — キャッシュ内の古くなったパッケージだけを削除します。"}),
 "apt-autoremove":({"pl": "Osierocone zależności", "en": "Orphaned dependencies", "ja": "不要になった依存パッケージ"},
                   {"pl": "apt autoremove --purge z ochroną jądra (tryb wybierany powyżej).", "en": "apt autoremove --purge with kernel protection (mode selected above).", "ja": "カーネル保護付きの apt autoremove --purge（モードは上で選択）。"}),
 "rc-purge":      ({"pl": "Resztki konfiguracji (rc)", "en": "Leftover configs (rc)", "ja": "残留設定ファイル (rc)"},
                   {"pl": "dpkg --purge pakietów w stanie „rc” (tylko gdy lista niepusta).", "en": "dpkg --purge of packages in “rc” state (only if any).", "ja": "「rc」状態のパッケージを dpkg --purge で完全削除します（該当がある場合のみ）。"}),
 "flatpak":       ({"pl": "Nieużywane runtime'y Flatpak", "en": "Unused Flatpak runtimes", "ja": "未使用の Flatpak ランタイム"},
                   {"pl": "flatpak uninstall --unused -y (systemowe i użytkownika).", "en": "flatpak uninstall --unused -y (system and user).", "ja": "flatpak uninstall --unused -y（システムとユーザーの両方）。"}),
 "journal":       ({"pl": "Logi systemowe", "en": "System journal", "ja": "システムログ"},
                   {"pl": "journalctl --vacuum-time=2weeks — przycina dziennik do 2 tygodni.", "en": "journalctl --vacuum-time=2weeks — trims the journal to 2 weeks.", "ja": "journalctl --vacuum-time=2weeks — ジャーナルを直近 2 週間分に縮小します。"}),
 "thumbs":        ({"pl": "Miniatury obrazków", "en": "Image thumbnails", "ja": "画像のサムネイル"},
                   {"pl": "~/.cache/thumbnails/*", "en": "~/.cache/thumbnails/*", "ja": "~/.cache/thumbnails/*"}),
 "firefox":       ({"pl": "Cache Firefoksa", "en": "Firefox cache", "ja": "Firefox のキャッシュ"},
                   {"pl": "~/.cache/mozilla/firefox/*/cache2 — pomijane, gdy Firefox działa. Ciasteczka zostają.", "en": "~/.cache/mozilla/firefox/*/cache2 — skipped while Firefox runs. Cookies are kept.", "ja": "~/.cache/mozilla/firefox/*/cache2 — Firefox の起動中はスキップします。Cookie は残ります。"}),
 "trash":         ({"pl": "Kosz", "en": "Trash", "ja": "ゴミ箱"},
                   {"pl": "~/.local/share/Trash/{files,info}/*", "en": "~/.local/share/Trash/{files,info}/*", "ja": "~/.local/share/Trash/{files,info}/*"}),
 "topcache":      ({"pl": "15 największych w ~/.cache", "en": "15 largest in ~/.cache", "ja": "~/.cache の容量上位 15 件"},
                   {"pl": "Tylko informacja do ręcznej oceny — nic nie jest usuwane.", "en": "Information only, for manual review — nothing is deleted.", "ja": "手動確認用の情報表示のみです。何も削除しません。"}),
}

# ---------------------------------------------------------------- config
def system_lang():
    for v in ("LANGUAGE", "LC_ALL", "LC_MESSAGES", "LANG"):
        val = os.environ.get(v, "")
        if val:
            code = val.split(":")[0][:2].lower()
            return {"pl": "pl", "ja": "ja"}.get(code, "en")
    return "en"

def load_conf():
    c = {}
    try:
        with open(CONF, encoding="utf-8") as f: c = json.load(f)
    except Exception: pass
    if c.get("lang") not in LANGS: c["lang"] = system_lang()
    if c.get("kernel_mode") not in ("strict", "standard"): c["kernel_mode"] = "strict"
    env = os.environ.get("MINT_CLEANER_LANG", "").lower()[:2]
    if env in LANGS: c["lang"] = env            # dev/test override, not persisted unless changed in UI
    return c

def save_conf(c):
    try:
        os.makedirs(CONF_DIR, exist_ok=True)
        tmp = CONF + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f: json.dump(c, f, ensure_ascii=False, indent=2)
        os.replace(tmp, CONF)
    except Exception as e: print("config save failed:", e, file=sys.stderr)

CFG = load_conf()
def T(key, **kw):
    s = S[key][CFG["lang"]]
    return s.format(**kw) if kw else s

# ---------------------------------------------------------------- commands
def sh(cmd): return ["bash", "-c", cmd]
def SUDO(sub): return ["sudo", "-n", HELPER, sub]
def globs(pattern): return " ".join(Q(p) for p in glob.glob(os.path.expanduser(pattern)))
def ff_caches(): return glob.glob(os.path.join(HOME, ".cache/mozilla/firefox/*/cache2"))
def firefox_running():
    return subprocess.run(["pgrep", "-x", "firefox"], stdout=subprocess.DEVNULL).returncode == 0
def du_cmd(paths):
    return f"du -sch {paths} 2>/dev/null | tail -1" if paths.strip() else f"echo {Q(T('empty'))}"
def install_cmd(): return f"sudo {INSTALLER}" if os.path.exists(INSTALLER) else "sudo ./install.sh"

TRASH = "~/.local/share/Trash/files/* ~/.local/share/Trash/files/.[!.]* ~/.local/share/Trash/info/*"
def t_thumbs_run():
    p = globs("~/.cache/thumbnails/*")
    return sh(f"rm -rf -- {p} && echo {Q(T('th_ok'))}" if p else f"echo {Q(T('th_none'))}")
def t_ff_prev():
    p = " ".join(Q(x) for x in ff_caches())
    extra = f"echo {Q(T('ff_running'))}; " if firefox_running() else ""
    return sh(extra + (f"du -sh {p}" if p else f"echo {Q(T('ff_none'))}"))
def t_ff_run():
    if firefox_running(): return T("ff_skip")
    p = " ".join(Q(x) for x in ff_caches())
    return sh(f"rm -rf -- {p} && echo {Q(T('ff_ok'))}" if p else f"echo {Q(T('ff_none'))}")
def t_trash_run():
    p = globs(TRASH)
    return sh(f"rm -rf -- {p} && echo {Q(T('tr_ok'))}" if p else f"echo {Q(T('tr_none'))}")
def t_top():
    return sh(f"du -sh {Q(HOME)}/.cache/* {Q(HOME)}/.cache/.[!.]* 2>/dev/null | sort -h | tail -15; echo {Q(T('info_only'))}")
def t_flat_prev():
    return sh(f"echo {Q(T('sys'))}; echo n | flatpak uninstall --system --unused 2>&1; echo {Q(T('user'))}; echo n | flatpak uninstall --user --unused 2>&1; true")
def t_flat_run():
    return sh(f"echo {Q(T('sys'))}; sudo -n {HELPER} flatpak-system; s=$?; echo {Q(T('user'))}; flatpak uninstall --user --unused -y --noninteractive; exit $(( s | $? ))")

# (id, root?, preview()->cmd, run()->cmd | str(error))
TASKS = [
 ("apt-clean", True, lambda: sh(f"du -sh /var/cache/apt/archives 2>/dev/null; echo \"{T('debs')} $(ls /var/cache/apt/archives/*.deb 2>/dev/null | wc -l)\"; true"),
  lambda: SUDO("apt-clean")),
 ("apt-autoclean", True, lambda: sh(f"ls -la /var/cache/apt/archives/*.deb 2>/dev/null || echo {Q(T('no_debs'))}; true"),
  lambda: SUDO("apt-autoclean")),
 ("apt-autoremove", True, lambda: [CHECK_HELPER, f"apt-autoremove-check-{CFG['kernel_mode']}"],
  lambda: SUDO(f"apt-autoremove-{CFG['kernel_mode']}")),
 ("rc-purge", True, lambda: sh(f"l=$(dpkg -l | awk '/^rc/{{print $2}}'); [ -z \"$l\" ] && echo {Q(T('no_rc'))} || echo \"$l\""),
  lambda: SUDO("rc-purge")),
 ("flatpak", True, t_flat_prev, t_flat_run),
 ("journal", True, lambda: ["journalctl", "--disk-usage"], lambda: SUDO("journal-vacuum")),
 ("thumbs", False, lambda: sh(du_cmd(globs("~/.cache/thumbnails/*"))), t_thumbs_run),
 ("firefox", False, t_ff_prev, t_ff_run),
 ("trash", False, lambda: sh(du_cmd(globs(TRASH))), t_trash_run),
 ("topcache", False, t_top, t_top),
]
DEFAULT_OFF = {"topcache"}

CSS = b"""
.card { border-radius: 12px; padding: 10px 14px; border: 1px solid alpha(@theme_fg_color,0.12); background-color: alpha(@theme_fg_color,0.035); }
.card-title { font-weight: bold; }
.dim { opacity: 0.7; }
.disk { font-size: 11pt; }
.freed { color: #2ec27e; font-weight: bold; }
.banner { background-color: #e5a50a; color: #1e1e1e; border-radius: 10px; padding: 8px 12px; }
.term { font-family: monospace; font-size: 9.5pt; }
.term text { background-color: #1b1d23; color: #d8dee9; }
.pill { border-radius: 99px; padding: 2px 8px; font-size: 8pt; background-color: alpha(@theme_fg_color,0.1); }
"""

def df_root():
    out = subprocess.run(["df", "-B1", "--output=avail,size", "/"], capture_output=True, text=True).stdout.split("\n")[1].split()
    return int(out[0]), int(out[1])
def human(n):
    for u in ["B", "KiB", "MiB", "GiB", "TiB"]:
        if abs(n) < 1024: return f"{n:.1f} {u}"
        n /= 1024
    return f"{n:.1f} PiB"
def helper_ready():
    if not os.path.exists(HELPER): return False
    return subprocess.run(["sudo", "-n", "-l", HELPER, "apt-clean"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0

def segmented(options, active, on_change):
    """Linked toggle buttons acting as a segmented control. options: [(value, label)]"""
    box = Gtk.Box(); box.get_style_context().add_class("linked")
    group, buttons = None, {}
    for val, label in options:
        b = Gtk.RadioButton.new_with_label_from_widget(group, label); group = group or b
        b.set_mode(False); b.set_valign(Gtk.Align.CENTER); buttons[val] = b; box.add(b)
    buttons[active].set_active(True)
    for val, b in buttons.items():
        b.connect("toggled", lambda w, v=val: w.get_active() and on_change(v))
    return box, buttons

class Win(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_default_size(1040, 740); self.set_icon_name(NAME)
        self.busy = False; self.start_free = df_root()[0]; self.krel = os.uname().release
        self.hb = Gtk.HeaderBar(show_close_button=True); self.set_titlebar(self.hb)
        self.preview = Gtk.Switch(active=True, valign=Gtk.Align.CENTER)
        pb = Gtk.Box(spacing=6); self.prev_lbl = Gtk.Label(); pb.add(self.prev_lbl); pb.add(self.preview); self.hb.pack_start(pb)
        self.run_btn = Gtk.Button(); self.run_btn.get_style_context().add_class("suggested-action")
        self.run_btn.connect("clicked", self.on_run_selected); self.hb.pack_end(self.run_btn)
        self.lang_box, self.lang_btns = segmented([("pl", "PL"), ("en", "EN"), ("ja", "JP")], CFG["lang"], self.set_lang)
        self.hb.pack_end(self.lang_box)
        self.spinner = Gtk.Spinner(); self.hb.pack_end(self.spinner)
        self.preview.connect("notify::active", self.on_mode)

        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10, margin=14); self.add(root)
        top = Gtk.Box(spacing=12)
        self.disk_lbl = Gtk.Label(xalign=0); self.disk_lbl.get_style_context().add_class("disk")
        self.freed_lbl = Gtk.Label(xalign=1); self.freed_lbl.get_style_context().add_class("freed")
        self.bar = Gtk.LevelBar(hexpand=True, valign=Gtk.Align.CENTER)
        top.pack_start(self.disk_lbl, False, False, 0); top.pack_start(self.bar, True, True, 0); top.pack_end(self.freed_lbl, False, False, 0)
        root.add(top)

        krow = Gtk.Box(spacing=8); self.k_lbl = Gtk.Label(xalign=0); self.k_lbl.get_style_context().add_class("card-title")
        self.k_box, self.k_btns = segmented([("strict", ""), ("standard", "")], CFG["kernel_mode"], self.set_kmode)
        self.k_hint = Gtk.Label(xalign=0, wrap=True); self.k_hint.get_style_context().add_class("dim")
        krow.pack_start(self.k_lbl, False, False, 0); krow.pack_start(self.k_box, False, False, 0); krow.pack_start(self.k_hint, True, True, 0)
        root.add(krow)

        self.banner = None
        if not helper_ready():
            self.banner = Gtk.Label(xalign=0, wrap=True, selectable=True)
            self.banner.get_style_context().add_class("banner"); root.add(self.banner)

        paned = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL, wide_handle=True, vexpand=True); root.pack_start(paned, True, True, 0)
        sc = Gtk.ScrolledWindow(hscrollbar_policy=Gtk.PolicyType.NEVER); sc.set_size_request(480, -1)
        lst = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8, margin_end=8); sc.add(lst); paned.pack1(sc, False, False)
        self.checks, self.card_lbls = {}, {}
        for tid, needs_root, _, _ in TASKS:
            card = Gtk.Box(spacing=10); card.get_style_context().add_class("card")
            cb = Gtk.CheckButton(active=tid not in DEFAULT_OFF, valign=Gtk.Align.CENTER); self.checks[tid] = cb
            txt = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
            tl = Gtk.Box(spacing=6); t = Gtk.Label(xalign=0); t.get_style_context().add_class("card-title"); tl.add(t)
            if needs_root:
                p = Gtk.Label(label="root"); p.get_style_context().add_class("pill"); tl.add(p)
            d = Gtk.Label(xalign=0, wrap=True, max_width_chars=46); d.get_style_context().add_class("dim")
            txt.add(tl); txt.add(d)
            btn = Gtk.Button.new_from_icon_name("media-playback-start-symbolic", Gtk.IconSize.BUTTON)
            btn.set_valign(Gtk.Align.CENTER); btn.connect("clicked", self.on_run_one, tid)
            card.pack_start(cb, False, False, 0); card.pack_start(txt, True, True, 0); card.pack_end(btn, False, False, 0)
            lst.add(card); self.card_lbls[tid] = (t, d, btn)

        right = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        rh = Gtk.Box(spacing=6); self.term_lbl = Gtk.Label(xalign=0); self.term_lbl.get_style_context().add_class("card-title")
        self.clr = Gtk.Button(); self.clr.connect("clicked", lambda *_: self.buf.set_text(""))
        rh.pack_start(self.term_lbl, True, True, 0); rh.pack_end(self.clr, False, False, 0); right.add(rh)
        tsc = Gtk.ScrolledWindow(vexpand=True)
        self.tv = Gtk.TextView(editable=False, cursor_visible=False, monospace=True, wrap_mode=Gtk.WrapMode.WORD_CHAR,
                               left_margin=10, right_margin=10, top_margin=8, bottom_margin=8)
        self.tv.get_style_context().add_class("term"); self.buf = self.tv.get_buffer()
        self.tag_cmd = self.buf.create_tag(foreground="#7fb4ff", weight=Pango.Weight.BOLD)
        self.tag_err = self.buf.create_tag(foreground="#ff7b72"); self.tag_ok = self.buf.create_tag(foreground="#7ee787")
        tsc.add(self.tv); right.pack_start(tsc, True, True, 0); paned.pack2(right, True, False)
        self.retranslate(); self.show_all()

    # ---- i18n / settings
    def retranslate(self):
        self.set_title(T("app_title")); self.hb.set_title(T("app_title")); self.hb.set_subtitle(T("subtitle"))
        self.prev_lbl.set_text(T("preview")); self.lang_box.set_tooltip_text(T("lang_tip"))
        self.k_lbl.set_text(T("kprot"))
        self.k_btns["strict"].set_label(T("k_strict")); self.k_btns["standard"].set_label(T("k_standard"))
        self.k_hint.set_text(T("k_strict_tip") if CFG["kernel_mode"] == "strict" else T("k_standard_tip", k=self.krel))
        if self.banner: self.banner.set_markup(T("banner", cmd=GLib.markup_escape_text(install_cmd())))
        for tid, (t, d, btn) in self.card_lbls.items():
            t.set_text(TASK_TXT[tid][0][CFG["lang"]]); d.set_text(TASK_TXT[tid][1][CFG["lang"]]); btn.set_tooltip_text(T("run_one"))
        self.term_lbl.set_text(T("terminal")); self.clr.set_label(T("clear"))
        self.on_mode(); self.refresh_disk()

    def set_lang(self, lang):
        CFG["lang"] = lang; save_conf({k: CFG[k] for k in ("lang", "kernel_mode")}); self.retranslate()
    def set_kmode(self, mode):
        CFG["kernel_mode"] = mode; save_conf({k: CFG[k] for k in ("lang", "kernel_mode")}); self.retranslate()

    def on_mode(self, *_):
        self.run_btn.set_label(T("prev_sel") if self.preview.get_active() else T("run_sel"))
        ctx = self.run_btn.get_style_context()
        (ctx.remove_class if self.preview.get_active() else ctx.add_class)("destructive-action")

    def refresh_disk(self):
        out = subprocess.run(["df", "-h", "/"], capture_output=True, text=True).stdout.split("\n")[1].split()
        avail, size = df_root()
        self.disk_lbl.set_markup(T("disk", a=out[3], s=out[1], p=out[4]))
        self.bar.set_value(1 - avail / size)
        freed = avail - self.start_free
        self.freed_lbl.set_text(T("freed", x=human(freed)) if freed > 0 else "")

    def log(self, text, tag=None):
        end = self.buf.get_end_iter()
        if tag: self.buf.insert_with_tags(end, text, tag)
        else: self.buf.insert(end, text)
        self.buf.place_cursor(self.buf.get_end_iter()); self.tv.scroll_mark_onscreen(self.buf.get_insert())
        return False

    def on_run_selected(self, *_): self.start([t for t in TASKS if self.checks[t[0]].get_active()])
    def on_run_one(self, _b, tid): self.start([t for t in TASKS if t[0] == tid])
    def start(self, tasks):
        if self.busy or not tasks: return
        self.busy = True; self.run_btn.set_sensitive(False); self.lang_box.set_sensitive(False); self.k_box.set_sensitive(False)
        self.spinner.start()
        threading.Thread(target=self.worker, args=(tasks, self.preview.get_active()), daemon=True).start()

    def worker(self, tasks, preview):
        L = lambda s, t=None: GLib.idle_add(self.log, s, t)
        lang = CFG["lang"]; before = df_root()[0]
        L(f"\n━━ {T('h_preview') if preview else T('h_clean')} ━━  df -h /:\n", self.tag_cmd)
        L(subprocess.run(["df", "-h", "/"], capture_output=True, text=True).stdout)
        for tid, needs_root, prev, run in tasks:
            L(f"\n▶ {TASK_TXT[tid][0][lang]}\n", self.tag_cmd)
            cmd = prev() if preview else run()
            if isinstance(cmd, str): L(cmd + "\n", self.tag_err); continue
            L("$ " + " ".join(Q(c) for c in cmd) + "\n", self.tag_cmd)
            try:
                with subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1,
                                      env={**os.environ, "LANGUAGE": {"ja": "ja:en", "pl": "pl:en"}.get(lang, "en")}) as p:
                    for line in p.stdout: L(line)
                    rc = p.wait()
            except Exception as e:
                L(T("error", e=e) + "\n", self.tag_err); continue
            if rc == 0: L(T("done") + "\n", self.tag_ok)
            elif needs_root and rc == 1 and not helper_ready(): L(T("noperm", cmd=install_cmd()) + "\n", self.tag_err)
            else: L(T("exit", rc=rc) + "\n", self.tag_err)
        after = df_root()[0]
        L(f"\n━━ {T('h_after')}\n", self.tag_cmd); L(subprocess.run(["df", "-h", "/"], capture_output=True, text=True).stdout)
        L(T("session_freed", x=human(max(0, after - before))) + "\n", self.tag_ok)
        GLib.idle_add(self.done)

    def done(self):
        self.busy = False
        for w in (self.run_btn, self.lang_box, self.k_box): w.set_sensitive(True)
        self.spinner.stop(); self.refresh_disk(); return False

def desktop_theme():
    for cmd in (["xfconf-query", "-c", "xsettings", "-p", "/Net/ThemeName"],
                ["gsettings", "get", "org.cinnamon.desktop.interface", "gtk-theme"],
                ["gsettings", "get", "org.gnome.desktop.interface", "gtk-theme"]):
        try:
            out = subprocess.run(cmd, capture_output=True, text=True, timeout=2).stdout.strip().strip("'")
            if out: return out
        except Exception: pass
    return ""

def apply_dark(settings, *_):
    name = (settings.get_property("gtk-theme-name") or desktop_theme()).lower()
    settings.set_property("gtk-application-prefer-dark-theme", "dark" in name)

def dev_selftest(win):
    """MINT_CLEANER_SELFTEST=1: cycle languages live, optional self-screenshot, then quit."""
    shot = os.environ.get("MINT_CLEANER_SCREENSHOT")
    seq = [l for l in LANGS if l != CFG["lang"]] + [CFG["lang"]]
    for l in seq:                        # live-switch without saving config
        CFG["lang"] = l; win.retranslate()
    win.start([t for t in TASKS if t[0] in ("apt-autoremove", "thumbs", "topcache")])
    def finish():
        if win.busy: return True
        if shot:
            gw = win.get_window(); w, h = gw.get_width(), gw.get_height()
            pb = Gdk.pixbuf_get_from_window(gw, 0, 0, w, h)
            if pb: pb.savev(shot, "png", [], []); print("screenshot:", shot, w, h)
        print("SELFTEST OK lang=" + CFG["lang"], "title=" + win.get_title())
        win.get_application().quit(); return False
    GLib.timeout_add(1500, finish)
    return False

class App(Gtk.Application):
    def __init__(self): super().__init__(application_id="io.github.mintcleaner.MintCleaner")
    def do_activate(self):
        if self.get_windows(): self.get_windows()[0].present(); return
        s = Gtk.Settings.get_default(); apply_dark(s); s.connect("notify::gtk-theme-name", apply_dark)
        prov = Gtk.CssProvider(); prov.load_from_data(CSS)
        Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), prov, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        w = Win(self)
        if os.environ.get("MINT_CLEANER_SELFTEST"): GLib.timeout_add(800, dev_selftest, w)
    def do_startup(self): Gtk.Application.do_startup(self)

if __name__ == "__main__":
    sys.exit(App().run([sys.argv[0]]))
