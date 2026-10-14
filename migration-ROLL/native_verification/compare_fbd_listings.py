#!/usr/bin/env python3
"""Strict static comparison of the supplied STEP 5 ASCII FBD diagrams.

Reads separate native diagrams and MC5 instruction rows, builds Boolean action
signatures, and compares them. Does not execute timers/counters, PLC scans or
hardware. Unsupported or ambiguous syntax fails instead of being guessed.
This is a reader for these supplied listings, not a general STEP 5 importer.
"""
from pathlib import Path
import csv
import hashlib
import json
import re
from collections import defaultdict

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
PROCESS_FILES={'PB2':'PB2ROLLS.INI','PB3':'PB3ROLLS.INI','PB4':'PB4ROLLS.INI',
       'PB13':'PB13ROLS.INI','PB17':'PB17ROLS.INI','PB18':'PB18ROLS.INI'}
AUTOMATION_FILES={'PB7':'PB7RROLS.INI','PB8':'PB8ROLLS.INI','PB9':'PB9ROLLS.INI',
                  'PB10':'PB10ROLS.INI','PB14':'PB14ROLS.INI','PB15':'PB15ROLS.INI',
                  'PB50':'PB50ROLS.INI','PB51':'PB51ROLS.INI','PB52':'PB51ROLS.INI'}
PLANT_FILES={'PB19':'PB19ROLS.INI','PB20':'PB20ROLS.INI','PB21':'PB21ROLS.INI',
             'PB23':'PB23ROLS.INI','PB24':'PB24ROLS.INI','PB25':'PB25ROLS.INI'}
FILES={**PROCESS_FILES,**AUTOMATION_FILES,**PLANT_FILES}


def read_csv(path):
    with path.open(encoding='utf-8-sig',newline='') as f:
        return list(csv.DictReader(f,delimiter=';'))


def canon(op,*args):
    if op=='NOT':
        return args[0][1] if args[0][0]=='NOT' else ('NOT',args[0])
    if op in ('AND','OR'):
        items=[]
        for arg in args:
            if arg[0]==op:items.extend(arg[1:])
            else:items.append(arg)
        items=sorted(set(items),key=repr)
        return items[0] if len(items)==1 else (op,*items)
    if op=='EQ':args=tuple(sorted(args,key=repr))
    return (op,*args)


def atom(value):
    parts=value.split()
    area=parts[0]
    if area in ('KB','KF','KH','KM','KT','KZ'):
        data=parts[1]
        if area=='KT':return ('TIME',data.zfill(5))
        if area=='KZ':return ('COUNTER_PRESET',int(data))
        base=16 if area=='KH' else 2 if area=='KM' else 10
        return ('NUMBER',int(data,base))
    return ('READ',value)


def expression_text(node):
    if node[0]=='BOOL':return 'TRUE' if node[1] else 'FALSE'
    if node[0]=='READ':return node[1].replace(' ','')
    if node[0]=='NUMBER':return str(node[1])
    if node[0]=='TIME':return 'KT'+node[1]
    if node[0]=='COUNTER_PRESET':return 'KZ'+str(node[1])
    if node[0]=='NOT':return 'NOT '+expression_text(node[1])
    return '('+(' '+node[0]+' ').join(expression_text(x) for x in node[1:])+')'


class Logic:
    def __init__(self):
        self.current=None;self.pending=[];self.fresh=True
    def value(self):
        assert self.current is not None,'Missing RLO'
        return canon('OR',*self.pending,self.current) if self.pending else self.current
    def apply(self,command,arg=None):
        if command=='O' and arg is None:
            self.pending=[self.value()];self.current=None;self.fresh=True
            return
        if self.fresh:
            self.current=arg;self.fresh=False
        else:self.current=canon('AND' if command=='U' else 'OR',self.current,arg)
    def action(self):
        value=self.value();self.pending=[];self.current=value;self.fresh=True
        return value


