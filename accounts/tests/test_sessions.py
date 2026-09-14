from django.contrib.auth import get_user_model
from django.contrib.sessions.backends.db import SessionStore as DBSessionStore
from django.test import TestCase, override_settings

from accounts.models import UserSession
from accounts.services.sessions import delete_django_session, revoke_other_sessions, revoke_session


User = get_user_model()


class SessionRevocationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="owner",
            email="owner@example.com",
            password="TestPass123!",
        )

    def _create_tracked_session(self, session_key):
        return UserSession.objects.create(
            user=self.user,
            session_key=session_key,
            ip_address="127.0.0.1",
            user_agent="test",
            device_label="Test",
            is_current=False,
        )

    def test_delete_django_session_removes_db_session(self):
        store = DBSessionStore()
        store["marker"] = "alive"
        store.save()
        key = store.session_key
        self.assertTrue(DBSessionStore().exists(key))

        delete_django_session(key)
        self.assertFalse(DBSessionStore().exists(key))

    def test_revoke_other_sessions_deletes_django_sessions(self):
        current = DBSessionStore()
        current["who"] = "current"
        current.save()

        other = DBSessionStore()
        other["who"] = "other"
        other.save()

        self._create_tracked_session(current.session_key)
        UserSession.objects.filter(session_key=current.session_key).update(is_current=True)
        self._create_tracked_session(other.session_key)

        revoke_other_sessions(self.user, current.session_key)

        self.assertTrue(DBSessionStore().exists(current.session_key))
        self.assertFalse(DBSessionStore().exists(other.session_key))
        self.assertFalse(
            UserSession.objects.filter(session_key=other.session_key, revoked_at__isnull=True).exists()
        )

    @override_settings(SESSION_ENGINE="django.contrib.sessions.backends.cache")
    def test_delete_django_session_works_with_cache_engine(self):
        from django.contrib.sessions.backends.cache import SessionStore as CacheSessionStore

        store = CacheSessionStore()
        store["marker"] = "cached"
        store.save()
        key = store.session_key
        self.assertTrue(CacheSessionStore().exists(key))

        delete_django_session(key)
        self.assertFalse(CacheSessionStore().exists(key))

    def test_revoke_session_skips_current_key(self):
        store = DBSessionStore()
        store["who"] = "keep"
        store.save()
        tracked = self._create_tracked_session(store.session_key)

        result = revoke_session(self.user, tracked.pk, current_session_key=store.session_key)
        self.assertIsNotNone(result)
        self.assertTrue(DBSessionStore().exists(store.session_key))
