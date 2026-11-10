#!/usr/bin/env python3
"""Network policy regressions; all DNS and opener I/O is mocked."""

import importlib.util
import io
import socket
import unittest
from contextlib import redirect_stderr
from pathlib import Path
from unittest.mock import patch
from urllib.response import addinfourl


SCRIPT = (Path(__file__).resolve().parents[1] / "skills" / "gtm-leak-check"
          / "scripts" / "check.py")
SPEC = importlib.util.spec_from_file_location("leak_check_fetch", SCRIPT)
check = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(check)


class FetchPolicy(unittest.TestCase):
    def setUp(self):
        self.opened = []
        self.responses = {}
        self.addresses = {}
        self.read_sizes = []
        self.dns = self.enterContext(patch("socket.getaddrinfo", side_effect=self.resolve))
        # Keep urllib's real redirect/error dispatch, replacing only transport I/O.
        self.enterContext(patch("urllib.request.OpenerDirector._open", autospec=True,
                                side_effect=self.open_response))

    def resolve(self, host, port, *args, **kwargs):
        return [(socket.AF_INET6 if ":" in ip else socket.AF_INET,
                 socket.SOCK_STREAM, socket.IPPROTO_TCP, "", (ip, port))
                for ip in self.addresses.get(host, ["93.184.216.34"])]

    def open_response(self, opener, request, data):
        url = request.full_url
        self.opened.append(url)
        status, headers, body = self.responses.get(url, (200, {}, b"public page"))
        response = addinfourl(io.BytesIO(body), headers, url, status)
        response.msg = "mock response"
        read = response.read

        def bounded_read(size=-1):
            self.read_sizes.append(size)
            return read(size)

        response.read = bounded_read
        return response

    def test_hostile_homepage_links_use_origin_defaults(self):
        for href in (
            "http://127.0.0.1/pricing", "http://169.254.169.254/careers",
            "http://localhost/jobs", "http://internal.example/pricing",
            "file:///etc/passwd", "file:///etc/passwd?pricing",
            "ftp://scan.example/pricing", "data:text/plain,pricing",
            "https://unrelated.example/pricing",
            "https://scan.example.evil.example/pricing",
        ):
            with self.subTest(href=href):
                self.opened.clear()
                self.addresses["internal.example"] = ["10.0.0.5"]
                self.responses["https://scan.example/"] = (
                    200, {}, f'<a href="{href}">Pricing careers</a>'.encode())
                result = check.fetch_domain("scan.example")
                self.assertNotIn(href, self.opened)
                self.assertEqual(result["pricing_url"], "https://scan.example/pricing")
                self.assertEqual(result["careers_url"], "https://scan.example/careers")

    def test_same_site_links_are_fetched(self):
        for href in ("/pricing", "/plans/team", "https://scan.example/pricing",
                     "https://www.scan.example/pricing",
                     "https://shop.scan.example/pricing"):
            with self.subTest(href=href):
                self.opened.clear()
                self.responses["https://scan.example/"] = (
                    200, {}, f'<a href="{href}">Pricing</a>'.encode())
                result = check.fetch_domain("scan.example")
                expected = check.urljoin("https://scan.example/", href)
                self.assertEqual(result["pricing_url"], expected)
                self.assertIn(expected, self.opened)

    def test_www_homepage_can_link_to_apex(self):
        self.responses["https://www.scan.example/"] = (
            200, {}, b'<a href="https://scan.example/plans">Plans</a>')
        check.fetch_domain("www.scan.example")
        self.assertIn("https://scan.example/plans", self.opened)

    def test_non_http_schemes_never_open(self):
        for url in ("file:///etc/passwd", "ftp://scan.example/pricing",
                    "data:text/plain,pricing"):
            with self.subTest(url=url):
                self.assertEqual(check.fetch(url, required=False), (0, ""))
                with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as err:
                    check.fetch(url)
                self.assertEqual(err.exception.code, 2)
        self.assertEqual(self.opened, [])
        self.dns.assert_not_called()

    def test_non_public_literal_addresses_never_open(self):
        for ip in ("127.0.0.1", "10.0.0.5", "172.16.0.1", "192.168.1.1",
                   "169.254.169.254", "0.0.0.0", "224.0.0.1", "240.0.0.1",
                   "[::1]", "[fc00::1]", "[fe80::1]", "[::]", "[ff02::1]",
                   "[::ffff:127.0.0.1]"):
            with self.subTest(ip=ip):
                self.assertEqual(check.fetch(f"http://{ip}/", required=False), (0, ""))
        self.assertEqual(self.opened, [])

    def test_any_non_public_dns_answer_blocks_request(self):
        for addresses in (["10.0.0.5"], ["93.184.216.34", "10.0.0.5"],
                          ["93.184.216.34", "::1"], []):
            with self.subTest(addresses=addresses):
                self.addresses["internal.scan.example"] = addresses
                self.assertEqual(check.fetch("https://internal.scan.example/pricing",
                                             required=False), (0, ""))
        self.assertEqual(self.opened, [])

    def test_required_private_homepage_exits_two(self):
        self.addresses["scan.example"] = ["10.0.0.5"]
        with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as err:
            check.fetch_domain("scan.example")
        self.assertEqual(err.exception.code, 2)
        self.assertEqual(self.opened, [])

    def test_redirect_targets_are_checked_before_opening(self):
        source = "https://scan.example/pricing"
        self.addresses["internal.example"] = ["10.0.0.5"]
        for target in ("http://127.0.0.1/pricing", "http://169.254.169.254/careers",
                       "http://internal.example/jobs", "file:///etc/passwd",
                       "ftp://scan.example/pricing", "data:text/plain,pricing"):
            for status in (301, 302, 303, 307, 308):
                with self.subTest(target=target, status=status):
                    self.opened.clear()
                    self.responses[source] = (status, {"location": target}, b"")
                    self.assertEqual(check.fetch(source, required=False), (0, ""))
                    self.assertEqual(self.opened, [source])

    def test_every_redirect_hop_is_checked(self):
        first, second = "https://scan.example/", "https://other.example/"
        self.responses[first] = (302, {"location": second}, b"")
        self.responses[second] = (302, {"location": "http://127.0.0.1/"}, b"")
        self.assertEqual(check.fetch(first, required=False), (0, ""))
        self.assertEqual(self.opened, [first, second])

    def test_public_and_relative_redirects_still_work(self):
        self.responses["https://scan.example/"] = (302, {"location": "/pricing"}, b"")
        self.responses["https://scan.example/pricing"] = (
            302, {"location": "https://other.example/plans"}, b"")
        self.assertEqual(check.fetch("https://scan.example/"), (200, "public page"))
        self.assertEqual(self.opened, ["https://scan.example/", "https://scan.example/pricing",
                                       "https://other.example/plans"])

    def test_redirects_stop_after_five_hops(self):
        for number in range(8):
            self.responses[f"https://scan.example/{number}"] = (
                302, {"location": f"/{number + 1}"}, b"")
        self.assertEqual(check.fetch("https://scan.example/0", required=False), (0, ""))
        self.assertEqual(len(self.opened), 6)

    def test_status_and_response_size_preserved(self):
        for status in (200, 404):
            with self.subTest(status=status):
                self.responses["https://scan.example/"] = (
                    status, {}, b"x" * (check.MAX_BYTES + 10))
                code, body = check.fetch("https://scan.example/")
                self.assertEqual(code, status)
                self.assertEqual(len(body), check.MAX_BYTES)
        self.assertEqual(self.read_sizes, [check.MAX_BYTES + 1, check.MAX_BYTES])

    def test_www_and_jobs_fallbacks_preserved(self):
        self.responses["https://scan.example/"] = (404, {}, b"")
        self.responses["https://www.scan.example/careers"] = (404, {}, b"")
        result = check.fetch_domain("scan.example")
        self.assertEqual(result["page_url"], "https://www.scan.example/")
        self.assertEqual(result["careers_url"], "https://www.scan.example/jobs")


if __name__ == "__main__":
    unittest.main()
