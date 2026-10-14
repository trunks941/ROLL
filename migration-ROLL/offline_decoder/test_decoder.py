#!/usr/bin/env python3
"""Fixture checks for exploratory decoding, not PLC behavioral validation."""
import unittest
import re
from pathlib import Path
import decode_mc5 as mc5


class DecoderFixtures(unittest.TestCase):
    def test_inline_16_bit_immediate_and_alignment(self):
        data=bytes.fromhex('3004fffe6500')
        row=mc5.primitive(data,0)
        self.assertEqual((row['size'],row['value'],row['operand']),(4,65534,'KF -2'))
        self.assertEqual(mc5.primitive(data,4)['command'],'BE')

    def test_32_bit_immediate_is_six_bytes(self):
        data=bytes.fromhex('3840123456786500')
        row=mc5.primitive(data,0)
        self.assertEqual((row['size'],row['value'],row['operand']),(6,0x12345678,'DH 12345678'))
        self.assertEqual(mc5.primitive(data,6)['command'],'BE')
        add=mc5.primitive(bytes.fromhex('6005fedcba98'),0)
        self.assertEqual((add['size'],add['value']),(6,0xfedcba98))

    def test_timer_bcd_and_base(self):
        # 0x2123 means 123 ticks at 1s base, not decimal 8483 ticks.
        row=mc5.primitive(bytes.fromhex('30022123'),0)
        self.assertEqual((row['size'],row['operand']),(4,'KT 123.2'))
        self.assertNotIn('INVALID_KT_BCD_OR_BASE',row['issues'])
        invalid=mc5.primitive(bytes.fromhex('30024abc'),0)
        self.assertIn('INVALID_KT_BCD_OR_BASE',invalid['issues'])

    def test_kz_bcd_is_not_binary_value(self):
        row=mc5.primitive(bytes.fromhex('30010345'),0)
        self.assertEqual(row['operand'],'KZ 345')

    def test_io_area_and_bit_masks(self):
        # Output-area mask is more specific than otherwise matching input mask.
        out=mc5.primitive(bytes.fromhex('dca0'),0)
        self.assertEqual((out['command'],out['operand'] ),('=','A 32.4'))
        inp=mc5.primitive(bytes.fromhex('c520'),0)
        self.assertEqual((inp['command'],inp['operand']),('U','E 32.5'))
        self.assertEqual(out['issues'],[])

    def test_whole_word_advance_for_bad_14bit_table_entry(self):
        row=mc5.primitive(bytes.fromhex('5f046500'),0)
        self.assertEqual(row['size'],2)
        self.assertIn('TABLE_NONWORD_BITS:14',row['issues'])
        self.assertEqual(mc5.primitive(bytes.fromhex('5f046500'),2)['command'],'BE')

    def test_fb_declarations_consume_six_bytes_each(self):
        data=bytes.fromhex('707008608400000000162d0b')+b'SWAP    '+bytes([2,32])+b'INPU'+bytes([8,32])+b'OUTP'+bytes.fromhex('6500')
        start,pars=mc5.fb_declarations(data)
        self.assertEqual(start,32)
        self.assertEqual([(p['name'],p['type'],p['format']) for p in pars], [('INPU','E','W'),('OUTP','A','W')])
        self.assertEqual(mc5.primitive(data,start,pars)['command'],'BE')

    def test_fb_call_span_skips_argument_words(self):
        pars=[dict(name='INPU',type='E',format='W'),dict(name='OUTP',type='A',format='W')]
        data=bytes.fromhex('3d602d03122532326500')
        rows=mc5.decode_body(data,0,[],{'FB96':pars})
        self.assertEqual([r['offset'] for r in rows],[0,8])
        self.assertEqual(rows[0]['size'],8)
        self.assertEqual(rows[0]['argument_span_words'],2)
        self.assertEqual([a['value'] for a in rows[0]['arguments']],['MW 37','DW 50'])
        self.assertEqual(rows[0]['issues'],[])
        self.assertEqual(rows[1]['command'],'BE')

    def test_invalid_call_parameter_count_explicit_and_aligned(self):
        pars=[dict(name='X',type='E',format='W')]
        rows=mc5.decode_body(bytes.fromhex('3d602d03122532326500'),0,[],{'FB96':pars})
        self.assertIn('CALL_ARGUMENT_COUNT_MISMATCH:2:1',rows[0]['issues'])
        self.assertEqual(rows[-1]['offset'],8)

    def test_signed_jump_from_jump_own_word(self):
        # At byte4, -1 word lands on byte2; not after the instruction.
        data=bytes.fromhex('000065002dff')
        rows=mc5.decode_body(data,0,[],{})
        self.assertEqual(rows[2]['jump_words_signed'],-1)
        self.assertEqual(rows[2]['jump_target_offset'],2)
        self.assertTrue(rows[2]['jump_boundary_ok'])

    def test_jump_into_immediate_explicitly_reported(self):
        rows=mc5.decode_body(bytes.fromhex('2d0230406500'),0,[],{})
        self.assertEqual(rows[0]['jump_target_offset'],4)
        self.assertFalse(rows[0]['jump_boundary_ok'])
        self.assertIn('JUMP_TARGET_NOT_INSTRUCTION_BOUNDARY',rows[0]['issues'])
        self.assertEqual(mc5.primitive(bytes.fromhex('2d0230406500'),4)['command'],'BE')

    def test_unknown_word_retained_without_claimed_semantics(self):
        data=bytes.fromhex('78086500')
        rows=mc5.decode_body(data,0,[],{})
        self.assertEqual(rows[0]['command'],'UNKNOWN')
        self.assertEqual(rows[0]['raw_hex'],'7808')
        self.assertEqual(rows[1]['command'],'BE')

    def test_kc_preserves_file_order_and_flags_native_comparison(self):
        row=mc5.primitive(bytes.fromhex('30104142'),0)
        self.assertEqual(row['operand'],"KC 'AB'")
        self.assertIn('KC_BYTE_ORDER_NATIVE_COMPARISON_REQUIRED',row['issues'])

    def test_legacy_s5_equal_and_unequal_labels(self):
        # Lexical checks only. Siemens S5 !=F is equality, not Python !=.
        self.assertEqual(mc5.primitive(bytes.fromhex('2180'),0)['command'],'!=F')
        self.assertEqual(mc5.primitive(bytes.fromhex('2160'),0)['command'],'><F')