def mc5_actions(rows):
    logic=Logic();stack=[];actions=[];accu1=accu2=None
    for r in rows:
        c,o=r['command'],r['operand']
        if c in ('BLD','NOP0'):continue
        if c in ('U(','O('):
            stack.append((logic,c[0]));logic=Logic();continue
        if c==')':
            arg=logic.value();logic,command=stack.pop();logic.apply(command,arg);continue
        if c in ('U','UN','O','ON'):
            arg=atom(o) if o else None
            if c in ('UN','ON'):arg=canon('NOT',arg)
            logic.apply(c[0],arg);continue
        if c=='L':accu2,accu1=accu1,atom(o);continue
        if c in ('!=F','><F','>F','<F','<=F','>=F'):
            assert accu1 is not None and accu2 is not None
            logic.apply('U',canon({'!=F':'EQ','><F':'NE','>F':'GT','<F':'LT','<=F':'LE','>=F':'GE'}[c],accu2,accu1));continue
        if c in ('=','S','R','SE','SA','ZR','ZV'):
            condition=logic.action()
            preset=accu1 if c in ('SE','SA') or (c=='S' and o.startswith('Z ')) else None
            actions.append((c,o,condition,preset));continue
        if c=='A' and o.startswith('DB '):actions.append(('OPEN_DB',o,None,None));continue
        if c=='SPA' and o.startswith('FB '):actions.append(('CALL',o,None,None));continue
        if c=='BE':actions.append(('BE','',None,None));continue
        raise AssertionError(('Unsupported MC5 instruction',c,o))
    assert not stack
    return actions


