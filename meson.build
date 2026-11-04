project('clipperino', 'rust',
  version: '1.4.0',
  meson_version: '>= 1.0.0',
  license: 'MIT',
  default_options: ['buildtype=release'],
)

gnome = import('gnome')
i18n = import('i18n')

app_id = 'io.github.djshiye.Clipperino'
prefix = get_option('prefix')
bindir = prefix / get_option('bindir')
datadir = prefix / get_option('datadir')

# Runtime/build requirements are checked here; Cargo links against them.
dependency('gtk4', version: '>= 4.22')
dependency('libadwaita-1', version: '>= 1.9')
dependency('sqlite3')
find_program('blueprint-compiler')
find_program('glib-compile-resources')
find_program('glib-compile-schemas')
cargo = find_program('cargo')

subdir('data')
subdir('po')
subdir('src')

gnome.post_install(
  glib_compile_schemas: true,
  gtk_update_icon_cache: true,
  update_desktop_database: true,
)
