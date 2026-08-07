"""Generate site-wide CSS color overrides from brand settings."""

from __future__ import annotations

import colorsys
import re

HEX_PATTERN = re.compile(r"^#([0-9A-Fa-f]{6}|[0-9A-Fa-f]{3})$")

THEME_PRESETS: dict[str, dict[str, str]] = {
    "zreta_indigo": {
        "label": "Zreta Sky & Mint",
        "primary": "#2563eb",
        "accent": "#14b8a6",
    },
    "navy_gold": {
        "label": "Classic Navy & Gold",
        "primary": "#1e3a5f",
        "accent": "#c9a227",
    },
    "ocean_teal": {
        "label": "Ocean Teal",
        "primary": "#0c4a6e",
        "accent": "#14b8a6",
    },
    "royal_purple": {
        "label": "Royal Purple",
        "primary": "#4c1d95",
        "accent": "#a78bfa",
    },
    "forest_green": {
        "label": "Forest Green",
        "primary": "#14532d",
        "accent": "#84cc16",
    },
    "burgundy_amber": {
        "label": "Burgundy & Amber",
        "primary": "#7f1d1d",
        "accent": "#f59e0b",
    },
    "slate_indigo": {
        "label": "Slate & Indigo",
        "primary": "#334155",
        "accent": "#6366f1",
    },
    "midnight_cyan": {
        "label": "Midnight Cyan",
        "primary": "#0f172a",
        "accent": "#22d3ee",
    },
    "custom": {
        "label": "Custom colors",
        "primary": "#1e3a5f",
        "accent": "#c9a227",
    },
}

DEFAULT_PRIMARY = THEME_PRESETS["zreta_indigo"]["primary"]
DEFAULT_ACCENT = THEME_PRESETS["zreta_indigo"]["accent"]


def normalize_hex(value: str, fallback: str) -> str:
    value = (value or "").strip()
    if not HEX_PATTERN.match(value):
        return fallback
    if len(value) == 4:
        value = "#" + "".join(ch * 2 for ch in value[1:])
    return value.lower()


def _hex_to_rgb(hex_color: str) -> tuple[float, float, float]:
    hex_color = normalize_hex(hex_color, DEFAULT_PRIMARY)
    return (
        int(hex_color[1:3], 16) / 255,
        int(hex_color[3:5], 16) / 255,
        int(hex_color[5:7], 16) / 255,
    )


def _rgb_to_hex(r: float, g: float, b: float) -> str:
    return f"#{int(round(r * 255)):02x}{int(round(g * 255)):02x}{int(round(b * 255)):02x}"


def _shade(hex_color: str, lightness: float) -> str:
    r, g, b = _hex_to_rgb(hex_color)
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    l = max(0.0, min(1.0, lightness))
    r, g, b = colorsys.hls_to_rgb(h, l, s)
    return _rgb_to_hex(r, g, b)


def _palette(base_hex: str) -> dict[str, str]:
    base_hex = normalize_hex(base_hex, DEFAULT_PRIMARY)
    r, g, b = _hex_to_rgb(base_hex)
    _, base_l, _ = colorsys.rgb_to_hls(r, g, b)
    return {
        "50": _shade(base_hex, min(base_l + 0.42, 0.96)),
        "100": _shade(base_hex, min(base_l + 0.34, 0.90)),
        "200": _shade(base_hex, min(base_l + 0.26, 0.82)),
        "300": _shade(base_hex, min(base_l + 0.18, 0.72)),
        "400": _shade(base_hex, min(base_l + 0.10, 0.62)),
        "500": _shade(base_hex, base_l),
        "600": base_hex,
        "700": _shade(base_hex, max(base_l - 0.08, 0.12)),
        "800": _shade(base_hex, max(base_l - 0.16, 0.08)),
        "900": _shade(base_hex, max(base_l - 0.24, 0.04)),
    }


def _rgba(hex_color: str, alpha: float) -> str:
    hex_color = normalize_hex(hex_color, DEFAULT_PRIMARY)
    r, g, b = _hex_to_rgb(hex_color)
    return f"rgba({int(r * 255)}, {int(g * 255)}, {int(b * 255)}, {alpha})"