class Diagram:
    def __init__(self,body,aliases):
        # Symbols/legends are not interpreted as diagram wires.
        self.lines=[]
        for line in body.splitlines():
            if re.match(r'^\s*(?:F|FY|FW|I|Q|T|C|FB)\s+\d',line):break
            if 'Page' in line or re.match(r'^PB\s+\d',line):continue
            self.lines.append(line)
        self.aliases=aliases;self.boxes=[];self.cache={}
        for y,line in enumerate(self.lines):
            for m in re.finditer(r'\+-{3,}\+',line):
                left,right=m.start(),m.end()-1
                if y+1>=len(self.lines) or self.char(y+1,left)!='!':continue
                ends=[i for i in range(y+2,len(self.lines)) if self.lines[i][left:right+1]=='+'+'-'*(right-left-1)+'+']
                assert ends,(y,line)
                end=ends[0]
                label=self.lines[y+1][left+1:right].strip()
                box=dict(top=y,bottom=end,left=left,right=right,label=label)
                self.boxes.append(box)
    def char(self,y,x):
        return self.lines[y][x] if 0<=y<len(self.lines) and 0<=x<len(self.lines[y]) else ' '
    def reference(self,text):
        text=text.strip()
        if text.startswith('-'):
            name=text[1:].rstrip()
            assert name in self.aliases,('Unknown diagram symbol',name)
            return atom(self.aliases[name])
        m=re.fullmatch(r'(KT|KC|KB|KF|KH|KM|DW)\s+(.+)',text)
        assert m,('Unknown diagram input',text)
        return atom(('KZ' if m[1]=='KC' else m[1])+' '+m[2].replace(' ',''))
    def wire(self,y,left):
        prefix=self.lines[y][:left]
        invert=prefix.endswith('O')
        if invert:prefix=prefix[:-1]
        # Empty unconnected ports are not PLC operations.
        if not prefix.strip(' -+'):
            if '+' in prefix:
                column=prefix.rfind('+')
                origin=y-1
                while origin>=0 and self.char(origin,column) in ('!','+'):
                    if self.char(origin,column)=='+' and self.char(origin,column-1)=='-':
                        value=self.wire(origin,column)
                        return canon('NOT',value) if invert else value
                    origin-=1
                raise AssertionError(('Unresolved vertical output branch',y,column))
            return None
        x=len(prefix)-1
        while x>=0 and prefix[x] in '-+':x-=1
        if x>=0 and prefix[x]=='!':
            boxes=[b for b in self.boxes if b['right']==x and b['top']<y<b['bottom']]
            assert len(boxes)==1,('Unresolved source box',y,x,prefix)
            value=self.output(boxes[0])
        else:
            token=prefix[:x+1].rstrip()
            value=self.reference(token)
        return canon('NOT',value) if invert else value
    def inputs(self,b):
        inputs=[]
        for y in range(b['top']+1,b['bottom']):
            if self.char(y,b['left'])=='!' and self.char(y,b['left']-1) in '-O':
                value=self.wire(y,b['left'])
                if value is not None:inputs.append((y,self.lines[y][b['left']+1:b['right']].strip(),value))
        return inputs
    def target(self,b):
        if b['label']=='=':
            row=next(y for y in range(b['top']+1,b['bottom']) if self.lines[y][b['right']+1:].strip().startswith('-'))
            return self.reference(self.lines[row][b['right']+1:].strip())[1]
        line=self.lines[b['top']-1]
        token=line[max(0,b['left']-3):].strip()
        # A preceding gate may share the title row. Use the rightmost dash-name.
        names=[name for name in self.aliases if token.endswith('-'+name)]
        assert len(names)==1,('Missing block target',b,token)
        return self.aliases[names[0]]
    def output(self,b):
        key=(b['top'],b['left'])
        if key in self.cache:return self.cache[key]
        label=b['label'];inputs=self.inputs(b)
        if label in ('&','>=1'):
            assert inputs
            value=canon('AND' if label=='&' else 'OR',*(v for _,_,v in inputs))
        elif label in ('!=  F','!= F','><  F','>< F','>   F','> F','<=  F','<= F'):
            assert len(inputs)==2
            comparator={'!=':'EQ','><':'NE','>':'GT','<=':'LE'}[label.split()[0]]
            value=canon(comparator,inputs[0][2],inputs[1][2])
        elif label in ('S','T!-!0','0!-!T','CD'):
            value=atom(self.target(b))
        else:raise AssertionError(('Unsupported diagram box',label,b))
        self.cache[key]=value;return value
    def actions(self):
        actions=[]
        for b in self.boxes:
            label=b['label']
            if label in ('&','>=1') or ' F' in label:
                # STEP 5 may label a gate's output directly instead of drawing
                # a separate assignment box (PB13 network 33).
                for y in range(b['top']+1,b['bottom']):
                    tail=self.lines[y][b['right']+1:]
                    match=re.fullmatch(r'-+[ \t]+(-.+)',tail)
                    if match:
                        actions.append(('=',self.reference(match[1])[1],self.output(b),None))
                continue
            if label=='=':
                inputs=self.inputs(b);assert len(inputs)==1
                actions.append(('=',self.target(b),inputs[0][2],None))
            elif label=='S':
                target=self.target(b)
                for _,port,value in self.inputs(b):
                    assert port in ('S','R   Q'),port
                    actions.append(('S' if port=='S' else 'R',target,value,None))
            elif label in ('T!-!0','0!-!T','CD'):
                target=self.target(b);inputs=self.inputs(b);preset=None
                for _,port,value in inputs:
                    if port.startswith(('TV','CV')):preset=value
                for _,port,value in inputs:
                    if port.startswith(('TV','CV')):continue
                    if label=='CD':command={'CD':'ZR','CU':'ZV','S':'S','R   Q':'R'}[port]
                    else:command={'T!-!0':'SE','0!-!T':'SA','R   Q':'R'}[port]
                    actions.append((command,target,value,preset if command in ('SE','SA','S') else None))
            elif label=='SW PAUSE':actions.append(('CALL','FB 69',None,None))
            else:raise AssertionError(('Unsupported action box',label))
        return actions


def aliases_from(text):
    aliases={}
    for area,address,name in re.findall(r'^\s*(F|FY|FW|I|Q|T|C|FB)\s+(\d+(?:\.\d+)?)\s*=[ \t]*(.*)$',text,re.M):
        area={'F':'M','FY':'MB','FW':'MW','I':'E','Q':'A','C':'Z'}.get(area,area)
        name=name[:8].rstrip();value=area+' '+address
        assert aliases.get(name,value)==value,('Conflicting native symbol',name)
        aliases[name]=value
    return aliases


