#!/usr/bin/env python3
"""Save the manually reviewed PB16 FBD conditions and check its structure.

This does not automatically interpret FBD wiring or execute PLC logic. Boolean
grouping, input inversions, self references, and S/R order were compared
manually with all 34 native networks. The checks below validate identities,
network coverage, lengths and operand sets, not runtime equivalence.
"""
from pathlib import Path
import csv
import hashlib
import json
import re

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
DEFINITIONS = {
    'Z': 'NOT E11.0 AND NOT E11.1 AND NOT E11.2 AND NOT E11.3 AND NOT E11.4 AND NOT E119.6 AND NOT E119.7 AND NOT E120.0 AND NOT E120.1',
    'G': 'M63.1 OR (E13.3 AND Z)',
    'C8': 'E11.1 OR E11.2 OR E11.3 OR E11.4 OR E119.6 OR E119.7 OR E120.0 OR E120.1',
    'C7': 'E11.1 OR E11.2 OR E11.3 OR E11.4 OR E119.6 OR E119.7 OR E120.0',
}
# Recorded from the native diagrams; AND/OR grouping is explicit. These are
# documentation expressions, not SCL, LAD source, or an import into TIA.
REVIEW = '''1;= M73.7;M27.7 AND E0.1 AND M190.5 AND M190.6
2;= M74.2;E124.1 AND E124.4 AND (M20.3 OR M20.5)
3;= M74.1;(M190.6 AND NOT M190.5 AND M74.2) OR (M74.0 AND (M70.2 OR M70.3))
4;= M74.4;(M20.4 OR M20.5) AND E0.1 AND M190.6
5;= M74.5;(E123.6 OR M70.3 OR M70.5 OR M70.6) AND NOT A113.3 AND (M74.0 OR M74.4)
6;= M75.2;Z
7;= M75.3;(M23.1 AND M190.6 AND M75.3) OR M75.2
8;= M75.4;(NOT M75.3 OR M75.2 OR NOT E11.6) AND G AND E12.5 AND M190.6 AND M23.1 AND E0.1
9;= M75.5;G AND E0.1 AND (M74.0 OR (M23.1 AND M190.5 AND NOT M190.6))
10;= M75.6;(M190.6 AND M23.1 AND M75.2 AND E0.1) OR ((M74.0 OR (M23.1 AND M190.5 AND E0.1)) AND NOT E11.0 AND M63.1)
11;= M76.0;M23.0 AND M190.5 AND NOT E11.0 AND E11.6
12;= M76.1;(M23.0 AND M190.6 AND E11.0 AND E11.6) OR (M74.0 AND NOT E11.0)
13;= M76.2;(M76.0 OR M76.1) AND E0.1
14;= M240.0;NOT E12.5 AND NOT E12.1
15;= M77.1;(M23.0 AND M190.6 AND M77.1) OR M240.0
16;= M77.2;(NOT M77.1 OR M240.0 OR NOT E12.7) AND E11.6 AND M190.6 AND M23.0 AND E0.1 AND ((C8 AND NOT E12.1) OR NOT E12.7)
17;= M76.4;(NOT M6.0 AND NOT M6.2 AND C7) OR E11.4
18;= M76.5;M76.4 AND NOT M190.5 AND M190.6 AND M23.0 AND M77.2
19;= M76.6;((M23.0 AND M190.5 AND NOT M190.6) OR M74.0) AND E11.0 AND ((E124.2 AND E124.5) OR M0.4) AND M63.1
20;= M77.0;(M76.5 OR (M76.6 AND (NOT E12.7 OR NOT E12.1))) AND E11.6 AND E0.1
21;= M240.0;(M190.5 AND NOT E11.0 AND NOT E12.5) OR (M190.6 AND E11.0 AND NOT E12.1)
22;= M240.1;C7 AND NOT E12.1
23;= M240.2;E11.0 AND NOT E12.1
24;= M76.7;(M240.0 AND M76.2) OR ((M240.1 OR M240.2) AND M77.0)
25;= M77.3;E12.1 AND E12.7 AND E11.0 AND E124.5 AND NOT M70.2 AND NOT M70.3 AND E0.1 AND NOT A113.3
26;= M77.4;((M22.0 AND M190.5 AND NOT M190.6) OR M74.0) AND M77.3 AND NOT M77.6 AND A113.2
27;= M77.6;M22.0 AND NOT M190.5 AND M190.6 AND M77.3 AND NOT M77.4
28;= M77.7;((NOT M190.5 AND M190.6 AND M22.1 AND E0.1) OR (M74.0 AND M20.2 AND NOT E124.4)) AND E124.1 AND NOT E124.5 AND NOT M70.3
29;= M78.0;((M190.5 AND NOT M190.6 AND M22.1 AND E0.1) OR (M74.0 AND M20.1 AND NOT M15.1)) AND E124.1 AND NOT E124.4 AND NOT M70.3
30;S M78.4 then R M78.4;S: ((M22.3 OR M22.4) AND E0.1 AND M190.6) OR (M74.0 AND E123.5) | R: (M22.3 AND E0.1 AND M190.5 AND NOT A113.3) OR (M74.0 AND NOT E123.4 AND NOT A113.3) OR NOT E0.1
31;= M78.5;(M190.1 OR NOT E123.4) AND NOT E123.5 AND NOT E123.6 AND NOT M9.1 AND NOT M16.0 AND NOT M16.4
32;S M78.6 then R M78.6;S: (M22.4 AND E0.1 AND NOT M190.5 AND M190.6 AND E124.4 AND E124.1 AND NOT M70.3 AND NOT E124.2) OR (M74.0 AND M70.2) | R: (M22.4 AND E0.1 AND M190.5 AND NOT M70.2) OR M70.0 OR (M74.0 AND M20.1 AND NOT M70.2) OR (M74.0 AND M20.2 AND (NOT E124.1 OR NOT E124.4) AND NOT M70.2) OR NOT E0.1
33;S M78.7 then R M78.7;S: (M22.4 AND E0.1 AND M190.5 AND NOT M70.2) OR (M74.0 AND (M20.1 OR (M20.2 AND E124.5)) AND NOT M70.2) | R: M78.6 OR M70.0 OR NOT E0.1
34;BE;Explicit unaddressed BE in the final network
'''


