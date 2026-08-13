"""Tests for backup foundation helpers."""

import json
import tempfile
from pathlib import Path

from django.test import SimpleTestCase

from core.backup.manifest import (
    is_production_db_name,
    is_safe_backup_filename,
    is_safe_backup_root,
    is_safe_pg_identifier,
    load_manifest,
    normalize_pg_identifier,
    verify_manifest_artifact,
)


class BackupPathSafetyTests(SimpleTestCase):
    def test_rejects_public_media_backup_root(self):
        self.assertFalse(is_safe_backup_root("/var/www/marketing-site/media/backups"))
        self.assertFalse(is_safe_backup_root("media/private"))

    def test_accepts_standard_backup_root(self):
        self.assertTrue(is_safe_backup_root("/var/backups/zreta"))

    def test_rejects_secret_like_filenames(self):
        self.assertFalse(is_safe_backup_filename("db-password-backup.pgdump"))
        self.assertFalse(is_safe_backup_filename(".env.copy"))
        self.assertFalse(is_safe_backup_filename("../../etc/passwd"))
        self.assertTrue(is_safe_backup_filename("marketing-20260813.pgdump"))


class BackupRestoreSafetyTests(SimpleTestCase):
    def test_normalizes_pg_identifiers_case_insensitively(self):
        self.assertEqual(normalize_pg_identifier("Marketing"), "marketing")

    def test_accepts_valid_pg_identifiers(self):
        self.assertTrue(is_safe_pg_identifier("zreta_restore_drill"))
        self.assertTrue(is_safe_pg_identifier("marketing"))

    def test_rejects_invalid_pg_identifiers(self):
        self.assertFalse(is_safe_pg_identifier(""))
        self.assertFalse(is_safe_pg_identifier("bad-name"))
        self.assertFalse(is_safe_pg_identifier("foo'; DROP DATABASE marketing; --"))

    def test_detects_production_db_name_case_insensitively(self):
        self.assertTrue(is_production_db_name("Marketing", "marketing"))
        self.assertTrue(is_production_db_name("marketing", "marketing"))
        self.assertFalse(is_production_db_name("zreta_restore_drill", "marketing"))


class BackupManifestTests(SimpleTestCase):
    def test_verify_manifest_checksum_and_size(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            artifact = root / "marketing-test.pgdump"
            artifact.write_bytes(b"pgdump-test-content")

            manifest_path = root / "manifest.json"
            manifest_path.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "backup_type": "database",
                        "created_at_utc": "2026-08-13T12:00:00Z",
                        "hostname": "test",
                        "app_dir": "/var/www/marketing-site",
                        "database_name": "marketing",
                        "artifact": artifact.name,
                        "size_bytes": artifact.stat().st_size,
                        "sha256": __import__("hashlib").sha256(artifact.read_bytes()).hexdigest(),
                    }
                ),
                encoding="utf-8",
            )

            ok, message = verify_manifest_artifact(manifest_path)
            self.assertTrue(ok, message)

            loaded = load_manifest(manifest_path)
            self.assertEqual(loaded.backup_type, "database")
            self.assertEqual(loaded.database_name, "marketing")

    def test_detects_checksum_mismatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            artifact = root / "marketing-test.pgdump"
            artifact.write_bytes(b"content")

            manifest_path = root / "manifest.json"
            manifest_path.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "backup_type": "database",
                        "created_at_utc": "2026-08-13T12:00:00Z",
                        "hostname": "test",
                        "app_dir": "/var/www/marketing-site",
                        "database_name": "marketing",
                        "artifact": artifact.name,
                        "size_bytes": artifact.stat().st_size,
                        "sha256": "0" * 64,
                    }
                ),
                encoding="utf-8",
            )

            ok, message = verify_manifest_artifact(manifest_path)
            self.assertFalse(ok)
            self.assertIn("checksum", message.lower())

    def test_rejects_path_traversal_artifact(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest_path = root / "manifest.json"
            manifest_path.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "backup_type": "database",
                        "created_at_utc": "2026-08-13T12:00:00Z",
                        "hostname": "test",
                        "app_dir": "/var/www/marketing-site",
                        "database_name": "marketing",
                        "artifact": "../../etc/passwd",
                        "size_bytes": 0,
                        "sha256": "0" * 64,
                    }
                ),
                encoding="utf-8",
            )

            ok, message = verify_manifest_artifact(manifest_path)
            self.assertFalse(ok)
            self.assertIn("unsafe", message.lower())
