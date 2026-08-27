# Sprint 3 desktop layout fix

## Root cause

The mobile branch rendered correctly, while the desktop branch used `NavigationRail`
with a trailing account `ListTile`. At wide viewport widths, the trailing content could
be laid out with incomplete horizontal constraints, which caused a render object to
remain without a size. The repeated `Cannot hit test a render box with no size` messages
were secondary errors.

Opening Chrome DevTools reduced the viewport width below the responsive breakpoint, so
the app switched to the mobile drawer branch and appeared to work.

## Fix

`AppShell` now uses an explicitly constrained desktop sidebar:

- 88 px compact width.
- 280 px expanded width.
- Every navigation and account element receives bounded constraints.
- Mobile `NavigationDrawer` behavior remains unchanged.
