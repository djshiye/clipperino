%global app_id io.github.djshiye.Clipperino

Name:           clipperino
Version:        1.4.0
Release:        1%{?dist}
Summary:        Clipboard history manager for GNOME

License:        MIT
URL:            https://github.com/djshiye/Clipperino
Source0:        %{url}/releases/download/v%{version}/%{name}-%{version}.tar.gz
# cargo vendor --locked, from the same tag
Source1:        %{url}/releases/download/v%{version}/%{name}-%{version}-vendor.tar.xz
# The public package signing key; CI exports it from the signing secret.
Source2:        RPM-GPG-KEY-djshiye

BuildRequires:  cargo-rpm-macros >= 24
BuildRequires:  meson >= 1.0
BuildRequires:  gcc
BuildRequires:  pkgconfig(gtk4) >= 4.22
BuildRequires:  pkgconfig(libadwaita-1) >= 1.9
BuildRequires:  pkgconfig(sqlite3)
BuildRequires:  pkgconfig(gio-2.0)
BuildRequires:  blueprint-compiler
BuildRequires:  desktop-file-utils
BuildRequires:  appstream
BuildRequires:  gettext

Requires:       gtk4%{?_isa} >= 4.22
Requires:       libadwaita%{?_isa} >= 1.9
Requires:       hicolor-icon-theme
# Clipboard monitoring, the global shortcut and autostart all go through portals.
Recommends:     xdg-desktop-portal-gnome
# Renamed from Clipped in 1.1.0.
Obsoletes:      clipped < 1.1.0
Provides:       clipped = %{version}-%{release}

%description
Clipperino keeps a history of the text and images you copy and lets you paste
any of them back into the app you were using. It runs in the background on
GNOME (Wayland) using desktop portals, opens with Super+Shift+V, and includes
a searchable emoji and symbol picker.

%prep
%autosetup -n %{name}-%{version} -a1
%cargo_prep -v vendor

%build
export CARGO_HOME="$PWD/.cargo"
export RUSTFLAGS="%{build_rustflags}"
%meson -Doffline=true
%meson_build

%install
%meson_install
# The DNF repository definition and its signing key, so the repository keeps itself configured.
install -Dpm 0644 build-aux/%{name}.repo %{buildroot}%{_sysconfdir}/yum.repos.d/%{name}.repo
install -Dpm 0644 %{SOURCE2} %{buildroot}%{_sysconfdir}/pki/rpm-gpg/RPM-GPG-KEY-djshiye-%{name}

%check
%meson_test

%files
%license LICENSE
%doc README.md docs/FEDORA_REBUILD_PLAN.md
%{_bindir}/%{name}
%{_mandir}/man1/%{name}.1*
%{_datadir}/applications/%{app_id}.desktop
%{_datadir}/dbus-1/services/%{app_id}.service
%{_datadir}/glib-2.0/schemas/%{app_id}.gschema.xml
%{_datadir}/icons/hicolor/scalable/apps/%{app_id}.svg
%{_datadir}/icons/hicolor/symbolic/apps/%{app_id}-symbolic.svg
%{_datadir}/metainfo/%{app_id}.metainfo.xml
# Plain %%config, not noreplace: an upgrade replaces an older hand-added copy
# (saved as .rpmorig/.rpmsave), which is how users of the old per-Fedora
# repository move to the signed one.
%config %{_sysconfdir}/yum.repos.d/%{name}.repo
%{_sysconfdir}/pki/rpm-gpg/RPM-GPG-KEY-djshiye-%{name}

%changelog
* Wed Nov 04 2026 Dino Klisura <115914552+djshiye@users.noreply.github.com> - 1.4.0-1
- Signed packages and dnf repository; one package for every Fedora release
- The package installs its own repository file and signing key

* Tue Sep 29 2026 djshiye <dreamfantom16@gmail.com> - 1.3.2-1
- Reconnect clipboard access after GNOME ends the permission session
- Flatpak manifest and store screenshots

* Tue Sep 29 2026 djshiye <dreamfantom16@gmail.com> - 1.3.1-1
- Tidier status icon menu: fewer rows, shorter labels, fewer icons
- Square-cropped image thumbnails in the status icon menu

* Tue Sep 29 2026 djshiye <dreamfantom16@gmail.com> - 1.3.0-1
- Images gallery, filter chips and media cards for image clips
- Day sections, type icons, colour swatches and hover previews
- Sharp full-size image previews; transparency shown as a checkerboard

* Tue Sep 29 2026 djshiye <dreamfantom16@gmail.com> - 1.2.0-1
- Pause recording and automatic deletion of old unpinned clips
- Paste copied files as files; search the full text of clips
- Fix row menu actions after the list changes; wire the status icon switch
- Reconnect or ask again when the clipboard permission session ends

* Tue Sep 29 2026 djshiye <dreamfantom16@gmail.com> - 1.1.0-1
- Rename from Clipped to Clipperino
- Open the tray menu immediately on click

* Mon Sep 28 2026 djshiye <dreamfantom16@gmail.com> - 1.0.0-1
- Rewrite in Rust with GTK 4 and libadwaita for GNOME on Wayland
