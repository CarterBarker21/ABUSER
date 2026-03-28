# ABUSER UI Redesign — Design Spec
**Date:** 2026-03-28
**Status:** Approved
**Scope:** Visual polish (primary) + minor UX improvements (secondary)
**Goal:** Global visual consistency across all 7 pages using a design token system and unified component library

---

## 1. Problem Statement

All 7 pages currently have inconsistent styling — hard-coded colors, varied spacing, and components that don't share a unified visual language. Changing the theme does not reliably affect all pages. The result feels like multiple disconnected tools rather than one cohesive app.

---

## 2. Approach

**Option A (Design Token System) + elements of Option C (Component-driven pages)**

- Define a single `DesignTokens` dataclass in `theme.py` with semantic color names
- Every component and page consumes only these tokens — no raw hex values anywhere
- Refactor `components.py` so all shared widgets are token-aware and visually polished
- Sweep all 7 pages to use only shared components with no inline custom styling

---

## 3. Design Token System

### Color Tokens

| Token | Role |
|---|---|
| `background` | Deepest layer — app background |
| `surface` | Cards, panels, sidebar |
| `surface_raised` | Inputs, hover states, tooltips |
| `border` | Subtle dividers and outlines |
| `border_strong` | Focused inputs, active states |
| `text_primary` | Main readable text |
| `text_muted` | Labels, secondary info |
| `text_disabled` | Inactive / placeholder text |
| `accent` | Brand color (from accent picker) |
| `accent_hover` | Accent on hover |
| `accent_muted` | Accent at ~20% opacity (backgrounds) |
| `danger` | Destructive actions |
| `success` | Connected, confirmed states |
| `warning` | Caution states |

### Spacing & Shape Constants

| Constant | Value |
|---|---|
| `radius_sm` | 4px — chips, tags |
| `radius_md` | 8px — buttons, inputs |
| `radius_lg` | 12px — cards, panels |
| `radius_xl` | 16px — main content areas |
| `spacing_xs` | 4px |
| `spacing_sm` | 8px |
| `spacing_md` | 12px |
| `spacing_lg` | 16px |
| `spacing_xl` | 24px |
| `font_size_sm` | 11px |
| `font_size_md` | 13px |
| `font_size_lg` | 15px |
| `font_size_xl` | 18px |

### Typography

- **Font:** Inter (fallback: Segoe UI on Windows)
- **Weights:** normal, medium (500), bold (700)
- Text hierarchy enforced exclusively via `text_primary` / `text_muted` / `text_disabled` tokens

---

## 4. Curated Themes (reduced from 12 to 4)

| Theme | Description |
|---|---|
| **Midnight** | Deep navy-black — default/flagship |
| **Obsidian** | Pure charcoal blacks, maximum contrast |
| **Catppuccin Mocha** | Soft dark with warm tones |
| **Discord Dark** | Familiar to Discord users |

The accent picker retains all 8 colors. Selecting an accent overrides only `accent`, `accent_hover`, and `accent_muted` tokens.

---

## 5. Component System (`components.py`)

All components inherit from `ThemedWidget` and consume `DesignTokens` exclusively.

| Component | Visual Spec |
|---|---|
| `AppButton` (primary) | Accent fill, `radius_md`, hover → `accent_hover` |
| `AppButton` (secondary) | `surface_raised` bg, `border` outline |
| `AppButton` (danger) | `danger` color fill, confirm dialog required |
| `AppLineEdit` | `surface_raised` bg, `border` outline, `border_strong` on focus, `radius_md` |
| `AppLineEdit` (multiline) | Same as above, min-height 80px |
| `PanelCard` | `surface` bg, `border` outline, `radius_lg`, `spacing_md` padding |
| `SectionLabel` | `text_muted`, `font_size_sm`, uppercase, letter-spacing |
| `StatusChip` | Pill, `radius_sm`, color from `success`/`danger`/`warning` |
| `ToggleSwitch` | Accent when on, `text_disabled` when off |
| `SidebarNavButton` | Icon + label, accent left-border + `accent_muted` bg on active, `surface_raised` on hover |
| `AppComboBox` | Matches `AppLineEdit` style |
| `InfoBanner` | Full-width, left-border accent, `accent_muted`/`danger`/`warning` bg variants |

---

## 6. Sidebar (UX Refinement)

- **Expanded width:** 220px | **Collapsed width:** 56px (icons only)
- Collapsible via toggle arrow button at sidebar bottom
- **Top group (core tools):** Login, Guilds, Nuker, DM
- **Divider**
- **Bottom group (utility):** Logs, Settings, Docs
- Active item: accent-colored left border + `accent_muted` background
- Hover: `surface_raised` background

---

## 7. Universal Page Layout Rule

Every page uses the same structural skeleton:

```
┌─────────────────────────────────────┐
│ Page Header                         │
│   Title (font_size_xl, text_primary)│
│   Subtitle (text_muted, optional)   │
├─────────────────────────────────────┤
│ Content Area                        │
│   PanelCards with spacing_lg gaps   │
│   SectionLabels as group headers    │
├─────────────────────────────────────┤
│ Action Row (inside relevant card)   │
│   Buttons bottom-aligned            │
└─────────────────────────────────────┘
```

---

## 8. Page-by-Page Design

### Login Page
- Single centered `PanelCard` (not full-width)
- Token `AppLineEdit` (password masked) + "Find Tokens" secondary `AppButton`
- Saved sessions list: rows with avatar placeholder, username, `StatusChip`, remove button
- "Connect" primary `AppButton` full-width inside card
- Feedback via `InfoBanner` (no popups)

### Guilds Page
- `SectionLabel` + search `AppLineEdit` at top
- Scrollable list of `PanelCard` rows: guild icon, name, member count, role
- Selecting a guild expands an inline detail panel (channels, roles, basic info)
- No destructive actions on this page

### Nuker Page
- `InfoBanner` (warning variant) prominently at top
- Safe-mode `ToggleSwitch` directly below banner
- `PanelCards` grouped by action category (channels, roles, messages)
- Each card: `SectionLabel` title, `text_muted` description, `AppButton` danger style
- All destructive actions require confirm dialog (themed with token system)

### DM Page
- Recipient `AppLineEdit` at top
- Multiline message `AppLineEdit`
- Options row: delay + repeat count as small labeled inputs side by side
- "Send" primary `AppButton`
- Result displayed via `InfoBanner`

### Logs Page
- Toolbar: log level filter (`AppComboBox`), clear button (secondary), auto-scroll `ToggleSwitch`
- Monospace log area, log levels color-mapped to tokens:
  - DEBUG → `text_muted`
  - INFO → `text_primary`
  - WARNING → `warning`
  - ERROR → `danger`
  - SUCCESS → `success`
- Bottom status bar: log count + last event timestamp

### Settings Page
- `SectionLabel` groups: Appearance, Behavior, Privacy, Connection
- Each setting: label (`text_primary`) + control in consistent two-column row
- Theme picker: 4 swatches | Accent picker: 8 color dots
- "Save" primary `AppButton` pinned to page bottom

### Docs Page
- Left sub-sidebar: command category list using `SidebarNavButton` style
- Content area: markdown rendered as styled `QLabel` blocks
- Heading/body hierarchy via font tokens

---

## 9. Out of Scope

- No changes to bot logic, commands, or backend systems
- No new pages or routes added
- No new dependencies introduced
- CLI/terminal mode untouched

---

## 10. Success Criteria

- Every page visually belongs to the same app — consistent spacing, color, typography
- Switching themes affects 100% of the UI with no leftover hard-coded colors
- Collapsible sidebar works on all pages
- All existing functionality preserved exactly
