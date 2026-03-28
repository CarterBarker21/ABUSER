import pytest
from abuse.gui.theme import (
    DesignTokens,
    make_design_tokens,
    create_theme_from_preset,
    get_theme_manager,
)


def test_design_tokens_fields_populated():
    theme = create_theme_from_preset("Midnight")
    dt = make_design_tokens(theme)
    assert dt.background == theme.bg_primary
    assert dt.surface == theme.surface
    assert dt.surface_raised == theme.surface_hover
    assert dt.border == theme.border
    assert dt.border_strong == theme.border_light
    assert dt.text_primary == theme.text_primary
    assert dt.text_secondary == theme.text_secondary
    assert dt.text_muted == theme.text_muted
    assert dt.text_disabled == theme.text_disabled
    assert dt.accent == theme.accent_primary
    assert dt.accent_hover == theme.accent_hover
    assert dt.accent_muted.startswith("rgba(")
    assert dt.danger == theme.error
    assert dt.danger_hover == theme.error_hover
    assert dt.success == theme.success
    assert dt.success_hover == theme.success_hover
    assert dt.success_bright == theme.success_bright
    assert dt.warning == theme.warning


def test_design_tokens_all_four_themes():
    for name in ("Midnight", "Obsidian", "Discord Dark", "Catppuccin Mocha"):
        theme = create_theme_from_preset(name)
        dt = make_design_tokens(theme)
        assert isinstance(dt, DesignTokens)
        assert dt.background
        assert dt.accent


def test_theme_manager_design_tokens_property():
    manager = get_theme_manager()
    dt = manager.design_tokens
    assert isinstance(dt, DesignTokens)
    assert dt.accent == manager.theme.accent_primary
