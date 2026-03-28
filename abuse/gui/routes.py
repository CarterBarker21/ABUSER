"""Route metadata shared by the sidebar, settings, and startup flow."""

from __future__ import annotations

from dataclasses import dataclass


ROUTE_LOGIN    = "login"
ROUTE_DOCS     = "docs"
ROUTE_GUILDS   = "guilds"
ROUTE_NUKER    = "nuker"
ROUTE_DM       = "dm"
ROUTE_LOGS     = "logs"
ROUTE_SETTINGS = "settings"
ROUTE_LAST_USED = "last_used"


@dataclass(frozen=True)
class RouteDefinition:
    key: str
    label: str
    icon_name: str
    description: str
    group: str = "core"   # "core" | "utility"


ROUTES = [
    # ── Core tools (top of sidebar) ──────────────────────────────────────────
    RouteDefinition(ROUTE_LOGIN,    "Login",    "login",    "Connect, disconnect, and manage remembered sessions.", group="core"),
    RouteDefinition(ROUTE_GUILDS,   "Guilds",   "guilds",   "Browse connected guilds and inspect their details.",  group="core"),
    RouteDefinition(ROUTE_NUKER,    "Nuker",    "nuker",    "Preview grouped action surfaces and safety gating.",  group="core"),
    RouteDefinition(ROUTE_DM,       "DM",       "dm",       "Compose drafts and review messaging controls.",       group="core"),
    # ── Utility (bottom of sidebar) ──────────────────────────────────────────
    RouteDefinition(ROUTE_LOGS,     "Logs",     "logs",     "Inspect runtime logs with filtering and export.",     group="utility"),
    RouteDefinition(ROUTE_SETTINGS, "Settings", "settings", "Adjust appearance, startup behavior, and privacy.",  group="utility"),
    RouteDefinition(ROUTE_DOCS,     "Docs",     "docs",     "Read the in-app guide and current UI notes.",         group="utility"),
]

ROUTE_INDEX  = {route.key: index for index, route in enumerate(ROUTES)}
ROUTE_LABELS = {route.key: route.label for route in ROUTES}
LABEL_TO_ROUTE = {route.label: route.key for route in ROUTES}
LABEL_TO_ROUTE["Last Used"] = ROUTE_LAST_USED
LABEL_TO_ROUTE["Commands"]  = ROUTE_GUILDS

STARTUP_OPTIONS = [route.label for route in ROUTES] + ["Last Used"]


def get_route_index(route_key: str) -> int:
    return ROUTE_INDEX.get(route_key, 0)


def get_route_label(route_key: str) -> str:
    return ROUTE_LABELS.get(route_key, ROUTE_LABELS[ROUTE_LOGIN])


def normalize_route(route_key: str | None) -> str:
    if not route_key:
        return ROUTE_LOGIN
    normalized = route_key.lower().strip().replace(" ", "_")
    if normalized == "last_used":
        return ROUTE_LAST_USED
    return normalized if normalized in ROUTE_INDEX else ROUTE_LOGIN


def route_from_label(label: str | None) -> str:
    if not label:
        return ROUTE_LOGIN
    return LABEL_TO_ROUTE.get(label, ROUTE_LOGIN)
