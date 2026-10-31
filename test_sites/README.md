# AccessGuard AI — Test Website Fixtures

This directory hosts deterministic local fixture websites used during scanner and accessibility testing.

## Fixture Sites

1. `accessible/` — Standard accessible HTML5 page featuring correct semantic landmarks, valid heading hierarchy, accessible buttons, labeled form controls, and appropriate image text alternatives (`alt`).
2. `violations/` — Controlled accessibility failure scenarios including missing image alternatives, unlabeled form inputs, empty buttons, low color contrast, and skipped heading levels.
3. `dynamic/` — Dynamic DOM manipulation, delayed client rendering, and asynchronous failure routes.
4. `external_links/` — Pages containing same-origin, cross-origin, mailto, tel, and fragment links to validate crawler boundary enforcement.
5. `long_page/` — Deep DOM tree and large content to validate crawler page-size, memory, and timeout limits.
