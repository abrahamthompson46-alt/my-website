"""Contextual help content for Control Room pages."""

from __future__ import annotations

PAGE_HELP: dict[str, dict] = {
    "dashboard": {
        "title": "Super Dashboard guide",
        "intro": "Your home base for running the marketing site without code or terminal access.",
        "steps": [
            "Check the status pills — maintenance mode blocks public visitors but staff still have access.",
            "Use Platform Setup first on a new site to seed products, CMS pages, navigation, and demo content.",
            "Open Site Settings to set branding, contact emails, and header buttons (Start Trial / Request Demo).",
            "Use Products to publish catalog entries, pricing plans, and ChurchHub external links.",
            "Ops Dashboard shows live demo requests, customers, and support tickets.",
        ],
        "tips": [
            "Run seeds from Platform Setup if pricing plans or homepage content are missing.",
            "After changing navigation JSON, save and refresh the public site to verify links.",
        ],
        "mistakes": [
            "Enabling maintenance mode during a launch without telling your team.",
            "Skipping migrate/collectstatic on the server after pulling code updates.",
        ],
    },
    "settings": {
        "title": "Site Settings guide",
        "intro": "Global branding and behavior applied to every public page instantly after save.",
        "steps": [
            "Set site name, tagline, and footer copyright under Branding.",
            "Upload brand logo and favicon — they appear in the header, footer, and browser tab.",
            "Choose Zreta Sky & Mint (or Custom) under Brand colors — save to refresh the live palette.",
            "Set default SEO title and OG image for pages that do not define their own metadata.",
            "Configure contact and support emails — used in footers and system emails.",
            "Header CTA labels/URLs control the top-right buttons. Use contact:trial and contact:demo.",
            "Turn on maintenance mode only when deploying; add a clear maintenance message.",
        ],
        "tips": [
            "Demo form, newsletter, and partner toggles hide sections site-wide when disabled.",
        ],
        "mistakes": [
            "Using contact:form for CTAs — use contact:trial or contact:demo instead.",
            "Picking a dark brand preset and wondering why the homepage looks too dark.",
        ],
    },
    "navigation": {
        "title": "Navigation guide",
        "intro": "Menus for the public header, footer, and internal portals.",
        "steps": [
            "Edit public_header to change the Products mega menu and top links.",
            "Use url_name (e.g. products:detail) plus url_kwargs (e.g. {\"slug\": \"churchhub\"}) for product links.",
            "Use plain url for external links such as https://mychurch.zreta.com/contact/.",
            "Save the menu, then open the live site and test every link in desktop and mobile nav.",
        ],
        "tips": [
            "Invalid url_name values fail silently to # — always test after editing JSON.",
        ],
        "mistakes": [
            "Pointing all products to products:list instead of each product detail page.",
            "Breaking JSON syntax — use a JSON validator before saving.",
        ],
    },
    "navigation_edit": {
        "title": "Editing a navigation menu",
        "intro": "Each menu is a JSON array of items stored in the database.",
        "steps": [
            "Keep the structure as a JSON array [ {...}, {...} ].",
            "Mega menus use type: \"mega\" with columns and links arrays.",
            "Save, then visit the public site to confirm links resolve correctly.",
        ],
        "tips": ["Copy the default from common/navigation.py if you need a clean starting point."],
        "mistakes": ["Trailing commas in JSON will prevent save."],
    },
    "redirects": {
        "title": "URL Redirects guide",
        "intro": "Redirect old paths to new URLs without redeploying code.",
        "steps": [
            "from_path must start with / and match the old URL path.",
            "Use to_path for internal paths or to_url_name for a named Django route.",
            "Choose 301 for permanent SEO moves, 302 for temporary redirects.",
        ],
        "tips": ["Test redirects in a private/incognito window to avoid cache confusion."],
        "mistakes": ["Creating redirect loops (A → B → A)."],
    },
    "redirect_form": {
        "title": "Adding or editing a redirect",
        "intro": "One redirect rule maps a single incoming path to a destination.",
        "steps": [
            "Enter the exact path visitors will request (including leading slash).",
            "Provide either a destination path or a url_name — not both unless intentional.",
            "Leave notes for your team explaining why the redirect exists.",
        ],
        "tips": [],
        "mistakes": ["Forgetting the leading slash on from_path."],
    },
    "announcements": {
        "title": "Announcements guide",
        "intro": "Timed banners on public pages and/or the customer portal.",
        "steps": [
            "Set starts_at and ends_at to control visibility automatically.",
            "Choose variant (info, warning, success) for visual emphasis.",
            "Use show_on_public and show_on_portal to target the right audience.",
        ],
        "tips": ["Deactivate instead of deleting to preserve history."],
        "mistakes": ["Leaving expired announcements marked active without end dates."],
    },
    "announcement_form": {
        "title": "Creating an announcement",
        "intro": "Short message with optional link displayed site-wide.",
        "steps": [
            "Keep the message under two lines for mobile readability.",
            "Add link_url and link_label if the banner should drive to a CTA page.",
            "Preview on the homepage after saving.",
        ],
        "tips": [],
        "mistakes": [],
    },
    "flags": {
        "title": "Feature Flags guide",
        "intro": "Toggle platform features without code deploys.",
        "steps": [
            "demo_form — shows/hides demo request forms on marketing pages.",
            "newsletter — controls newsletter signup sections.",
            "public_registration — allows or blocks self-service signups.",
            "Use the quick toggle on the list or edit for label/description updates.",
        ],
        "tips": ["Document flag keys before sharing access with other admins."],
        "mistakes": ["Disabling demo_form while still linking CTAs to #demo anchors."],
    },
    "flag_form": {
        "title": "Editing a feature flag",
        "intro": "Keys are referenced in templates — do not rename keys casually.",
        "steps": [
            "Use lowercase keys with underscores (e.g. demo_form).",
            "Write a clear description so future admins understand impact.",
        ],
        "tips": [],
        "mistakes": ["Changing the key field on a flag already used in code."],
    },
    "content": {
        "title": "Content Hub guide",
        "intro": "Jump to Control Room tools or Django Admin for each content domain.",
        "steps": [
            "Products — catalog, pricing, and publishing (Control Room + Admin for media).",
            "Documentation — articles, videos, downloads, and categories (Control Room).",
            "CMS pages / heroes — homepage and landing content (Admin).",
            "Blog & marketing — posts, events, case studies (Admin).",
            "Leads & demos — review submissions in Ops → Demo Requests.",
        ],
        "tips": ["Admin opens in a new tab — use it for screenshots, videos, and FAQs."],
        "mistakes": ["Expecting pricing tiers to appear without running seed_products or creating plans."],
    },
    "documentation": {
        "title": "Documentation guide",
        "intro": "Manage public help content at /docs/ without Django Admin.",
        "steps": [
            "Create categories first to organize articles, videos, and downloads.",
            "Add articles for guides, FAQs, installation steps, and release notes.",
            "Add videos with a YouTube/Vimeo URL or embed code — they appear on /docs/videos/.",
            "Upload downloads (PDFs, SDKs) — files are served from /docs/downloads/.",
            "Check Is published before expecting content on the live site.",
            "Use View public docs or View live on an article to preview.",
        ],
        "tips": [
            "Run seed_documentation from Platform Setup to populate starter content.",
            "Link articles to a product to filter docs when visitors browse by product.",
        ],
        "mistakes": [
            "Saving articles as drafts and wondering why /docs/ looks empty.",
            "Creating downloads without uploading a file.",
        ],
    },
    "doc_category_form": {
        "title": "Documentation category",
        "intro": "Categories group related articles, videos, and downloads.",
        "steps": [
            "Name and slug identify the category on /docs/categories/.",
            "Optionally link to a product so docs filter by product slug.",
            "Set sort_order to control display order (lower = first).",
        ],
        "tips": [],
        "mistakes": ["Deleting a category that still has articles attached."],
    },
    "doc_article_form": {
        "title": "Documentation article",
        "intro": "Long-form help content shown at /docs/<slug>/.",
        "steps": [
            "Choose article type (guide, FAQ, installation, release note, etc.).",
            "Write excerpt for cards and body for the full page (Markdown supported).",
            "Assign a category and optional product for filtering.",
            "Enable Is published and save — use View live to preview.",
        ],
        "tips": ["Featured articles may appear on the docs homepage."],
        "mistakes": ["Duplicate slugs — each article slug must be unique."],
    },
    "doc_video_form": {
        "title": "Documentation video",
        "intro": "Tutorial videos linked from /docs/videos/.",
        "steps": [
            "Paste a video_url (YouTube/Vimeo) or embed_code for custom players.",
            "Set duration_minutes for display on listing cards.",
            "Assign category and product, then publish.",
        ],
        "tips": [],
        "mistakes": ["Publishing without either video_url or embed_code."],
    },
    "doc_download_form": {
        "title": "Documentation download",
        "intro": "Upload files for visitors to download from /docs/downloads/.",
        "steps": [
            "Upload the file (PDF, ZIP, etc.) and choose file type.",
            "Add title, description, and optional version label.",
            "Publish when ready — file replaces previous upload on edit.",
        ],
        "tips": [],
        "mistakes": ["Forgetting to upload a file on create."],
    },
    "products": {
        "title": "Products guide",
        "intro": "Manage your product catalog, publishing, and ChurchHub links from here.",
        "steps": [
            "Click Add product or Edit to set name, slug, descriptions, and hero image.",
            "Enable Is published and Is featured to show on the homepage.",
            "Set Demo URL and Register URL for ChurchHub (mychurch.zreta.com/contact/ and /apply/).",
            "Open Manage on a product → Pricing plans to create Starter / Pro / Enterprise tiers.",
            "Upload screenshots, templates, and videos via Django Admin (linked from product detail).",
            "Use View public page to preview /products/your-slug/ before sharing.",
        ],
        "tips": [
            "If no pricing appears, go to Platform Setup and run seed_products, then edit currencies in pricing.",
            "Slug must match URL — churchhub → /products/churchhub/.",
        ],
        "mistakes": [
            "Saving a product as draft (not published) and expecting it on the homepage.",
            "Uploading only one screenshot — the gallery needs items with the correct Kind set.",
        ],
    },
    "product_form": {
        "title": "Product editor guide",
        "intro": "Core catalog fields — pricing and media are managed on the product detail page.",
        "steps": [
            "Basics — name, slug, category, tagline, status (use GA when live), accent color.",
            "Publishing — is_published, is_featured, sort_order (lower = first), hero image.",
            "Links — Demo URL, Register URL, external app URL for ChurchHub buttons.",
            "After save you land on the product detail page — add pricing plans next.",
        ],
        "tips": ["Hero image appears at the top of the public product page."],
        "mistakes": ["Changing slug after sharing links — old URLs will 404 unless you add a redirect."],
    },
    "product_detail": {
        "title": "Product activity & next steps",
        "intro": "Track demos and subscriptions, then finish pricing and media setup.",
        "steps": [
            "Click Manage pricing plans to add tiers, currencies, and feature bullets.",
            "Open Admin links for screenshots (set Kind = Template or Screenshot) and videos.",
            "View public page and pricing page to verify buttons and plans display correctly.",
            "Review demo requests here or in Ops → Demo Requests.",
        ],
        "tips": [
            "Pricing page URL: /products/<slug>/pricing/ — only visible when at least one plan is published.",
        ],
        "mistakes": ["Creating plans but leaving is_published unchecked on the plan."],
    },
    "product_pricing": {
        "title": "Pricing plans guide",
        "intro": "Plans appear on /products/<slug>/pricing/ when published with at least one price tier.",
        "steps": [
            "Click Add pricing plan — name it Starter, Pro, or Enterprise.",
            "Set billing interval (monthly/annual) and mark one plan as Popular if desired.",
            "Add a Pricing tier with currency (GHS, USD), region (global), and amount.",
            "Add plan features as bullet lines shown on the pricing card.",
            "Check Is published on the plan, save, then preview the public pricing page.",
        ],
        "tips": [
            "Use Contact sales (no amount) for Enterprise tiers — enables Contact Sales button.",
            "To change currency, edit the tier row — do not create duplicate tiers for the same currency.",
        ],
        "mistakes": [
            "Saving a plan without any pricing tier — page shows Contact Sales only.",
            "Forgetting to publish the plan after creating it.",
        ],
    },
    "product_pricing_form": {
        "title": "Editing a pricing plan",
        "intro": "Each plan needs at least one tier (currency + amount) to show a price.",
        "steps": [
            "Fill plan name and billing interval first.",
            "Under tiers, set currency to GHS or USD and enter the numeric amount.",
            "Add feature bullets — one per row, included/excluded toggles strikethrough.",
            "Save and click View pricing page to confirm display.",
        ],
        "tips": [],
        "mistakes": ["Leaving amount empty on a non-contact-sales plan."],
    },
    "setup": {
        "title": "Platform Setup guide",
        "intro": "One-click seeds populate demo content — safe to re-run; existing records may update.",
        "steps": [
            "Run seed_products first if pricing plans or catalog entries are missing.",
            "Run seed_control_room for navigation menus and platform settings.",
            "Run seed_cms for homepage sections and hero content.",
            "Use Run all only on a fresh install or when you intentionally want to refresh seeds.",
        ],
        "tips": ["After seeding products, edit ChurchHub URLs and currencies in Control Room."],
        "mistakes": ["Running seeds on production with real customer data without reviewing impact."],
    },
    "changelog": {
        "title": "Change Log guide",
        "intro": "Audit trail of actions taken in Control Room.",
        "steps": [
            "Filter mentally by area (products, platform_settings, navigation, etc.).",
            "Use alongside Ops activity logs for full operational history.",
        ],
        "tips": [],
        "mistakes": [],
    },
    "team": {
        "title": "Team & Access guide",
        "intro": "Invite staff, assign roles, and control who can access Control Room and Operations.",
        "steps": [
            "Only Platform Owners and Platform Admins can manage team members.",
            "Enter email, choose a role, and send invitation — the invitee receives a secure link.",
            "Pending invitations can be revoked before they are accepted.",
            "Open a staff member to assign additional roles or remove roles.",
            "Staff with Control Room access must enroll in MFA after accepting an invite.",
        ],
        "tips": [
            "Run promote_platform_owner for the first bootstrap owner account.",
            "If invite email fails, configure SMTP under Platform Ops.",
        ],
        "mistakes": [
            "Inviting the same email twice — revoke the old invite first.",
            "Removing Platform Owner role without another superuser available.",
        ],
    },
    "platform_ops": {
        "title": "Platform Ops guide",
        "intro": "Owner-only tools for outbound email and pulling GitHub updates on the server.",
        "steps": [
            "Enable custom SMTP and enter host, port, username, password, and from address.",
            "Send a test email to yourself before inviting staff.",
            "Use Pull latest from GitHub to run git pull, migrate, and collectstatic.",
            "Restart Gunicorn after deploy: sudo systemctl restart marketing-site",
        ],
        "tips": [
            "Grant manage_platform_operations permission to another role if a non-owner should access this page.",
            "Leave SMTP password blank when saving to keep the existing stored password.",
        ],
        "mistakes": [
            "Using file-based email backend without EMAIL_FILE_PATH in .env.",
            "Expecting Gunicorn to restart automatically — that still requires sudo on the VPS.",
        ],
    },
    "team_user": {
        "title": "Managing a team member",
        "intro": "View roles and assign or remove access for an individual staff user.",
        "steps": [
            "Review currently assigned roles and their descriptions.",
            "Use Assign role to add Platform Admin, Support Agent, or Billing Admin.",
            "Remove roles the user no longer needs — permissions sync automatically.",
        ],
        "tips": ["Staff flag controls Control Room / Operations access."],
        "mistakes": ["Removing all roles but leaving staff access enabled without purpose."],
    },
}


def get_page_help(key: str) -> dict | None:
    return PAGE_HELP.get(key)
