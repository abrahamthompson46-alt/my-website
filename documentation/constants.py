"""Documentation section and article type constants."""

GETTING_STARTED = "getting_started"
INSTALLATION = "installation"
GUIDE = "guide"
FAQ = "faq"
API = "api"
RELEASE_NOTE = "release_note"

ARTICLE_TYPES = [
    (GETTING_STARTED, "Getting Started"),
    (INSTALLATION, "Installation"),
    (GUIDE, "Guide"),
    (FAQ, "FAQ"),
    (API, "API Reference"),
    (RELEASE_NOTE, "Release Note"),
]

SECTIONS = [
    {"slug": "getting-started", "label": "Getting Started", "icon": "rocket", "type": GETTING_STARTED, "url_name": "documentation:getting_started"},
    {"slug": "installation", "label": "Installation", "icon": "download", "type": INSTALLATION, "url_name": "documentation:installation"},
    {"slug": "videos", "label": "Videos", "icon": "play-circle", "url_name": "documentation:videos"},
    {"slug": "faqs", "label": "FAQs", "icon": "help-circle", "type": FAQ, "url_name": "documentation:faqs"},
    {"slug": "api", "label": "API Documentation", "icon": "code", "url_name": "documentation:api"},
    {"slug": "downloads", "label": "Downloads", "icon": "file-down", "url_name": "documentation:downloads"},
    {"slug": "release-notes", "label": "Release Notes", "icon": "tag", "type": RELEASE_NOTE, "url_name": "documentation:release_notes"},
]
