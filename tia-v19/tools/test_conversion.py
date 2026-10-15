#!/usr/bin/env python3
"""Independent MC5 register execution vs the emitted PB SCL subset.

Executes generated Boolean/accumulator/coil statements in Python, not in TIA.
The timer/counter model is shared; tests cannot establish S7 timing or compilation.
"""
from pathlib import Path
import copy
import hashlib
import json
import math
import random
import re
import unittest
import generate as gen


class Model:
    def __init__(self, seed=1):
        rng = random.Random(seed)
        self.bits = {area: {(b, bit): bool(rng.getrandbits(1)) for b in range(256 if area == 'M' else 128) for bit in range(8)} for area in ('M', 'E', 'A')}
        self.timer = [{'remaining': rng.randrange(0, 10000), 'base': 100, 'mode': rng.randrange(2), 'previous': bool(rng.getrandbits(1)), 'q': bool(rng.getrandbits(1))} for _ in range(128)]
        self.counter = [{'value': rng.randrange(1000), 'set': bool(rng.getrandbits(1)), 'up': bool(rng.getrandbits(1)), 'down': bool(rng.getrandbits(1))} for _ in range(128)]
        self.db = {15: [65535] * 132, 19: [65535] * 132}
        for row in gen.csv_rows(gen.OLD / 'native_verification/runtime-db-words.csv'):
            self.db[int(row['runtime_DB'][2:])][int(row['runtime_DW'])] = int(row['supplied_hex'], 16)

    def get_m(self, FirstByte, Width):
        value = 0
        for n in range(Width // 8):
            value = (value << 8) | sum((1 << bit) for bit in range(8) if self.bits['M'][FirstByte + n, bit])
        return value

    def set_m_word(self, first, value):
        for bit in range(8):
            self.bits['M'][first, bit] = bool(value & (1 << (bit + 8)))
            self.bits['M'][first + 1, bit] = bool(value & (1 << bit))

    def fb69(self):
        self.set_m_word(240, 0x2005 if self.bits['M'][240, 0] and self.bits['M'][240, 1] else 0x1005)

    def read(self, operand, db=0, boolean=False):
        area, index = operand.split()
        if area in ('M', 'E', 'A'):
            return self.bits[area][tuple(map(int, index.split('.')))]
        if area == 'T':
            state = self.timer[int(index)]
            return state['q'] if boolean else math.ceil(state['remaining'] / state['base'])
        if area == 'Z':
            value = self.counter[int(index)]['value']
            return value != 0 if boolean else value
        if area in ('MB', 'MW'):
            return self.get_m(int(index), 8 if area == 'MB' else 16)
        if area == 'DW':
            return self.db[db][int(index)]
        if area == 'KT':
            return gen.kt_word(index)
        if area == 'KZ':
            return gen.kt_word(index + '.0')
        return int(index, {'KH': 16, 'KM': 2}.get(area, 10)) & 65535

    @staticmethod
    def bcd(value):
        digits = [(value >> shift) & 15 for shift in (8, 4, 0)]
        assert all(d <= 9 for d in digits), hex(value)
        return 100 * digits[0] + 10 * digits[1] + digits[2]

    def action(self, command, operand, signal, preset):
        area, index = operand.split()
        signal = bool(signal)
        if area == 'T':
            timer = self.timer[int(index)]
            if command == 'R':
                if signal:
                    timer.update(remaining=0, q=False)
                return
            mode = 0 if command == 'SE' else 1
            trigger = (signal and not timer['previous']) if mode == 0 else (not signal and timer['previous'])
            if trigger:
                base = [10, 100, 1000, 10000][preset >> 12]
                timer.update(base=base, remaining=self.bcd(preset) * base)
            timer['mode'] = mode
            if (mode == 0 and not signal) or (mode == 1 and signal):
                timer['remaining'] = 0
            timer['q'] = (signal and timer['remaining'] <= 0) if mode == 0 else (signal or timer['remaining'] > 0)
            timer['previous'] = signal
        elif area == 'Z':
            counter = self.counter[int(index)]
            if command == 'R':
                if signal:
                    counter['value'] = 0
                return
            edge = {'S': 'set', 'ZV': 'up', 'ZR': 'down'}[command]
            if signal and not counter[edge]:
                if command == 'S':
                    counter['value'] = self.bcd(preset)
                elif command == 'ZV':
                    counter['value'] = min(999, counter['value'] + 1)
                else:
                    counter['value'] = max(0, counter['value'] - 1)
            counter[edge] = signal
        else:
            target = tuple(map(int, index.split('.')))
            if command == '=':
                self.bits[area][target] = signal
            elif signal:
                self.bits[area][target] = command == 'S'


def signed(word):
    return word - 65536 if word >= 32768 else word


def execute_mc5(model, rows):
    # Direct registers and a parentheses stack, independent of symbolic Logic.
    rlo, first, pending, db, a1, a2 = False, True, False, 0, 0, 0
    stack = []
    for row in rows:
        c, o = row['command'], row['operand']
        if c in ('BLD', 'NOP0'):
            continue
        if c in ('U(', 'O('):
            stack.append((rlo, first, pending, c[0]))
            rlo, first, pending = False, True, False
        elif c == ')':
            value = rlo or pending
            rlo, first, pending, operation = stack.pop()
            rlo = value if first else ((rlo and value) if operation == 'U' else (rlo or value))
            first = False
        elif c in ('U', 'UN', 'O', 'ON'):
            if not o:
                assert c == 'O'
                pending = pending or rlo
                rlo, first = False, True
                continue
            value = model.read(o, db, boolean=True)
            if c in ('UN', 'ON'):
                value = not value
            rlo = value if first else ((rlo and value) if c[0] == 'U' else (rlo or value))
            first = False
        elif c == 'L':
            a2, a1 = a1, model.read(o, db)
        elif c in ('!=F', '><F', '>F', '<F', '<=F', '>=F'):
            x, y = signed(a2), signed(a1)
            value = {'!=F': x == y, '><F': x != y, '>F': x > y, '<F': x < y, '<=F': x <= y, '>=F': x >= y}[c]
            rlo = value if first else (rlo and value)
            first = False
        elif c in ('=', 'S', 'R', 'SE', 'SA', 'ZR', 'ZV'):
            rlo = rlo or pending
            pending, first = False, True
            model.action(c, o, rlo, a1)
        elif c == 'A':
            db = int(o.split()[1])
        elif c == 'SPA':
            assert o == 'FB 69'
            model.fb69()
        elif c == 'BE':
            return
        else:
            raise AssertionError((c, o))


def eval_scl(model, expression, env):
    # Only the controlled output of generate.py is accepted here.
    expression = re.sub(r'"ROLL_State"\.M\[(\d+), (\d+)\]', lambda m: f'bits["M"][({m[1]}, {m[2]})]', expression)
    expression = re.sub(r'"ROLL_IO"\.(Input|Output)\[(\d+), (\d+)\]', lambda m: f'bits["{"E" if m[1] == "Input" else "A"}"][({m[2]}, {m[3]})]', expression)
    expression = re.sub(r'"ROLL_State"\.S5Timers\[(\d+)\]\.Q', lambda m: f'timer[{m[1]}]["q"]', expression)
    expression = re.sub(r'"ROLL_State"\.S5Counters\[(\d+)\]\.Value', lambda m: f'counter[{m[1]}]["value"]', expression)
    expression = expression.replace('"ROLL_GetM"', 'getm').replace('"ROLL_GetDW"', 'getdw').replace('"ROLL_TimerValue"', 'gett')
    expression = expression.replace('WORD_TO_INT', 'signed').replace('INT_TO_WORD', 'int')
    expression = re.sub(r'W#16#([0-9A-F]+)', r'0x\1', expression)
    expression = expression.replace(' := ', '=').replace('#', '').replace('<>', '!=')
    expression = re.sub(r'(?<![<>=!])=(?!=)', '==', expression)
    # Restore Python keyword arguments after transforming SCL comparison signs.
    expression = re.sub(r'(FirstByte|Width|DbNumber|Index|Number)==', r'\1=', expression)
    for old, new in [('AND', 'and'), ('OR', 'or'), ('NOT', 'not'), ('TRUE', 'True'), ('FALSE', 'False')]:
        expression = re.sub(r'\b' + old + r'\b', new, expression)
    scope = dict(env, bits=model.bits, timer=model.timer, counter=model.counter, getm=model.get_m, getdw=lambda DbNumber, Index: model.db[DbNumber][Index], gett=lambda Number: model.read(f'T {Number}'), signed=signed, int=int)
    return eval(expression, {'__builtins__': {}}, scope)


def execute_scl(model, source):
    body = source.split('\nBEGIN\n', 1)[1].split('\nEND_FUNCTION', 1)[0]
    env = {'r': False, 'a1': 0, 'a2': 0, 'activeDataBlock': 0, 'comparisonResults': [False] * 256}
    for raw in body.splitlines():
        line = raw.strip()
        if not line or line.startswith('//'):
            continue
        if line == 'RETURN;':
            return
        if line == '"ROLL_FB69"();':
            model.fb69()
            continue
        call = re.fullmatch(r'"ROLL_(Timer|Counter)Op"\(Number := (\d+), Operation := (\d+), Signal := #r, Preset := #a1\);', line)
        if call:
            commands = {0: 'SE', 1: 'SA', 2: 'R'} if call[1] == 'Timer' else {0: 'S', 1: 'R', 2: 'ZV', 3: 'ZR'}
            model.action(commands[int(call[3])], ('T' if call[1] == 'Timer' else 'Z') + ' ' + call[2], env['r'], env['a1'])
            continue
        conditional = re.fullmatch(r'IF #r THEN (.*) END_IF;', line)
        if conditional:
            if not env['r']:
                continue
            line = conditional[1]
        lhs, rhs = line.rstrip(';').split(' := ', 1)
        value = eval_scl(model, rhs, env)
        if lhs.startswith('#comparisonResults['):
            env['comparisonResults'][int(lhs[len('#comparisonResults['):-1])] = value
        elif lhs.startswith('#'):
            env[lhs[1:]] = value
        else:
            target = re.fullmatch(r'"(ROLL_State|ROLL_IO)"\.(M|Input|Output)\[(\d+), (\d+)\]', lhs)
            assert target, lhs
            model.bits[{'M': 'M', 'Input': 'E', 'Output': 'A'}[target[2]]][int(target[3]), int(target[4])] = value


def same(test, a, b):
    test.assertEqual(a.bits, b.bits)
    test.assertEqual(a.timer, b.timer)
    test.assertEqual(a.counter, b.counter)
    test.assertEqual(a.db, b.db)


class ConversionTests(unittest.TestCase):
    def test_all_22_pbs_against_direct_mc5_register_execution(self):
        rows = gen.csv_rows(gen.OLD / 'offline_decoder/instructions.csv')
        functions = {name: source for name, source in re.findall(r'FUNCTION "(ROLL_PB\d+)"(.*?END_FUNCTION)', (gen.OUT / 'sources/02-process.scl').read_text(), re.S)}
        self.assertEqual(22, len(functions))
        comparisons = 0
        for name, source in functions.items():
            block = name[5:]
            selected = [x for x in rows if x['block'] == block]
            for seed in range(1, 41):
                with self.subTest(block=block, seed=seed):
                    a = Model(seed)
                    # All timer/counter presets used by the native source are
                    # valid online words or constants; timers can have arbitrary
                    # previous states, as at an intermediate process scan.
                    b = copy.deepcopy(a)
                    execute_mc5(a, selected)
                    execute_scl(b, 'FUNCTION "' + name + '"' + source)
                    same(self, a, b)
                    comparisons += 1
        self.assertEqual(880, comparisons)

    def synthetic(self, pairs, prepare=lambda m: None):
        rows = [{'command': c, 'operand': o, 'network': '1'} for c, o in pairs]
        source, _ = gen.compile_pb('PB999', rows)
        a = Model()
        prepare(a)
        b = copy.deepcopy(a)
        execute_mc5(a, rows)
        execute_scl(b, source)
        same(self, a, b)
        return a

    def test_consecutive_coils_use_stored_rlo_after_source_bit_changes(self):
        a = self.synthetic([('U', 'M 0.3'), ('R', 'M 0.3'), ('S', 'M 0.4'), ('BE', '')], lambda m: m.bits['M'].__setitem__((0, 3), True))
        self.assertFalse(a.bits['M'][0, 3])
        self.assertTrue(a.bits['M'][0, 4])

    def test_multiple_comparisons_snapshot_accumulators(self):
        a = self.synthetic([('L', 'KF +1'), ('L', 'KF +1'), ('!=F', ''), ('O(', ''), ('L', 'KF +2'), ('L', 'KF +3'), ('!=F', ''), (')', ''), ('=', 'M 0.0'), ('BE', '')])
        self.assertTrue(a.bits['M'][0, 0])

    def test_signed_comparison(self):
        a = self.synthetic([('L', 'KF -1'), ('L', 'KF +0'), ('<F', ''), ('=', 'M 0.0'), ('BE', '')])
        self.assertTrue(a.bits['M'][0, 0])

    def test_overlapping_big_endian_words(self):
        m = Model()
        m.set_m_word(240, 0xA581)
        self.assertEqual(0xA5, m.get_m(240, 8))
        self.assertEqual(0x81, m.get_m(241, 8))
        m.set_m_word(241, 0x1234)
        self.assertEqual(0xA512, m.get_m(240, 16))

    def test_two_recipes_and_online_counter_presets(self):
        text = (gen.OUT / 'sources/01-data.scl').read_text()
        self.assertIn('DW[1] := W#16#0020;', text)
        self.assertIn('DW[2] := W#16#0014;', text)
        for seconds in [360, 90, 240, 60, 300, 120, 400]:
            self.assertIn('W#16#' + f'{gen.kt_word(f"{seconds}.2"):04X}', text)

    def test_ob1_writer_order_and_physical_profile(self):
        source = (gen.OUT / 'sources/04-hmi-cycle.scl').read_text().split('FUNCTION "ROLL_Cycle"', 1)[1].split('END_FUNCTION', 1)[0]
        self.assertLess(source.index('"ROLL_PB20"();'), source.index('"ROLL_PB23"();'))
        self.assertLess(source.index('"ROLL_PB16"();'), source.index('"ROLL_PB15"();'))
        io = (gen.OUT / 'sources/03-io.scl').read_text()
        self.assertEqual(128, len(re.findall(r':= %I\d+\.\d', io)))
        self.assertEqual(80, len(re.findall(r'%Q\d+\.\d :=', io)))
        self.assertNotRegex(io, r'%[IQ]1(?:12|13|19|2[0-5])\.')
        self.assertIn('%Q24.4 := #enabled AND "ROLL_IO".Output[24, 4];', io)
        self.assertIn('PhysicalOutputsEnabled : Bool := FALSE;', (gen.OUT / 'sources/00-runtime.scl').read_text())


if __name__ == '__main__':
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(ConversionTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    report = {'test_count': result.testsRun, 'failures': len(result.failures), 'errors': len(result.errors), 'success': result.wasSuccessful(), 'pb_state_comparisons': 880 if result.wasSuccessful() else None, 'tia_compiled': False, 'runtime_scl_executed': False, 'physical_machine_tested': False, 'scope': 'direct MC5 PB registers vs generated PB SCL subset in Python; shared timer/counter model'}
    report['source_sha256'] = {name: hashlib.sha256((gen.OUT / name).read_bytes()).hexdigest() for name in ['sources/02-process.scl', 'sources/04-hmi-cycle.scl', 'ROLL_ALL.scl']}
    (gen.OUT / 'reports/conversion-tests.json').write_text(json.dumps(report, indent=2) + '\n')
    raise SystemExit(0 if result.wasSuccessful() else 1)
