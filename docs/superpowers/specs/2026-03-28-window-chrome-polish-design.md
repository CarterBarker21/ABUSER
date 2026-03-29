# Window Chrome Polish Design

**Date:** 2026-03-28  
**Status:** Approved  
**Scope:** Desktop GUI chrome polish for title bar and sidebar collapse control  
**Goal:** Make the top bar feel intentionally branded, improve the minimize and close buttons visually and functionally, and replace the bottom-left collapse button with a cleaner, more legible control.

---

## Problem

The current window chrome reads as three unrelated pieces:

- The custom title bar is very close in color to the main background, so it does not feel like a distinct layer.
- The minimize and close buttons work, but their visual weight, glyph alignment, and hover states feel unfinished.
- The collapse button is too small and too neutral, so it looks disconnected from the rest of the shell.

The result is a UI that functions, but the chrome does not match the polish level of the rest of the redesign.

---

## Design Direction

Use an accent-aware branded chrome treatment:

- The title bar becomes a slightly accent-tinted elevated layer that still stays dark enough to preserve contrast.
- The minimize button remains neutral and utility-focused.
- The close button gets a stronger danger treatment on hover and press.
- The collapse button becomes a wider rounded capsule that visually belongs to the same control family as the title-bar buttons.

This keeps the UI feeling branded and deliberate without making the shell visually heavy.

---

## Component Changes

### Title Bar

- Keep the existing frameless custom title bar and drag behavior.
- Tint the background by blending the active accent color into the title bar surface.
- Keep the title text high-contrast and crisp.
- Strengthen the bottom border slightly so the title bar reads as a separate horizontal layer.

### Window Controls

- Preserve current behavior:
  - Minimize triggers `showMinimized()`
  - Close triggers `close()`
- Increase perceived hit area and improve icon alignment.
- Add clearer hover and pressed feedback.
- Keep minimize visually neutral.
- Make close hover state more intentionally destructive and more consistent with the current accent/danger palette.

### Sidebar Collapse Button

- Keep the chevron rotation animation and collapse/expand behavior.
- Replace the small square look with a rounded capsule control.
- Use accent-aware tinting so it feels related to the title bar and active navigation state.
- Ensure the control remains centered and balanced in both expanded and collapsed sidebar modes.
- Keep tooltip text accurate for both states.

---

## Implementation Plan

Changes stay local to the current desktop shell:

- `abuse/gui/main_window.py`
  - Refine `_WinBtn` painting and state handling
  - Update `TitleBar.refresh_theme()`
  - Redesign `CollapseButton` painting/sizing
  - Adjust collapse button container sizing/layout if needed
  - Keep existing behavior intact
- `tests/test_gui_smoke.py`
  - Add focused smoke coverage for title-bar controls and collapse button state

No bot logic, page logic, or route behavior changes are required.

---

## Behavior Requirements

- The custom title bar still supports window dragging.
- The minimize button remains clickable and visible in all themes.
- The close button remains clickable and clearly indicates destructive intent on hover.
- The collapse button still toggles the sidebar width and updates route button presentation.
- The collapse button tooltip changes between collapse and expand states.
- The styling must adapt to the current active accent color instead of hard-coding red-only values.

---

## Testing

- Extend GUI smoke tests to assert:
  - Title-bar controls exist and remain connected
  - Collapse button tooltip and checked state update correctly
  - Sidebar width changes between expanded and collapsed states
  - Route labels hide in collapsed mode and return in expanded mode
- Run the relevant GUI test file after implementation.

---

## Out of Scope

- No new routes or page content changes
- No redesign of the whole sidebar navigation system
- No window maximize/restore button
- No backend or bot-runner changes

---

## Success Criteria

- The top bar is visibly distinct from the main background and feels branded.
- The minimize and close buttons feel intentional, aligned, and polished.
- The collapse button no longer looks like a placeholder control.
- Existing sidebar collapse behavior still works cleanly.
- The updated window chrome passes the smoke test suite.