def main():
    raw = (ROOT/'originals/step5-native/PB16ROLS.INI').read_bytes()
    text = raw.decode('cp850')
    assert hashlib.sha256(raw).hexdigest() == '0863b18063b58d0da3fcda158360ea38055ddeb51e8b9aaf5745ab85a1ed2f03'
    assert all(int(n)*2 == 838 for n in re.findall(r'LEN=(\d+)',text))
    assert len(re.findall(r'Page\s+\d+',text)) == 13
    segments = re.split(r'^Segment\s+(\d+)[^\r\n]*',text,flags=re.MULTILINE)
    native_nets = {int(segments[i]):segments[i+1] for i in range(1,len(segments),2)}
    assert list(native_nets)==list(range(1,35))
    with (ROOT/'offline_decoder/instructions.csv').open(encoding='utf-8-sig') as f:
        decoded = [r for r in csv.DictReader(f,delimiter=';') if r['block']=='PB16']
    reviews=[]
    for line in REVIEW.splitlines():
        number, target, condition = line.split(';',2);number=int(number)
        rows=[r for r in decoded if int(r['network'])==number]
        native_operands={f"{ {'F':'M','I':'E','Q':'A'}[area]} {address}" for area,address in
                         re.findall(r'^([FIQ])\s+(\d+\.\d+)\s*=',native_nets[number],re.MULTILINE)}
        code_operands={r['operand'] for r in rows if r['operand'] and r['command']!='BLD'}
        assert native_operands==code_operands,(number,native_operands,code_operands)
        reviews.append(dict(network=number,output_and_order=target,manual_condition=condition,
                            operand_set_check='Match',manual_FBD_logic_review='Match',
                            limit='Manual graph comparison; no native instruction addresses or runtime test'))
    assert len(reviews)==34 and len(decoded)==414
    assert re.search(r'^\s+:BE\s*$',native_nets[34],re.MULTILINE)
    cleaned=re.sub(r'\x1b\[[0-?]*[ -/]*[@-~]','',text).replace('\r\n','\n').replace('\x0c','\n')
    (HERE/'PB16-native.txt').write_text(cleaned,encoding='utf-8')
    with (HERE/'PB16-FBD-network-review.csv').open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(reviews[0]),delimiter=';');writer.writeheader();writer.writerows(reviews)
    result=dict(block='PB16',source_file='PB16ROLS.INI',size_bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),
                method='All 34 native FBD networks manually compared; operand sets checked',
                pages=13,networks=34,block_bytes=838,native_addressed_positions=0,
                offline_positions_in_comparison_context=414,offline_executing_instructions=381,
                networks_manually_compared=34,result='All FBD network logic and operands match.',
                condition_definitions=DEFINITIONS,review_table='PB16-FBD-network-review.csv',
                limitations='Manual comparison of native FBD logic, not instruction-by-instruction native STL confirmation or PLC execution.')
    (HERE/'PB16-comparison.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ['block','pages','networks','result']}))


if __name__=='__main__':
    main()
