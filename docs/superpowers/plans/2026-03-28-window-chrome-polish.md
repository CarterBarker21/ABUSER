# Window Chrome Polish Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Polish the custom title bar, window controls, and sidebar collapse button so the chrome feels branded, aligned, and reliable.

**Architecture:** Keep the behavior localized to the custom shell in `abuse/gui/main_window.py`. Use test-first coverage in `tests/test_gui_smoke.py` to pin collapse-state behavior and control sizing, then update the custom-painted widgets to use accent-aware chrome colors and cleaner geometry.

**Tech Stack:** Python 3.14, PyQt6, pytest-qt

---

## File Map

| File | Action | Responsibility |
|---|---|---|
| `abuse/gui/main_window.py` | Modify | Refine custom-painted title-bar buttons, title-bar tint, and collapse button shape/state styling |
| `tests/test_gui_smoke.py` | Modify | Add regression coverage for chrome behavior and collapse-state presentation |

### Task 1: Lock Down Chrome Behavior With Tests

**Files:**
- Modify: `tests/test_gui_smoke.py`
- Test: `tests/test_gui_smoke.py`

- [ ] **Step 1: Write the failing tests**

Add two smoke tests covering title-bar controls and sidebar collapse behavior:

```python
def test_title_bar_controls_are_present_and_sized(qtbot):
    window = build_window(qtbot)

    assert window.title_bar.minimumHeight() == window.title_bar.FIXED_HEIGHT
    assert window.title_bar.minimize_btn.isEnabled()
    assert window.title_bar.close_btn.isEnabled()
    assert window.title_bar.minimize_btn.width() >= 36
    assert window.title_bar.close_btn.width() >= 36


def test_sidebar_collapse_updates_tooltip_width_and_label_visibility(qtbot):
    window = build_window(qtbot)

    expanded_width = window.sidebar.width()
    assert not window._sidebar_collapsed
    assert window._collapse_btn.toolTip() == "Collapse sidebar"
    assert window.route_buttons["login"].title_label.isVisible()

    qtbot.mouseClick(window._collapse_btn, Qt.MouseButton.LeftButton)

    assert window._sidebar_collapsed
    assert window._collapse_btn.isChecked()
    assert window._collapse_btn.toolTip() == "Expand sidebar"
    assert window.sidebar.width() < expanded_width
    assert not window.route_buttons["login"].title_label.isVisible()

    qtbot.mouseClick(window._collapse_btn, Qt.MouseButton.LeftButton)

    assert not window._sidebar_collapsed
    assert not window._collapse_btn.isChecked()
    assert window._collapse_btn.toolTip() == "Collapse sidebar"
    assert window.sidebar.width() == expanded_width
    assert window.route_buttons["login"].title_label.isVisible()
```

- [ ] **Step 2: Run the targeted tests to verify they fail**

Run:
```bash
python -m pytest tests/test_gui_smoke.py -q
```

Expected: FAIL because the current title-bar controls are smaller than the new requirement and the collapse control does not yet match the desired polished behavior contract.

- [ ] **Step 3: Commit**

```bash
git add tests/test_gui_smoke.py
git commit -m "test: cover window chrome polish behavior"
```

### Task 2: Polish The Title Bar And Collapse Control

**Files:**
- Modify: `abuse/gui/main_window.py`
- Test: `tests/test_gui_smoke.py`

- [ ] **Step 1: Update `_WinBtn` geometry and state drawing**

Adjust the custom button to use a larger control size, support pressed state, and draw the minimize/close glyphs with cleaner alignment.

- [ ] **Step 2: Update `TitleBar.refresh_theme()`**

Blend the active accent into the title-bar background and refine the button colors so:
- minimize stays neutral
- close uses stronger danger hover/pressed feedback
- the title bar reads as a distinct chrome layer

- [ ] **Step 3: Redesign `CollapseButton`**

Convert the bottom-left collapse control into a wider pill-shaped button with:
- accent-aware background tint
- stronger border and hover states
- centered chevron animation
- reliable checked/collapsed visual state

- [ ] **Step 4: Adjust sidebar bottom layout if needed**

Keep the collapse control balanced in both expanded and collapsed modes without changing the actual collapse behavior.

- [ ] **Step 5: Run the targeted tests to verify they pass**

Run:
```bash
python -m pytest tests/test_gui_smoke.py -q
```

Expected: PASS.

- [ ] **Step 6: Run the full local test suite**

Run:
```bash
python -m pytest tests -q
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add abuse/gui/main_window.py tests/test_gui_smoke.py
git commit -m "feat: polish branded window chrome controls"
```
