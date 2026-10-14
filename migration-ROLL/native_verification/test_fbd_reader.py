#!/usr/bin/env python3
"""Independent fixture checks and negative controls for the ASCII FBD reader."""
import re
import unittest
from compare_fbd_listings import ROOT, Diagram, aliases_from, canon, atom, signatures, select_native_block, native_fbd_actions


def fixture(filename,network):
    text=(ROOT/'originals/step5-native'/filename).read_bytes().decode('cp850')
    pieces=re.split(r'^Segment\s+(\d+)[^\r\n]*',text,flags=re.MULTILINE)
    bodies={int(pieces[i]):pieces[i+1] for i in range(1,len(pieces),2)}
    return bodies[network],aliases_from(text)


class NativeFixtureTests(unittest.TestCase):
    def test_independent_manual_conveyor_condition(self):
        body,aliases=fixture('PB16ROLS.INI',4)
        condition=canon('AND',canon('OR',atom('M 20.4'),atom('M 20.5')),atom('E 0.1'),atom('M 190.6'))
        self.assertEqual(Diagram(body,aliases).actions(),[('=','M 74.4',condition,None)])

    def test_gate_change_is_detected(self):
        body,aliases=fixture('PB16ROLS.INI',1)
        before=Diagram(body,aliases).actions()
        after=Diagram(body.replace('! & !','!>=1!',1),aliases).actions()
        self.assertNotEqual(signatures(before),signatures(after))

    def test_input_inversion_is_detected(self):
        body,aliases=fixture('PB16ROLS.INI',4)
        changed=body.replace('-HAND    ---!','-HAND    --O!',1)
        self.assertNotEqual(body,changed)
        self.assertNotEqual(signatures(Diagram(body,aliases).actions()),signatures(Diagram(changed,aliases).actions()))

    def test_timer_type_change_is_detected(self):
        body,aliases=fixture('PB13ROLS.INI',4)
        before=Diagram(body,aliases).actions()
        after=Diagram(body.replace('T!-!0','0!-!T',1),aliases).actions()
        self.assertEqual(before[0][0],'SE')
        self.assertEqual(after[0][0],'SA')
        self.assertNotEqual(signatures(before),signatures(after))

    def test_counter_preset_change_is_detected(self):
        body,aliases=fixture('PB13ROLS.INI',49)
        before=Diagram(body,aliases).actions()
        after=Diagram(body.replace('KC 500','KC 501',1),aliases).actions()
        self.assertEqual(before[-1][3],('COUNTER_PRESET',500))
        self.assertEqual(after[-1][3],('COUNTER_PRESET',501))
        self.assertNotEqual(signatures(before),signatures(after))

    def test_vertical_branch_feeds_both_destinations(self):
        body,aliases=fixture('PB13ROLS.INI',43)
        actions=Diagram(body,aliases).actions()
        self.assertEqual({x[1] for x in actions},{'M 63.7','A 24.5'})
        self.assertEqual(actions[0][2],actions[1][2])

    def test_unknown_symbol_fails(self):
        body,aliases=fixture('PB16ROLS.INI',4)
        with self.assertRaises(AssertionError):
            Diagram(body.replace('-T-ARBST','-UNKNOWN',1),aliases).actions()

    def test_combined_printout_selects_only_PB51(self):
        text=(ROOT/'originals/step5-native/PB51ROLS.INI').read_bytes().decode('cp850')
        selected,scope=select_native_block(text,'PB51')
        self.assertEqual(re.findall(r'^Segment\s+(\d+)',selected,re.M),[str(n) for n in range(1,9)])
        self.assertEqual(set(re.findall(r'LEN=(\d+)',selected)),{'79'})
        self.assertEqual(scope['source_byte_start'],0)
        self.assertEqual(scope['other_blocks_in_source'],['PB52'])

    def test_combined_printout_selects_PB52_after_ANSI_control(self):
        raw=(ROOT/'originals/step5-native/PB51ROLS.INI').read_bytes()
        selected,scope=select_native_block(raw.decode('cp850'),'PB52')
        self.assertGreater(scope['source_byte_start'],0)
        self.assertEqual(re.findall(r'^Segment\s+(\d+)',selected,re.M),[str(n) for n in range(1,17)])
        self.assertEqual(set(re.findall(r'LEN=(\d+)',selected)),{'173'})
        self.assertEqual(raw[scope['source_byte_start']:scope['source_byte_end']].decode('cp850'),selected)

    def test_absent_block_is_rejected(self):
        text=(ROOT/'originals/step5-native/PB51ROLS.INI').read_bytes().decode('cp850')
        with self.assertRaises(AssertionError):select_native_block(text,'PB53')

    def test_graphical_output_and_terminal_BE_are_both_read(self):
        body,aliases=fixture('PB21ROLS.INI',46)
        condition=canon('AND',atom('M 100.0'),atom('E 6.5'))
        self.assertEqual(native_fbd_actions(body,aliases),[('=','A 17.5',condition,None),('BE','',None,None)])

    def test_missing_BE_changes_the_ordered_action_list(self):
        body,aliases=fixture('PB21ROLS.INI',46)
        changed=re.sub(r'^\s*:BE\s*$', '', body, flags=re.MULTILINE)
        self.assertNotEqual(body,changed)
        self.assertNotEqual(native_fbd_actions(body,aliases),native_fbd_actions(changed,aliases))

    def test_BE_before_graphical_actions_is_rejected(self):
        body,aliases=fixture('PB21ROLS.INI',46)
        changed=':BE\n'+re.sub(r'^\s*:BE\s*$', '', body, flags=re.MULTILINE)
        with self.assertRaises(AssertionError):native_fbd_actions(changed,aliases)


if __name__=='__main__':unittest.main(verbosity=2)
