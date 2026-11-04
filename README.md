# Clipperino

**A clipboard history manager for Fedora and GNOME, rebuilt from the ground up.**

Copy anything. Press **Super+Shift+V**. Pick it. It lands in the app you were using.

Clipperino keeps a history of the text and images you copy, lets you search and paste
them back with the keyboard, and includes an emoji and symbol picker. It runs
quietly in the background, starts with your session, and lives in the panel tray,
where its menu gives one-click access to your recent clips.

---

## The rebuild

Clipperino (called Clipped until 1.1) is a complete rewrite. The earlier app was written in C with GTK 3
and depended on X11: it grabbed the hotkey with `XGrabKey`, watched the
clipboard through an XWayland bridge, faked keystrokes with `XTest`, and used the
long-deprecated `GtkStatusIcon`. On a modern Fedora desktop (GNOME on Wayland)
that meant the shortcut only worked while an X11 window had focus, the tray
needed an extension to exist at all, and window placement was ignored.

The new app is written in **Rust** with **GTK 4** and **libadwaita**, and talks to
the desktop only through **GNOME's portals**. Nothing in it depends on X11, on a
shell extension, or on the app having focus.

| Concern | Before | Now |
|---|---|---|
| Language and toolkit | C, GTK 3 | Rust, GTK 4.22, libadwaita 1.9 |
| Clipboard monitoring | X11 selection events via XWayland | RemoteDesktop + Clipboard portals |
| Global shortcut | `XGrabKey` (silent on Wayland apps) | GlobalShortcuts portal, listed in GNOME Settings |
| Paste into the previous app | `XTest` fake keys | Portal keyboard injection, with focus handed back by GNOME |
| Start at login | System-wide `/etc/xdg/autostart` file | Background portal; toggle in Preferences or GNOME Settings › Apps |
| Tray icon | `GtkStatusIcon` (removed in GTK 4) | StatusNotifierItem, shown when the desktop has a tray |
| History storage | Text file written at exit, images lost | SQLite, written through on every change, images kept as PNG files |
| Settings | INI file; "max entries" was never saved | GSettings, every control applies immediately |
| Packaging | `.deb` only | RPM (spec, man page, AppStream metadata, D-Bus service) |

## Features

