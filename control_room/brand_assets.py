"""Bundled Zreta brand kit assets available for download."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BrandAsset:
    key: str
    label: str
    description: str
    static_path: str
    filename: str
    group: str


BRAND_KIT_ASSETS: tuple[BrandAsset, ...] = (
    BrandAsset(
        "logo-mark-1024",
        "Logo mark — 1024px",
        "Square icon for apps, avatars, and product splash screens.",
        "images/brand/png/logo-mark-1024.png",
        "zreta-logo-mark-1024.png",
        "mark",
    ),
    BrandAsset(
        "logo-mark-512",
        "Logo mark — 512px",
        "Medium square mark for dashboards and app icons.",
        "images/brand/png/logo-mark-512.png",
        "zreta-logo-mark-512.png",
        "mark",
    ),
    BrandAsset(
        "logo-mark-256",
        "Logo mark — 256px",
        "Small square mark for UI chrome and emails.",
        "images/brand/png/logo-mark-256.png",
        "zreta-logo-mark-256.png",
        "mark",
    ),
    BrandAsset(
        "logo-mark-128",
        "Logo mark — 128px",
        "Compact mark for tight layouts.",
        "images/brand/png/logo-mark-128.png",
        "zreta-logo-mark-128.png",
        "mark",
    ),
    BrandAsset(
        "logo-mark-64",
        "Logo mark — 64px",
        "Favicon-sized mark.",
        "images/brand/png/logo-mark-64.png",
        "zreta-logo-mark-64.png",
        "mark",
    ),
    BrandAsset(
        "logo-mark-32",
        "Logo mark — 32px",
        "Minimum size for browser tabs.",
        "images/brand/png/logo-mark-32.png",
        "zreta-logo-mark-32.png",
        "mark",
    ),
    BrandAsset(
        "logo-full-3360",
        "Full lockup — 3360px",
        "High-resolution horizontal logo with wordmark.",
        "images/brand/png/logo-full-3360.png",
        "zreta-logo-full-3360.png",
        "lockup",
    ),
    BrandAsset(
        "logo-full-1680",
        "Full lockup — 1680px",
        "Print and presentation-ready horizontal logo.",
        "images/brand/png/logo-full-1680.png",
        "zreta-logo-full-1680.png",
        "lockup",
    ),
    BrandAsset(
        "logo-full-840",
        "Full lockup — 840px",
        "Website hero and slide deck logo.",
        "images/brand/png/logo-full-840.png",
        "zreta-logo-full-840.png",
        "lockup",
    ),
    BrandAsset(
        "logo-full-420",
        "Full lockup — 420px",
        "Compact horizontal logo for documents.",
        "images/brand/png/logo-full-420.png",
        "zreta-logo-full-420.png",
        "lockup",
    ),
    BrandAsset(
        "apple-touch-icon",
        "Apple touch icon — 180px",
        "Home-screen icon for mobile bookmarks.",
        "images/brand/png/apple-touch-icon.png",
        "zreta-apple-touch-icon.png",
        "icons",
    ),
    BrandAsset(
        "favicon-32",
        "Favicon — 32px PNG",
        "Raster favicon fallback.",
        "images/brand/png/favicon-32.png",
        "zreta-favicon-32.png",
        "icons",
    ),
    BrandAsset(
        "logo-mark-svg",
        "Logo mark — SVG",
        "Scalable vector icon (best for developers).",
        "images/brand/logo-mark.svg",
        "zreta-logo-mark.svg",
        "vector",
    ),
    BrandAsset(
        "logo-full-svg",
        "Full lockup — SVG",
        "Scalable vector logo with wordmark.",
        "images/brand/logo-full.svg",
        "zreta-logo-full.svg",
        "vector",
    ),
    BrandAsset(
        "logo-full-dark-svg",
        "Full lockup — dark SVG",
        "Vector logo for dark backgrounds.",
        "images/brand/logo-full-inverse.svg",
        "zreta-logo-full-dark.svg",
        "vector",
    ),
    BrandAsset(
        "favicon-svg",
        "Favicon — SVG",
        "Scalable favicon source.",
        "images/brand/favicon.svg",
        "zreta-favicon.svg",
        "vector",
    ),
)


def grouped_brand_assets() -> dict[str, list[BrandAsset]]:
    groups = {
        "mark": [],
        "lockup": [],
        "icons": [],
        "vector": [],
    }
    for asset in BRAND_KIT_ASSETS:
        groups[asset.group].append(asset)
    return groups


def brand_asset_lookup() -> dict[str, BrandAsset]:
    return {asset.key: asset for asset in BRAND_KIT_ASSETS}
