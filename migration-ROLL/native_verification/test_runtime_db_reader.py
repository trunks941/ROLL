#!/usr/bin/env python3
"""Independent conversion examples and incomplete/corrupt-printout controls."""
import re
import unittest
from read_runtime_db_listings import ROOT, bcd_count, kt_ms, parse_printout


class RuntimeDBTests(unittest.TestCase):
    def setUp(self):
        self.raw=(ROOT/'originals/step5-native/DB15ROLS.INI').read_bytes()

    def test_counter_values_are_BCD_instead_of_binary_hex(self):
        self.assertEqual(bcd_count(0x0020),20)
        self.assertEqual(bcd_count(0x0014),14)
        self.assertNotEqual(bcd_count(0x0014),int('0014',16))

    def test_KT_bases_cover_short_and_long_intervals(self):
        self.assertEqual(kt_ms(0x0002),20)
        self.assertEqual(kt_ms(0x1010),1000)
        self.assertEqual(kt_ms(0x3180),1800000)
        self.assertEqual(kt_ms(0x3360),3600000)

    def test_unused_or_bad_BCD_is_rejected(self):
        for word in [0xffff,0x0abc]:
            with self.assertRaises(AssertionError):bcd_count(word)
        for word in [0xffff,0x3a60]:
            with self.assertRaises(AssertionError):kt_ms(word)

    def test_empty_132_marker_is_not_a_data_word(self):
        result,_=parse_printout(self.raw,15)
        self.assertEqual(len(result['words']),132)
        self.assertEqual(result['words'][-1],dict(dw=131,raw_hex='0000'))
        self.assertEqual(result['block_bytes'],274)

    def test_missing_word_is_rejected(self):
        changed=re.sub(rb'^\s*10:\s+KH\s*=\s*FFFF;\r?\n',b'',self.raw,flags=re.MULTILINE)
        self.assertNotEqual(changed,self.raw)
        with self.assertRaises(AssertionError):parse_printout(changed,15)

    def test_duplicate_word_is_rejected(self):
        changed=self.raw.replace(b'    42:     KH = FFFF;',b'    42:     KH = FFFF;\r\n    42:     KH = FFFF;',1)
        self.assertNotEqual(changed,self.raw)
        with self.assertRaises(AssertionError):parse_printout(changed,15)

    def test_wrong_block_identity_is_rejected(self):
        with self.assertRaises(AssertionError):parse_printout(self.raw,19)


if __name__=='__main__':unittest.main(verbosity=2)
