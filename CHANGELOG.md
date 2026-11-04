# Changelog

## 1.4.0 (2026-11-04)

- **Signed packages**: the RPMs and the dnf repository metadata are signed,
  so dnf checks them (`gpgcheck=1`, `repo_gpgcheck=1`) and asks once to
  trust the key.
- **One package for every Fedora**: the repository moved to
  `https://djshiye.github.io/clipperino/rpm/`, without a Fedora version in
  the path. The package is built on Fedora 44 and works on 44, 45 and later.
- The package installs its own `/etc/yum.repos.d/clipperino.repo` and the
  signing key, so the repository stays configured. If you added the old
  repository, this update replaces its file; the old address keeps working.
- The package recommends `gnome-shell-extension-appindicator`, which GNOME
  Shell needs to show the status icon.

## 1.3.2 (2026-09-29)

- **Fix:** after GNOME ended the clipboard permission session, Clipperino
  could not reconnect: the automatic retry and the Grant Access button both
  failed until the app was restarted, and nothing was recorded meanwhile.
- **Flatpak**: a manifest in `build-aux/flatpak`, and tagged releases attach
  a `.flatpak` bundle built on the GNOME 50 runtime. The status icon works
  inside the sandbox.
- Screenshots in the app metadata, for software centres and Flathub.

## 1.3.1 (2026-09-29)

- The **status icon menu** is less crowded: it lists 8 clips instead of 10,
  labels are shorter, the Pinned and Recent headers are gone (pinned clips
  keep their pin icon and sit above a separator), and type icons are shown
  only for pins and images.
- **Image thumbnails** in the menu are cropped to a square, so a wide
  screenshot fills its icon instead of shrinking to a sliver. Image entries
  read "Image · 14:32".
- **Clear History…** is no longer in the status icon menu; it stays in
  Preferences.

## 1.3.0 (2026-09-29)

### Images

- **Filter chips** under the search field: All, Text, Images, Files
  (`Alt+1`–`Alt+4`). **Images** shows a gallery of large, uniform tiles with
  each image's size and the time it was copied; arrow keys move through it.
- In the full list, image clips are **media cards** with a wide preview
  instead of a small thumbnail, so rows line up and images are recognisable.
- The preview pane and details view load the **full-size image** instead of
  stretching the thumbnail, and small images are no longer upscaled.
- **Transparent images** sit on a checkerboard, so a dark logo stays visible
  in dark mode.
- **Hover** over an image to see it larger without opening Details.
- The status icon menu adds the time to image entries
  ("Image · 1920 × 1080 · 14:32"), so they can be told apart.

### Everything else

- History is grouped under **Today, Yesterday, Last 7 Days and Earlier**
  headers. Text rows show their time on hover; image cards show it below
  the picture.
- **Type icons**: links show a link icon and their domain, email addresses
  a mail icon, code a terminal icon, and colour codes such as `#3584e4` a
  swatch of the colour. The status icon menu uses the same icons.
- The window opens on the newest clip, scrolled to the top.

## 1.2.0 (2026-09-29)

### New

- **Pause recording** from the main menu, the status icon menu or
  Preferences. A banner in the window shows it is paused, with a Resume button.
- **Delete unpinned items automatically** after 1 day, 1 week, 30 days or
  90 days (Preferences › History; off by default). Checked at startup and hourly.
- Copied files paste as files in Nautilus (`x-special/gnome-copied-files` and
  `text/uri-list`), and still paste as their URIs in text fields.
- Search matches the whole text of a clip (up to its first 64 KB), not just
  the one-line preview.
- The status icon menu and Preferences show the shortcut actually bound in
  GNOME Settings, and follow changes to it.
- "5 min ago" labels stay current while the window is open.
- The same image copied from two apps is stored once: images are identified
  by their pixels, not by the PNG bytes each app encodes.

### Fixed

- Row menu actions (Paste, Copy, Pin, Details, Delete) could act on the
  wrong item after a clip was added or deleted while the window was open.
  They now name the item by its content hash. The Pin/Unpin label also
  follows the item when it is pinned with Ctrl+P.
- Pinning an item restored from a previous session did not update the
  status icon menu.
- The Show Status Icon switch in Preferences did nothing. Without a tray host,
  its subtitle now explains that GNOME needs the AppIndicator extension.
- When GNOME ended the clipboard permission session, recording stopped
  silently. Clipperino now reconnects, or shows the permission page again.
- Oversized clipboard contents are no longer read fully into memory before
  the 20 MB limit applies.

## 1.1.0 (2026-09-29)

- Renamed from Clipped to Clipperino: app ID `io.github.djshiye.Clipperino`,
  binary and package `clipperino`. The RPM replaces `clipped` on upgrade, and
  the clipboard history moves to `~/.local/share/clipperino` on first launch.
  GNOME asks for the clipboard permission and the shortcut again, since both
  are granted per app ID.
- The tray menu opens as soon as the icon is clicked. GNOME's AppIndicator
  extension used to wait out the double-click time first, because the status
  item exported an `Activate` method; a vendored ksni (`third_party/ksni`) no
  longer exports it.

## 1.0.0 (2026-09-28)

Complete rewrite in Rust with GTK 4 and libadwaita, targeting Fedora GNOME on Wayland.

- Clipboard monitoring, paste injection, the global shortcut and autostart now go
  through GNOME's desktop portals (RemoteDesktop + Clipboard, GlobalShortcuts,
  Background); no X11, no shell extension required.
- Default shortcut is `Super+Shift+V` (`Super+V` is GNOME's notification list).
- History is stored in SQLite and survives restarts, images included.
- Search, keyboard navigation, `Ctrl+1`–`Ctrl+9`, pin, delete with undo, details view.
- Emoji browser backed by GNOME's localized emoji database; curated symbol browser;
  recently used chips.
- Preferences apply immediately: history size, paste on select, run in background.
- Password-manager clipboard entries are skipped; clipboard content is never logged.
- Adaptive layout: bottom tab bar on narrow windows, list plus preview pane above 700 px.
- Card-based visual design on Adwaita tokens: rounded rows, tinted selection, pill search, hover-revealed controls.
- Status icon (StatusNotifierItem) whose menu lists the ten most recent clips for one-click paste, grouped into Pinned and Recent sections, with image thumbnails and file icons, plus Open, Clear History…, Preferences and Quit; shown when a tray host exists.
- Packaged as an RPM with a spec, man page and AppStream metadata.

### Removed

- Windows and macOS builds, X11 hotkey grabbing, `GtkStatusIcon` tray, the
  remote "announcements" fetch and the `curl` dependency.