- **History** of text, file lists and images, persisted across restarts, grouped by day (Today, Yesterday, Last 7 Days, Earlier). Copied files paste back as files in Nautilus.
- **Images at a glance**: image clips are large preview cards; the **Images** filter shows them as a gallery; transparent images sit on a checkerboard; hover for a bigger view. Links, email addresses, code and colour codes get their own icons (colour codes show a swatch).
- **Filters**: All, Text, Images, Files (`Alt+1`–`Alt+4`).
- **Global shortcut** `Super+Shift+V` (`Super+V` is taken by GNOME's notification list). Change it in Settings › Keyboard.
- **Keyboard-first**: type to filter (search covers the full text of each clip), `↑`/`↓` to move, `Enter` to paste, `Ctrl+1`–`Ctrl+9` for the first nine, `Delete` to remove (with Undo), `Ctrl+P` to pin, `Ctrl+D` for details, `Escape` to close, `Ctrl+?` for the full list.
- **Paste on select**: the item is pasted straight into the app you came from. Turn it off in Preferences to copy-and-close instead.
- **Pin** favourites so they survive trimming; **Undo** after deleting; **Clear History** asks first.
- **Details view** for the full text or full-size image, with Copy and Paste.
- **Emoji picker** using GNOME's own emoji database, with localized names and keywords in 24 languages, category chips and a Recent chip.
- **Symbol picker**: math, arrows, currency, punctuation, keyboard, geometric, Greek and more.
- **Adaptive layout**: tabs at the bottom on a narrow window; list plus a live preview pane when the window is wider than 700 px.
- **Runs in the background** and **starts at login** (Preferences › Run in Background).
- **Quick access from the panel**: the status icon opens a compact menu of your eight most recent clips, pinned ones first, with square thumbnails for images. One click pastes into the app you're using, without opening the window. Below the clips: Open Clipperino, Pause Recording, Preferences, Quit. Middle-click opens the full window. On GNOME this needs the AppIndicator extension; Preferences says so when no tray exists.
- **Privacy**: entries flagged by password managers are skipped, clipboard content is never logged, and the history file is private to your user. **Pause Recording** (main menu, panel menu or Preferences) stops saving copies until you resume, and unpinned items can be deleted automatically after a day, a week, 30 or 90 days.
- Follows the system light/dark style and accent colour.

## Design

The visual language follows Apple's Human Interface Guidelines in spirit, built with
GNOME's own components: history rows are rounded cards with a hairline ring and a
soft shadow; the selected card is tinted with the accent colour instead of filled;
the search field is a pill; secondary controls appear only on hover, focus or
selection; emoji and symbol cells have rounded hover states; and every state
change eases over 120–150 ms. All colours are Adwaita semantic tokens, so light
mode, dark mode and the accent colour follow the system automatically.

Measured on a 120 Hz display: scrolling 1,000 rows renders at one frame per
display refresh, with a single dropped frame in three seconds. Idle memory for
the running service is about 53 MB. See `docs/PERF.md`.

## Install (Fedora)

Add the Clipperino repository once, then install. `sudo dnf upgrade` keeps
it up to date from then on:

```bash
sudo dnf config-manager addrepo --from-repofile=https://djshiye.github.io/clipperino/clipperino.repo
sudo dnf install clipperino
```

One package works on every current Fedora release. The repository is
published to GitHub Pages from each release by `.github/workflows/repo.yml`
and keeps the last three releases. Packages and repository metadata are
signed; dnf asks once to trust the key
([RPM-GPG-KEY-djshiye](https://djshiye.github.io/clipperino/RPM-GPG-KEY-djshiye)).
The package installs its own `/etc/yum.repos.d/clipperino.repo` and the key,
so the repository stays configured. You can
also download the RPM from the [latest release](https://github.com/djshiye/Clipperino/releases/latest)
and install it with `sudo dnf install ./clipperino-*.rpm`, but then it won't
receive updates.

## Install (Flatpak, any distribution)

Each release from 1.3.2 on carries a Flatpak bundle, which brings its own
GTK and libadwaita through the GNOME 50 runtime:

```bash
flatpak install --user ./clipperino-<version>.x86_64.flatpak
```

The Flatpak behaves like the native app. It keeps its own history and
settings in `~/.var/app/io.github.djshiye.Clipperino`, so it starts empty.
Install one or the other: both use the same app ID, so the one installed
last takes over the app grid and the login item.

### First run

Launch **Clipperino** from the app grid. GNOME asks two things, once:

1. **Remote desktop access.** This is how GNOME lets an app watch the clipboard
   in the background and paste for you. Click **Share**. Nothing leaves your
   computer; the permission is remembered.
2. **Bind the shortcut** `Super+Shift+V`. Accept it.

From then on Clipperino runs in the background, starts at login, and shows its
icon in the panel tray.

### Requirements

Fedora 44 or newer with GNOME (GTK 4.22, libadwaita 1.9, `xdg-desktop-portal-gnome`).
Other desktops need a portal backend that implements RemoteDesktop with
Clipboard, and GlobalShortcuts (KDE Plasma 6.4 or newer should, untested).

## Build from source

```bash
sudo dnf install rust cargo meson gtk4-devel libadwaita-devel sqlite-devel \
     blueprint-compiler desktop-file-utils appstream gettext
meson setup builddir
meson compile -C builddir
sudo meson install -C builddir
```

For development, `cargo run` works without installing, as long as a desktop file
for `io.github.djshiye.Clipperino` exists in `~/.local/share/applications`, because
the portals identify apps by their desktop entry.

### Build the Flatpak

```bash
flatpak-builder --user --install --force-clean build-flatpak \
    build-aux/flatpak/io.github.djshiye.Clipperino.yml
```

After changing `Cargo.lock`, regenerate `build-aux/flatpak/cargo-sources.json`
with [flatpak-cargo-generator](https://github.com/flatpak/flatpak-builder-tools/tree/master/cargo),
since Flatpak builds are offline.

### Build the RPM

```bash
cargo vendor vendor && tar -cJf clipperino-1.4.0-vendor.tar.xz vendor
# source tarball named clipperino-1.4.0.tar.gz with a clipperino-1.4.0/ prefix
rpmdev-setuptree && cp clipperino-1.4.0*.tar.* ~/rpmbuild/SOURCES/
rpmbuild -ba build-aux/clipperino.spec
```

CI (`.github/workflows/ci.yml`) runs formatting, clippy and unit tests on
Fedora 44 for every push, with the Cargo build cached, and on Rawhide weekly.
Pushing a `v*` tag builds the RPM once on Fedora 44, the oldest supported
release (its `%check` runs the Meson validation tests), signs the RPM and the
source RPM (key in the `RPM_SIGNING_KEY` secret), publishes a GitHub release
with them and the source and vendor tarballs the spec expects, refreshes the
signed dnf repository on GitHub Pages and installs it from there in clean
Fedora 44 and 45 containers. The spec also needs the public key as
`RPM-GPG-KEY-djshiye` in `SOURCES` (CI exports it from the secret).

## Project layout

```
src/            Rust sources: application, window, model, storage, platform (portals, shortcut, tray), ui
data/           Blueprint UI files, stylesheet, icons, desktop entry, AppStream metainfo, GSettings schema, man page
build-aux/      RPM spec and the Cargo wrapper used by Meson
docs/           Rebuild plan, verified platform findings, performance notes
spikes/         Throwaway portal experiments that validated the approach
```

## Documentation

- `docs/FEDORA_REBUILD_PLAN.md`: architecture, design rules and the phased plan.
- `docs/FLATPAK.md`: Flatpak status, the test checklist and the Flathub submission steps.
- `docs/SPIKES.md`: what was verified on GNOME 50 and the platform quirks worth knowing.
- `docs/PERF.md`: measurements and how to reproduce them.
- `CHANGELOG.md`: release notes.

## License

MIT. See `LICENSE`.
