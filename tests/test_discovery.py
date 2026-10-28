import unittest

from tvboot.discovery import Candidate, valid_ipv4, location_from_response, parse_description, default_candidate


class DiscoveryTests(unittest.TestCase):
    def test_only_private_ipv4_targets_are_accepted(self):
        for host in ("192.168.4.8", "10.3.4.5", "172.16.20.30"):
            self.assertTrue(valid_ipv4(host))
        for host in ("127.0.0.1", "8.8.8.8", "172.32.1.1", "192.168.1.1;reboot", "example.org"):
            self.assertFalse(valid_ipv4(host))

    def test_location_must_match_sender_and_use_http(self):
        response = b"HTTP/1.1 200 OK\r\nLOCATION: http://192.168.8.2:49152/description.xml\r\n\r\n"
        self.assertEqual(location_from_response(response, "192.168.8.2"), "http://192.168.8.2:49152/description.xml")
        self.assertIsNone(location_from_response(response, "192.168.8.3"))
        bad = response.replace(b"http://", b"file://")
        self.assertIsNone(location_from_response(bad, "192.168.8.2"))

    def test_vendor_description_produces_a_tv_candidate(self):
        xml = b'<root xmlns="urn:schemas-upnp-org:device-1-0"><device><friendlyName>Living room REDMI TV</friendlyName><manufacturer>Xiaomi</manufacturer></device></root>'
        candidate = parse_description(xml, "192.168.8.2")
        self.assertEqual(candidate.ip, "192.168.8.2")
        self.assertEqual(candidate.name, "Living room REDMI TV")

    def test_non_xiaomi_and_doctype_descriptions_are_ignored(self):
        self.assertIsNone(parse_description(b"<root><friendlyName>Other</friendlyName><manufacturer>Other</manufacturer></root>", "192.168.8.2"))
        hostile = b'<!DOCTYPE root [<!ENTITY x "Xiaomi">]><root><manufacturer>&x;</manufacturer></root>'
        self.assertIsNone(parse_description(hostile, "192.168.8.2"))

    def test_utf16_doctype_cannot_bypass_xml_safety_check(self):
        hostile = '<?xml version="1.0" encoding="utf-16"?><!DOCTYPE root [<!ENTITY x "Xiaomi">]><root><friendlyName>TV</friendlyName><manufacturer>&x;</manufacturer></root>'.encode('utf-16')
        self.assertIsNone(parse_description(hostile, "192.168.8.2"))

    def test_multiple_televisions_are_never_selected_automatically(self):
        one = Candidate("192.168.8.2", "TV one")
        two = Candidate("192.168.8.3", "TV two")
        self.assertEqual(default_candidate([one]), one)
        self.assertIsNone(default_candidate([one, two]))
        self.assertIsNone(default_candidate([]))


if __name__ == "__main__":
    unittest.main()
