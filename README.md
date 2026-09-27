# Stremio Flatpak + Host MPV/VLC

Flatpak ile kurulu Stremio'nun, sistemde kurulu olan **MPV** (ve **VLC**)
ile video acabilmesini saglayan yama.

## Sorun

Stremio Flatpak, harici oynaticilari `server.js` icindeki sabit yollarla
(`fs.existsSync("/usr/bin/mpv")`) tespit eder. Bu yollar sandbox icinde
yoktur ve `/usr` Flatpak'a rezerve oldugu icin paylasilamaz. Ayrica
`flatpak-spawn --host` icin session bus izni (`org.freedesktop.Flatpak`)
varsayilan olarak kapali gelir. Sonuc: "Play in MPV" secenegi hic cikmaz.

## Cozum

1. **Sandbox-host koprusu** (bir kez yapilir, guncellemelerde silinmez):

   ```bash
   flatpak override --user --talk-name=org.freedesktop.Flatpak com.stremio.Stremio
   ```

2. **`server.js` yamasi** (`apply.py` ile uygulanir):
   - Tespit: sandbox'ta bulunamayan yol, host'ta
     `flatpak-spawn --host test -x <yol>` ile kontrol edilir.
   - Calistirma: komut `flatpak-spawn --host /usr/bin/mpv --start=... --no-terminal "url"`
     seklinde kurulur (arguman sirasi bozulmaz).
   - Altyazi: sandbox `/tmp`'si host'a gorunmedigi (ozel tmpfs) icin
     altyazi dosyasi `~/.cache` altina yazilir.

## Kurulum

```bash
flatpak override --user --talk-name=org.freedesktop.Flatpak com.stremio.Stremio
python3 apply.py
flatpak kill com.stremio.Stremio   # yeniden baslat
flatpak run com.stremio.Stremio
```

Dogrulama:

```bash
curl -s http://127.0.0.1:11470/casting
# [{"name":"VLC",...},{"name":"MPV",...}] gormelisin
```

## Kullanim

Yayin sirasinda oynaticidaki **`...` menusu -> Play in MPV**.
Kaldigin saniye `--start` ile aktarilir, harici altyazilar calisir.

## Altyazi davranisi (onemli)

Harici oynaticiya **yalnizca Stremio oynaticisinda o an SECILI olan
tek altyazi** gonderilir (`--sub-file` ile). Gonderim akisi:

1. Yayini ac, Stremio'nun altyazi menusunden **Turkce altyaziyi sec**
   (OpenSubtitles listesinden).
2. Sonra `... -> Play in MPV` de. Secili TR altyazi MPV'de otomatik acilir.

Hicbir altyazi secilmezse MPV'ye harici altyazi gitmez; videoya gomulu
altyazilar (EN, FR, DE, ES, FI...) arasindan MPV kendi secer.

Yama MPV'ye ek olarak `--slang=tr,en` parametresi verir, yani gomulu
altyazilar arasinda **once Turkce, yoksa Ingilizce** otomatik secilir.
Olculen davranis (mpv IPC ile dogrulandi):

| durum | secilen |
|---|---|
| secim yok, slang yok | gomulu EN |
| Stremio'da TR secili | harici TR dosyasi |
| slang=tr,en, harici yok | gomulu TR (yoksa EN) |
| slang=tr,en + harici TR | harici TR dosyasi (bozulmaz) |

Farkli dil tercihi istersen `apply.py` icindeki `--slang=tr,en`
degerini degistir (örn. `--slang=tr,de,en`).

Not: `Ayarlar -> Play in external player` menusunde Linux'ta yalnizca
"Disabled / M3U Playlist" gorunur, bu Stremio'nun tasarimidir; MPV her
yayinda `...` menusunden secilir.

## Flatpak guncellemesi sonrasi

Guncelleme `server.js`'i sifirlar, yamayi tekrar uygulayin:

```bash
python3 apply.py
flatpak kill com.stremio.Stremio
```

`apply.py --check` ile yamanin durup durmadigina bakabilirsiniz.
Geri almak icin: `python3 revert.py`

## Dosyalar

- `apply.py` — yamayi uygular (idempotent, once yedek alir, `node` varsa
  sozdizimi kontrolu yapar)
- `revert.py` — yedekten geri yukler
- `server.js.patch` — degisikligin ham unified diff kaydi (referans icin)
