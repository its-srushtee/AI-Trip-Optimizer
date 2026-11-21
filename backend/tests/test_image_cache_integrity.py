"""Unit tests for image cache integrity, resolution fallback, and invalidation."""
import unittest

from app.database.session import SessionLocal
from app.models.destination import Destination
from app.models.image_cache import ImageCache
from app.services.image_service import (
    _norm,
    get_fallback_image,
    invalidate_cached_image,
    is_valid_image_url,
    resolve,
)


class TestImageCacheIntegrity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db = SessionLocal()

    @classmethod
    def tearDownClass(cls):
        cls.db.close()

    def test_target_destinations_resolution(self):
        """Verify image resolution for Cape Town, Vancouver, Varanasi, Palawan, Goa, Kerala."""
        targets = ["Cape Town", "Vancouver", "Varanasi", "Palawan", "Goa", "Kerala"]
        for t in targets:
            with self.subTest(destination=t):
                res = resolve(self.db, t, allow_remote=True)
                url = res.get("url")
                self.assertTrue(url, f"Resolution for {t} returned empty URL")
                self.assertTrue(
                    is_valid_image_url(url),
                    f"Resolved URL '{url}' for {t} is not valid",
                )
                self.assertIn(
                    res.get("source"),
                    ["cache", "catalogue", "provider"],
                    f"Unexpected source for {t}: {res.get('source')}",
                )

    def test_goa_resolves_local_catalogue(self):
        """Goa has a bundled local photo and should resolve locally without hitting providers."""
        res = resolve(self.db, "Goa", allow_remote=False)
        self.assertEqual(res.get("provider"), "local")
        self.assertEqual(res.get("source"), "catalogue")
        self.assertEqual(res.get("url"), "/images/goa.jpg")

    def test_repeated_lookup_reuses_cache(self):
        """Repeated lookups for cached destinations must hit the database cache with zero network calls."""
        for t in ["Cape Town", "Vancouver", "Varanasi", "Palawan"]:
            with self.subTest(destination=t):
                res = resolve(self.db, t, allow_remote=False)
                self.assertEqual(res.get("source"), "cache")
                self.assertTrue(is_valid_image_url(res.get("url")))

    def test_invalid_cache_does_not_serve_broken_url(self):
        """If a cache row holds an invalid/missing local file path, resolve() must not return it."""
        test_key = _norm("test_invalid_cache_destination")
        bad_url = "/images/fake_missing_image_xyz999.jpg"

        cached = self.db.get(ImageCache, test_key)
        if not cached:
            cached = ImageCache(query=test_key, url=bad_url, provider="local")
            self.db.add(cached)
        else:
            cached.url = bad_url
        self.db.commit()

        # Remote disabled: should fall back to valid hero image, never the bad_url
        res = resolve(self.db, "test_invalid_cache_destination", allow_remote=False)
        self.assertNotEqual(res.get("url"), bad_url)
        self.assertTrue(is_valid_image_url(res.get("url")))

        # Clean up
        self.db.delete(cached)
        self.db.commit()

    def test_cache_invalidation_updates_record_without_deleting_valid_entries(self):
        """Invalidating a cached item should refresh or apply fallback without touching other valid records."""
        initial_count = self.db.query(ImageCache).count()
        test_key = _norm("test_refresh_item_sample")

        # Invalidate / refresh
        result = invalidate_cached_image(self.db, "test_refresh_item_sample")
        self.assertIn(result.get("status"), ["refreshed", "fallback_applied"])
        self.assertTrue(is_valid_image_url(result.get("url")))

        # Verify other valid cache records remain intact
        current_count = self.db.query(ImageCache).count()
        self.assertGreaterEqual(current_count, initial_count)

        # Clean up test row
        row = self.db.get(ImageCache, test_key)
        if row:
            self.db.delete(row)
            self.db.commit()

    def test_fallback_hero_is_always_available(self):
        """A valid local fallback hero image must always exist on disk."""
        fb = get_fallback_image()
        self.assertTrue(is_valid_image_url(fb))
        self.assertEqual(fb, "/images/hero.jpg")

    def test_no_hardcoded_destination_mappings(self):
        """Image resolution uses generic normalization and dynamic discovery, not hardcoded if-statements."""
        import inspect
        from app.services import image_service
        source = inspect.getsource(image_service.resolve)
        self.assertNotIn("if name == 'Cape Town'", source)
        self.assertNotIn("if name == 'Goa'", source)
        self.assertNotIn("if name == 'Vancouver'", source)


if __name__ == "__main__":
    unittest.main()
