from common import navigation as nav_constants
from control_room.services import _merge_missing_nav_items, get_navigation, invalidate_navigation_cache


from django.test import TestCase


class ControlRoomNavigationMergeTests(TestCase):
    def test_merge_inserts_missing_platform_ops_link(self):
        stale = [
            {"label": "Super Dashboard", "url_name": "control_room:dashboard", "icon": "layout-dashboard"},
            {"section": "Platform"},
            {"label": "Site Settings", "url_name": "control_room:settings", "icon": "settings"},
        ]
        merged = _merge_missing_nav_items(stale, nav_constants.CONTROL_ROOM_NAV)
        urls = [item.get("url_name") for item in merged if item.get("url_name")]
        self.assertIn("control_room:platform_ops", urls)

    def test_get_navigation_always_includes_platform_ops(self):
        invalidate_navigation_cache("control_room")
        urls = [item.get("url_name") for item in get_navigation("control_room") if item.get("url_name")]
        self.assertIn("control_room:platform_ops", urls)
