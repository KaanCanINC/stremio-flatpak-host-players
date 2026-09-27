#!/usr/bin/env python3
"""Stremio Flatpak icindeki server.js'e host MPV/VLC yamasini uygular.

Yama ne yapar?
  1. Harici oynatici tespiti: sandbox'ta bulunamayan /usr/bin/mpv, /usr/bin/vlc
     gibi yollar host'ta `flatpak-spawn --host test -x` ile kontrol edilir.
  2. Baslatma: oynatici komutunun basina `flatpak-spawn --host ` eklenir.
  3. Altyazi: sandbox /tmp'si host'a gorunmedigi icin altyazi dosyasi
     ~/.cache altina yazilir.

Kullanim:
    python3 apply.py           # yamayi uygula (idempotent)
    python3 apply.py --check   # sadece yamali mi diye bak

Gereksinim: Stremio flatpak olarak kurulu olmali.
Dogrulama icin `node` kuruluysa sozdizimi kontrolu yapilir (opsiyonel).
"""

import shutil
import subprocess
import sys

APP_ID = "com.stremio.Stremio"

HELPER = """        var stremioHostPlayerPrefix = function(p) {
            var q = p.replace(/"/gi, "");
            if (fs.existsSync(q)) return "";
            try {
                return child.execSync('/usr/bin/flatpak-spawn --host test -x "' + q + '"', { stdio: "ignore" }), "/usr/bin/flatpak-spawn --host ";
            } catch (e) {
                return null;
            }
        };
"""

PATCHES = [
    (
        "tespit: host yollari da kabul et",
        """        devices.groups.external = [], Object.keys(players).forEach((function(el) {
            var player = players[el];
            player[process.platform] && player[process.platform].path.forEach((function(p) {
                fs.existsSync(p.replace(/"/gi, "")) && devices.groups.external.push((function(player, platform) {""",
        HELPER
        + """        devices.groups.external = [], Object.keys(players).forEach((function(el) {
            var player = players[el];
            player[process.platform] && player[process.platform].path.forEach((function(p) {
                null !== stremioHostPlayerPrefix(p) && devices.groups.external.push((function(player, platform) {""",
    ),
    (
        "calistirma: host yollari filtrele + spawn oneplani hazirla",
        """                                    var playerPaths = platformObj.path.filter((function(path) {
                                        return fs.existsSync(path.replace(/"/gi, ""));
                                    }));""",
        """                                    var playerPaths = platformObj.path.filter((function(path) {
                                        return null !== stremioHostPlayerPrefix(path);
                                    })), stremioSpawnPfx = playerPaths.length > 0 ? stremioHostPlayerPrefix(playerPaths[0]) : "";""",
    ),
    (
        "calistirma: komuta flatpak-spawn --host oneplani ekle",
        'fullCmd = playerPaths[0] + " " + timeCmd',
        'fullCmd = stremioSpawnPfx + playerPaths[0] + " " + timeCmd',
    ),
    (
        "altyazi: host'un gorebilecegi dizine yaz (~/.cache)",
        'subsFile = path.join(os.tmpdir(), "stremio-" + player + "-subtitles.srt")',
        'subsFile = path.join((function() { try { var d = path.join(os.homedir(), ".cache");'
        ' return fs.mkdirSync(d, { recursive: !0 }), d; } catch (e) { return os.tmpdir(); } })(),'
        ' "stremio-" + player + "-subtitles.srt")',
    ),
    (
        "mpv: gomulu altyazilarda TR -> EN otomatik tercih (--slang)",
        """            mpv: {
                title: "MPV",
                args: [ "--no-terminal" ],""",
        """            mpv: {
                title: "MPV",
                args: [ "--no-terminal", "--slang=tr,en" ],""",
    ),
]


def find_server_js() -> str:
    out = subprocess.run(
        ["flatpak", "info", "--show-location", APP_ID],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    return out + "/files/libexec/stremio/server.js"


def main() -> int:
    check_only = "--check" in sys.argv
    path = find_server_js()
    print(f"server.js: {path}")
    with open(path, encoding="utf-8") as f:
        src = f.read()

    already = "stremioHostPlayerPrefix" in src
    if check_only:
        print("YAMA UYGULANMIS" if already else "YAMA UYGULANMAMIS")
        return 0 if already else 1

    if already:
        print("Yama zaten uygulanmis, yapilacak bir sey yok.")
        return 0

    backup = path + ".stremio-host-players.bak"
    with open(backup, "w", encoding="utf-8") as f:
        f.write(src)
    print(f"Yedek alindi: {backup}")

    for name, old, new in PATCHES:
        count = src.count(old)
        if count != 1:
            print(f"HATA: '{name}' capasi {count} kez bulundu (1 bekleniyordu).")
            print("server.js surumu degismis olabilir, yama uygulanmadi.")
            return 1
        src = src.replace(old, new)
        print(f"OK: {name}")

    with open(path, "w", encoding="utf-8") as f:
        f.write(src)

    node = shutil.which("node")
    if node is not None:
        chk = subprocess.run([node, "--check", path])
        if chk.returncode != 0:
            print("HATA: node --check basarisiz, yedek geri yukleniyor.")
            with open(backup, encoding="utf-8") as f:
                orig = f.read()
            with open(path, "w", encoding="utf-8") as f:
                f.write(orig)
            return 1
        print("OK: node --check gecti.")

    print("\nTamam. Stremio'yu yeniden baslatin: flatpak kill com.stremio.Stremio")
    return 0


if __name__ == "__main__":
    sys.exit(main())
