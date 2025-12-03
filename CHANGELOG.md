# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project does adhere to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


## [1.2.1] – 2025-12-03
### Fixed
- Soft-fail on unknown social service types. (continue export even if a service field fails)
- SQL sanitize respects `INNER JOIN`. Fixes an error introduced in v1.1.0 which would prohibit export of contacts with at least one social service.


## [1.2.0] – 2025-06-09
### Added
- Support for external images (referenced only by id within db)
- Warning for missing `-wal` & `-shm` files
- Warning for missing (and hidden) `.AddressBook-v22_SUPPORT` image storage folder

### Removed
- Warning for missing column `ZSERVICENAME` (column is not that important anyway)


## [1.1.1] – 2025-06-09
### Fixed
- Escape newline character in x520


## [1.1.0] – 2024-01-27
### Added
- Multi-file output. Use a formatter string to export each vcard individually.

### Fixed
- Continue processing of remaining entries if a single contact card fails to process
- Ignore table columns that do not exist (e.g., `ZTHUMBNAILIMAGEDATA`)


## [1.0.1] – 2023-02-21
### Added
- Types
- `abcddb2vcard` is now available on PyPi (`pip3 install abcddb2vcard`, then use `abcddb2vcard` or `vcard2img` in your shell)

### Fixed
- Crash when processing data fields with no corresponding Contact record



[1.2.1]: https://github.com/relikd/abcddb2vcard/compare/v1.2.0...v1.2.1
[1.2.0]: https://github.com/relikd/abcddb2vcard/compare/v1.1.1...v1.2.0
[1.1.1]: https://github.com/relikd/abcddb2vcard/compare/v1.1.0...v1.1.1
[1.1.0]: https://github.com/relikd/abcddb2vcard/compare/v1.0.1...v1.1.0
[1.0.1]:https://github.com/relikd/abcddb2vcard/compare/4d3af13996bbd26dcb07285a8460f04af345fa85...v1.0.1
