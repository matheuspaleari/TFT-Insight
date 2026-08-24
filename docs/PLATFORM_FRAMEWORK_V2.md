# Platform Framework 2.0 — Acyclic Edition

## Version
`v0.5.0-alpha.1r1`

## Architecture rule

The dependency direction is:

```text
Pages
  ↓
Platform Core
  ↓
Components
  ↓
Design System
```

Navigation is a passive catalog:

```text
PlatformContext → NavigationCatalog
```

`platform_core` never imports `pages` during package initialization.

The router performs a lazy import only inside `render()`, after the
package has been initialized.

## Why

This eliminates the circular dependency that occurred in the first
`v0.5.0-alpha.1` attempt.

## Compatibility

The public surface used by existing pages remains:

```python
from partner_platform.platform_core import PlatformPage
```

Existing v0.4.1A2 pages therefore do not need to be rewritten.