def native_fbd_actions(body,aliases):
    diagram=Diagram(body,aliases)
    actions=diagram.actions()
    ends=[y for y,line in enumerate(diagram.lines) if re.fullmatch(r'\s*:BE\s*',line)]
    assert len(ends)<=1,'Repeated BE in graphical network'
    if ends:
        assert all(b['bottom']<ends[0] for b in diagram.boxes),'BE precedes graphical actions'
        actions.append(('BE','',None,None))
    return actions


def signatures(actions):
    # Preserve the order of mutations for the same variable (S before R etc.).
    grouped=defaultdict(list)
    for action in actions:grouped[action[1]].append(action)
    return dict(grouped)


def select_native_block(text,block):
    """Select a contiguous block printout while preserving original offsets.

    PB51ROLS.INI contains PB51 and PB52, including repeated page headers.
    The full uploaded file remains the source and hash; offsets below use its
    one-byte CP850 encoding, not a fabricated second original file.
    """
    pattern=r'(?:^|\x0c)(?:\x1b\[[0-?]*[ -/]*[@-~])*(PB|FB|OB)\s+(\d+)[^\r\n]*LEN=(\d+)'
    headers=list(re.finditer(pattern,text,re.MULTILINE));assert headers,'Missing block header'
    runs=[]
    for h in headers:
        identity=h[1]+h[2]
        if not runs or runs[-1]['block']!=identity:
            if runs:runs[-1]['end']=h.start()
            runs.append(dict(block=identity,start=h.start(),end=len(text),header_lengths=[]))
        runs[-1]['header_lengths'].append(int(h[3]))
    chosen=[r for r in runs if r['block']==block]
    assert len(chosen)==1,('Missing or repeated non-contiguous block',block)
    r=chosen[0]
    return text[r['start']:r['end']],dict(source_byte_start=r['start'],source_byte_end=r['end'],
                                      other_blocks_in_source=sorted({x['block'] for x in runs if x['block']!=block}))


def compare(block,filename,decoded,directory):
    path=ROOT/'originals/step5-native'/filename;raw=path.read_bytes()
    text,scope=select_native_block(raw.decode('cp850'),block)
    assert all(2*int(n)==int(directory[block]['bytes']) for n in re.findall(r'LEN=(\d+)',text))
    parts=re.split(r'^Segment\s+(\d+)[^\r\n]*',text,flags=re.M)
    nets={int(parts[i]):parts[i+1] for i in range(1,len(parts),2)}
    assert len(nets)==(len(parts)-1)//2,'Repeated network number in selected printout'
    rows=[r for r in decoded if r['block']==block]
    assert list(nets)==list(range(1,1+max(int(r['network']) for r in rows)))
    aliases=aliases_from(text);reviews=[];errors=[]
    for number,body in nets.items():
        expected=mc5_actions([r for r in rows if int(r['network'])==number])
        try:
            method='Static native FBD action-expression comparison'
            if re.search(r'^([0-9A-F]{4})\s*:',body,re.M):
                from compare_addressed_listings import parse_addressed
                parsed=parse_addressed(f'Segment {number}\n'+body,int(directory[block]['bytes']))
                expected_rows=[r for r in rows if int(r['network'])==number]
                assert [r['block_byte_offset'] for r in parsed]==[int(r['offset']) for r in expected_rows]
                for n,p in zip(parsed,expected_rows):
                    assert (n['command'],n['operand'],n['network'])==(p['command'],p['operand'],int(p['network']))
                native=mc5_actions([{'command':r['command'],'operand':r['operand']} for r in parsed])
                method='All native STL positions in this network compared'
            else:native=native_fbd_actions(body,aliases)
            assert native==expected,('Ordered action mismatch',native,expected)
            reviews.append(dict(network=number,result='Match',method=method,
                                actions=[dict(command=c,target=t,condition=expression_text(v) if v else '',
                                              condition_ast=v,preset=expression_text(p) if p else '') for c,t,v,p in native]))
        except (AssertionError,KeyError,StopIteration,ValueError) as e:
            errors.append(dict(network=number,error=str(e)))
    return dict(block=block,source_file=filename,size_bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),
                source_scope=scope,
                pages=len(re.findall(r'Page\s+\d+',text)),block_bytes=int(directory[block]['bytes']),
                networks=len(nets),matched=len(reviews),reviews=reviews,errors=errors,
                native_addressed_STL_positions=len(re.findall(r'^[0-9A-F]{4}\s*:',text,re.M)),
                offline_positions_in_context=len(rows),offline_executing_instructions=sum(r['command']!='BLD' for r in rows),
                method='Static native FBD action-expression comparison; addressed STL fragments compared separately',
                limitations='Boolean logic, read operands, timer/counter operation types and presets are compared statically. No timer/counter execution, PLC scan simulation, TIA compilation or hardware test.')


