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
- Support for exporting external image files


## [1.1.1] – 2025-06-09
### Fixed
- Escape newline character in x520


## [1.1.0] – 2024-01-27
### Added
- Multi-file export

### Fixed
- Ignore non-existing columns


## [1.0.1] – 2023-02-21
Initial release


[1.2.1]: https://github.com/relikd/abcddb2vcard/compare/v1.2.0...v1.2.1
[1.2.0]: https://github.com/relikd/abcddb2vcard/compare/v1.1.1...v1.2.0
[1.1.1]: https://github.com/relikd/abcddb2vcard/compare/v1.1.0...v1.1.1
[1.1.0]: https://github.com/relikd/abcddb2vcard/compare/v1.0.1...v1.1.0
[1.0.1]:https://github.com/relikd/abcddb2vcard/compare/4d3af13996bbd26dcb07285a8460f04af345fa85...v1.0.1