class SuppliedProgramRegressions(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw=(mc5.BASE/'originals/s5/s5/1998_07_03/04201@ST.S5D').read_bytes()
        cls.directory=mc5.read_csv(mc5.BASE/'analysis/s5-program-blocks.csv')
        cls.blocks={r['kind']+r['number']:cls.raw[int(r['offset']):int(r['offset'])+int(r['bytes'])] for r in cls.directory}
        cls.interfaces={name:mc5.fb_declarations(data)[1] for name,data in cls.blocks.items() if name.startswith('FB')}

    def test_nine_fb105_create_db_operands_match_native_step5(self):
        # Independently read native FB105RLS.INI: STEP 5 word offsets are
        # relative to the ten-byte block header; bytes in S5D include it.
        # Native uses English G DB; this decoder uses German E DB.
        native_expected=[(0x0018,15),(0x0041,19),(0x0069,41),
                         (0x006e,51),(0x0078,205),(0x007f,210),
                         (0x0084,211),(0x008b,60),(0x0090,213)]
        native=(mc5.BASE/'native_verification/FB105-native.txt').read_text(encoding='utf-8')
        native_actual=[(int(offset,16),int(target)) for offset,target in
                       re.findall(r'^([0-9A-F]{4})\s+:G\s+DB\s+(\d+)\b',native,re.MULTILINE)]
        self.assertEqual(native_actual,native_expected)
        data=self.blocks['FB105']; start,pars=mc5.fb_declarations(data)
        rows=mc5.decode_body(data,start,pars,self.interfaces)
        creates=[r for r in rows if r['raw_hex'].startswith('7805')]
        self.assertEqual(len(creates),len(native_actual))
        for r,(native_word_offset,target) in zip(creates,native_expected):
            block_offset=10+2*native_word_offset
            self.assertEqual(r['offset'],block_offset)
            self.assertEqual(data[block_offset:block_offset+4],
                             bytes.fromhex('7805')+target.to_bytes(2,'big'))
            self.assertEqual((r['command'],r['operand_area'],r['operand'],r['size']),
                             ('E','DB',f'DB {target}',4))
            self.assertEqual(r['issues'],[])
            following=next(row for row in rows if row['offset']==block_offset+4)
            self.assertEqual((following['command'],following['operand']),('BLD','130'))

    def test_eight_fb96_arguments_match_independent_byte_review(self):
        data=self.blocks['FB92']; start,pars=mc5.fb_declarations(data)
        rows=mc5.decode_body(data,start,pars,self.interfaces)
        calls=[r for r in rows if r['command']=='SPA' and r['operand']=='FB 96']
        self.assertEqual(len(calls),8)
        self.assertEqual([r['offset'] for r in calls],list(range(468,525,8)))
        self.assertTrue(all(r['size']==8 and not r['issues'] for r in calls))
        self.assertEqual([r['arguments'][0]['value'] for r in calls],[f'MW {n}' for n in range(37,52,2)])
        self.assertEqual([r['arguments'][1]['value'] for r in calls],[f'DW {n}' for n in range(50,58)])

    def test_program_coverage_and_only_documented_jump_overlap(self):
        failures=[]; count=0; backward=0; interpreted=0; total=0
        for b in self.directory:
            name=b['kind']+b['number']
            if b['kind'] not in ('OB','PB','FB') or b['assembler_flag']=='True': continue
            data=self.blocks[name]
            start,pars=mc5.fb_declarations(data) if b['kind']=='FB' else (10,[])
            rows=mc5.decode_body(data,start,pars,self.interfaces)
            self.assertEqual(sum(r['size'] for r in rows),len(data)-start)
            self.assertFalse(any(r['command']=='UNKNOWN' for r in rows))
            interpreted+=1; total+=len(data)-start
            for r in rows:
                if 'jump_target_offset' in r:
                    count+=1; backward+=r['jump_words_signed']<0
                    if not r['jump_boundary_ok']: failures.append((name,r['offset'],r['jump_target_offset']))
        self.assertEqual((interpreted,total,count,backward),(44,18252,178,6))
        self.assertEqual(failures,[('FB51',1046,1050)])


if __name__=='__main__': unittest.main(verbosity=2)