def main():
    import sys
    decoded=read_csv(ROOT/'offline_decoder/instructions.csv')
    directory={r['kind']+r['number']:r for r in read_csv(ROOT/'analysis/s5-program-blocks.csv')}
    files={'PB16':'PB16ROLS.INI'} if '--check-pb16' in sys.argv else FILES
    results=[compare(b,f,decoded,directory) for b,f in files.items()]
    for r in results:
        print(json.dumps({k:r[k] for k in ['block','networks','matched','errors']},ensure_ascii=False))
    assert all(not r['errors'] and r['matched']==r['networks'] for r in results), 'Incomplete FBD comparison'
    if '--check-pb16' in sys.argv:return
    for r in results:
        block=r['block'];r['result']='All native network action expressions and operands match.'
        (HERE/f'{block}-comparison.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
        raw,_=select_native_block((ROOT/'originals/step5-native'/r['source_file']).read_bytes().decode('cp850'),block)
        cleaned=re.sub(r'\x1b\[[0-?]*[ -/]*[@-~]','',raw).replace('\r\n','\n').replace('\x0c','\n')
        (HERE/f'{block}-native.txt').write_text(cleaned,encoding='utf-8')
        table=[dict(network=n['network'],method=n['method'],result=n['result'],
                    action_order=' | '.join(a['command']+' '+a['target'] for a in n['actions']),
                    conditions=' | '.join(a['command']+' '+a['target']+': '+a['condition'] for a in n['actions']),
                    presets=' | '.join(a['target']+': '+a['preset'] for a in n['actions'] if a['preset'])) for n in r['reviews']]
        with (HERE/f'{block}-network-comparison.csv').open('w',encoding='utf-8-sig',newline='') as f:
            writer=csv.DictWriter(f,fieldnames=list(table[0]),delimiter=';');writer.writeheader();writer.writerows(table)
    for name,subset in [('process-control-comparison.json',[r for r in results if r['block'] in PROCESS_FILES]),
                        ('automation-control-comparison.json',[r for r in results if r['block'] in AUTOMATION_FILES]),
                        ('plant-control-comparison.json',[r for r in results if r['block'] in PLANT_FILES]),
                        ('FBD-blocks-comparison.json',results)]:
        summary=dict(blocks=[{k:v for k,v in r.items() if k not in ('reviews','errors')} for r in subset],
                     total_networks=sum(r['networks'] for r in subset),
                     native_addressed_STL_positions=sum(r['native_addressed_STL_positions'] for r in subset),
                     total_offline_positions_in_context=sum(r['offline_positions_in_context'] for r in subset),
                     total_offline_executing_instructions=sum(r['offline_executing_instructions'] for r in subset))
        (HERE/name).write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
    # This diagnostic snapshot was used only during reader development.
    (HERE/'partia4-FBD-work-in-progress.json').unlink(missing_ok=True)


if __name__=='__main__':main()
