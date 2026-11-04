# Flatpak

Status and next steps for the Flatpak build. Install and build commands for
users are in the README.

## Status (2026-09-29)

Done, on `main` since commit 6ad6d08, shipped with release 1.3.2 (the
`.flatpak` bundle attached to it has not been tested in the real session):

- Manifest: `build-aux/flatpak/io.github.djshiye.Clipperino.yml`, GNOME 50
  runtime (same GTK 4.22 / libadwaita 1.9 as Fedora 44), rust-stable 25.08.
  It builds the working tree (`type: dir`).
- `build-aux/flatpak/cargo-sources.json`: crates for the offline build.
  Regenerate after every `Cargo.lock` change:
  `flatpak-cargo-generator.py Cargo.lock -o build-aux/flatpak/cargo-sources.json`
  (from flatpak/flatpak-builder-tools, needs aiohttp, PyYAML and tomlkit).
- Tray: inside the sandbox, `ksni` runs with `disable_dbus_name`, because
  Flatpak refuses the `StatusNotifierItem-PID-ID` name
  (`platform::is_sandboxed()` checks `/.flatpak-info`).
- Permissions: ipc, wayland, fallback-x11, dri and
  `--talk-name=org.kde.StatusNotifierWatcher`. Clipboard, shortcut, paste
  and autostart go through portals.
- CI: on `v*` tags the `flatpak` job builds `clipperino.flatpak` in parallel,
  and `flatpak-upload` attaches it to the release as
  `clipperino-<version>.x86_64.flatpak`. It never blocks the RPM or the dnf
  repository. The job has not run yet.
- Screenshots: `data/screenshots/*.png`, listed in the metainfo by
  raw.githubusercontent.com URL. Regenerate them with a debug build and
  `CLIPPERINO_DEBUG_SEED=demo` in an isolated session (see
  `win.debug-snapshot`), never from real history.

Verified: the build installs, the sandboxed app starts, loads emoji and
symbols, and the tray registers and serves its menu through the D-Bus
proxy, tested against a stand-in tray host on a private bus.
`flatpak-builder-lint` passes except for screenshot mirroring, which the
Flathub build does itself (`appstream-screenshots-not-mirrored-in-ostree`,
`appstream-external-screenshot-url`), and a warning that the GNOME 51 runtime
exists. Staying on 50 is deliberate: it matches the native Fedora 44 build.

## Next steps

### 1. Test in the real session

Not done yet. Portals only work in the real session, so the checks need the
desktop:

```bash
flatpak-builder --user --install --force-clean build-flatpak \
    build-aux/flatpak/io.github.djshiye.Clipperino.yml
# quit the native app from its tray menu first (same app ID)
flatpak run io.github.djshiye.Clipperino
```

GNOME asks for the remote-desktop and shortcut permissions again, and history
starts empty: the Flatpak's settings and data live in
`~/.var/app/io.github.djshiye.Clipperino`. Check that:

- [ ] Copying text shows up in the tray menu. This tests that app-to-host
      `LayoutUpdated` signals get through the proxy, which the stand-in host
      did not.
- [ ] `Super+Shift+V` opens the window, and Enter pastes into the previous app.
- [ ] Copying an image gives a tray thumbnail and it pastes.
- [ ] Copying a file in Files pastes back as a file.
- [ ] The emoji and symbols pages work, including localized emoji search.
- [ ] Pause Recording, Preferences, and the Start at Login switch work.

Then go back to native. This matters: while the Flatpak is installed, its
desktop file shadows the native one in the app grid, and each Flatpak start
rewrites `~/.config/autostart/io.github.djshiye.Clipperino.desktop` to launch
the Flatpak.

```bash
flatpak uninstall --user io.github.djshiye.Clipperino
clipperino &   # the native app reclaims the login item on start
```

### 2. Release

Done: 1.3.2 was released for a reconnect fix and carries the Flatpak job.
Check that the v1.3.2 release has the `.flatpak` bundle. If the real-session
test finds problems, fix them in a later release and use that tag below.

### 3. Submit to Flathub

Opening the pull request publishes from the user's GitHub account, so ask
before doing it.

1. Fork `flathub/flathub` and make a branch from `new-pr`.
2. Add a copy of the manifest whose source is git instead of `dir`:
   ```yaml
   sources:
     - type: git
       url: https://github.com/djshiye/clipperino.git
       tag: v1.4.0
       commit: <full sha of the tag>
     - cargo-sources.json
   ```
   plus `cargo-sources.json`. Remove the local-build comments.
3. Open a PR against `new-pr`. The bot builds it; answer reviewer comments.
4. After the merge, `flathub/io.github.djshiye.Clipperino` exists with the
   user as maintainer. Verify the app on flathub.org by signing in with
   GitHub, which covers `io.github.djshiye`.
5. Later releases: a PR to that repo updating `tag`, `commit` and, if
   `Cargo.lock` changed, `cargo-sources.json`.

Possible review questions: the app ID `io.github.djshiye.Clipperino` against
the lowercase repo `djshiye/clipperino` (GitHub treats them the same). Also
the app needs the RemoteDesktop portal to read the clipboard, which the
README and first-run page explain.

### Other desktops

KDE's portal implements the Clipboard portal since Plasma 6.4 (merge request
!337 in plasma/xdg-desktop-portal-kde, merged 2025-03-26), so Clipperino
should work on Plasma. Untested: try it in a Plasma VM before claiming it.

## Local setup already in place

A per-user `flathub` remote, and `org.gnome.Sdk//50`, `org.gnome.Platform//50`,
`org.freedesktop.Sdk.Extension.rust-stable//25.08` and `org.flatpak.Builder`
(for `flatpak-builder-lint`) installed per user. Build caches are in
`.flatpak-builder/` and `build-flatpak/` (gitignored).