def build_brand_css(primary: str, accent: str) -> str:
    primary = normalize_hex(primary, DEFAULT_PRIMARY)
    accent = normalize_hex(accent, DEFAULT_ACCENT)
    primary_palette = _palette(primary)
    accent_palette = _palette(accent)

    lines = [
        ":root {",
        f"  --color-primary-50: {primary_palette['50']};",
        f"  --color-primary-100: {primary_palette['100']};",
        f"  --color-primary-200: {primary_palette['200']};",
        f"  --color-primary-300: {primary_palette['300']};",
        f"  --color-primary-400: {primary_palette['400']};",
        f"  --color-primary-500: {primary_palette['500']};",
        f"  --color-primary-600: {primary_palette['600']};",
        f"  --color-primary-700: {primary_palette['700']};",
        f"  --color-primary-800: {primary_palette['800']};",
        f"  --color-primary-900: {primary_palette['900']};",
        f"  --color-accent-50: {accent_palette['50']};",
        f"  --color-accent-100: {accent_palette['100']};",
        f"  --color-accent-200: {accent_palette['200']};",
        f"  --color-accent-300: {accent_palette['300']};",
        f"  --color-accent-400: {accent_palette['400']};",
        f"  --color-accent-500: {accent_palette['500']};",
        f"  --color-accent-600: {accent_palette['600']};",
        f"  --color-accent-700: {accent_palette['700']};",
        f"  --text-accent: {accent_palette['600']};",
        f"  --text-link: {primary_palette['600']};",
        f"  --text-link-hover: {primary_palette['700']};",
        f"  --border-focus: {primary_palette['500']};",
        f"  --border-accent: {accent_palette['400']};",
        f"  --surface-sidebar: {primary_palette['900']};",
        f"  --footer-bg: {primary_palette['50']};",
        f"  --footer-text: {primary_palette['700']};",
        f"  --footer-heading: {primary_palette['900']};",
        f"  --footer-link-hover: {primary_palette['600']};",
        f"  --footer-accent: {accent_palette['600']};",
        f"  --nav-link-hover: {primary_palette['600']};",
        f"  --nav-link-active: {primary_palette['700']};",
        f"  --nav-link-active-border: {accent_palette['400']};",
        f"  --sidebar-item-active-bg: {_rgba(accent, 0.14)};",
        f"  --sidebar-item-active-text: {accent_palette['300']};",
        f"  --sidebar-item-active-icon: {accent_palette['400']};",
        f"  --btn-primary-bg: {primary_palette['600']};",
        f"  --btn-primary-bg-hover: {primary_palette['700']};",
        f"  --btn-primary-bg-active: {primary_palette['800']};",
        f"  --table-row-selected: {primary_palette['50']};",
        f"  --color-info-fg: {primary_palette['600']};",
        f"  --color-info-icon: {primary_palette['500']};",
        f"  --hero-gradient-accent: {_rgba(accent, 0.12)};",
        f"  --hero-gradient-primary: {_rgba(primary, 0.1)};",
        f"  --stats-gradient-start: {primary_palette['50']};",
        f"  --stats-gradient-end: {accent_palette['50']};",
        f"  --stats-accent: {accent_palette['500']};",
        "}",
        '[data-theme="dark"] {',
        f"  --surface-page: {primary_palette['900']};",
        f"  --surface-section: {primary_palette['800']};",
        f"  --surface-card: {primary_palette['700']};",
        f"  --surface-raised: {primary_palette['600']};",
        f"  --surface-sidebar: {_shade(primary, 0.03)};",
        f"  --surface-header: {_rgba(primary_palette['900'], 0.94)};",
        f"  --text-link: {primary_palette['300']};",
        f"  --text-link-hover: {primary_palette['200']};",
        f"  --footer-bg: {_shade(primary, 0.03)};",
        f"  --sidebar-item-active-bg: {_rgba(accent, 0.18)};",
        "}",
    ]
    return "\n".join(lines)


def get_brand_colors(settings_obj) -> dict[str, str]:
    preset = getattr(settings_obj, "brand_theme_preset", "zreta_indigo") or "zreta_indigo"
    preset_data = THEME_PRESETS.get(preset, THEME_PRESETS["zreta_indigo"])
    primary = normalize_hex(
        getattr(settings_obj, "brand_primary_color", "") or preset_data["primary"],
        preset_data["primary"],
    )
    accent = normalize_hex(
        getattr(settings_obj, "brand_accent_color", "") or preset_data["accent"],
        preset_data["accent"],
    )
    return {
        "preset": preset,
        "primary": primary,
        "accent": accent,
        "theme_color": _palette(primary)["900"],
    }


def get_brand_theme_css(settings_obj) -> str:
    colors = get_brand_colors(settings_obj)
    return build_brand_css(colors["primary"], colors["accent"])


def get_preset_choices() -> list[tuple[str, str]]:
    return [(key, data["label"]) for key, data in THEME_PRESETS.items()]
