# Changelog

All notable changes to this project are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and the project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.0]

### Added

- Space bar shortcut for baking a cookie.
- Autosave every minute, alongside the manual **Save** button.
- Versioned save format (`SAVE_VERSION`) that loads legacy saves and reports
  a corrupted file instead of crashing.
- Compact number rendering (`1.5K`, `2.3M`) in the UI.
- GitHub Actions workflow running the test suite on Python 3.9–3.13.

### Changed

- Costs and totals now come from the UI-free `economy` module, shared by the
  shop and the game loop.
- README rewritten for the 0.2 release.

### Fixed

- Prices are rounded instead of truncated, so `100 * 1.15` no longer sells
  for 114.
- Upgrade effects no longer stack again on every save load.
- The click upgrade level is tracked separately from click power.

## [0.1.0]

### Added

- Initial release: clickable cookie, five buildings, four upgrades and a
  tkinter interface.
