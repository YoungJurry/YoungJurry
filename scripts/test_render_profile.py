"""Offline checks for generated covers and public-project selection."""
import unittest
import xml.etree.ElementTree as ET

from render_profile import latest_project, render


class CoverTests(unittest.TestCase):
    def test_filters_profile_private_fork_and_archived(self):
        base = {"name": "pi-web-lite", "pushed_at": "2026-09-01T08:00:00Z"}
        repos = [base, dict(base, name="youngjurry", pushed_at="2026-09-06T08:00:00Z")]
        for flag in ("private", "fork", "archived"):
            repos.append(dict(base, name="excluded", **{flag: True}, pushed_at="2026-09-07T08:00:00Z"))
        self.assertEqual(latest_project(repos), ("pi-web-lite", "2026.09.01"))

    def test_empty_and_missing_push_dates(self):
        self.assertEqual(latest_project([]), ("Exploring new ideas", ""))
        self.assertEqual(latest_project([{"name": "empty"}]), ("Exploring new ideas", ""))

    def test_truncation(self):
        name, _ = latest_project([{"name": "x" * 60, "pushed_at": "2026-09-01T00:00:00Z"}])
        self.assertEqual(len(name), 30)

    def test_both_themes_valid_and_accessible(self):
        for theme in ("dark", "light"):
            svg = render([{"name": 'x<&"', "pushed_at": "2026-09-01T00:00:00Z"}], theme)
            doc = ET.fromstring(svg)
            self.assertEqual(doc.attrib["viewBox"], "0 0 1000 440")
            self.assertIn("prefers-reduced-motion", svg)
            self.assertIn("data:font/ttf;base64,", svg)
            self.assertNotIn("ENERGY", svg)
            self.assertLess(len(svg.encode()), 350_000)


if __name__ == "__main__":
    unittest.main()
