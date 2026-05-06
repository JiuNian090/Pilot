#!/usr/bin/env python3
"""Pilot 知识库 HTML 生成器 v2"""
import re, json, os

HERE = os.path.dirname(os.path.abspath(__file__))
HTML = os.path.join(HERE, "index.html")
FILES = {"words":"单词本.md","knowledge":"知识本.md","guide":"指南本.md","abbreviations":"缩略词.md"}

def rd(name):
    with open(os.path.join(HERE,FILES[name]),encoding='utf-8') as f:
        return f.read()

def parse_words(text):
    secs,cur=[],None
    for line in text.split('\n'):
        if line.startswith('## '):
            if cur:secs.append(cur)
            t=line.strip('# ').strip()
            cur={"id":"w-"+re.sub(r'[^\w\u4e00-\u9fff]+','-',t).strip('-').lower(),"label":t,"items":[],"empty":True}
        elif cur and '|' in line and line.strip().startswith('|') and line.strip().endswith('|'):
            cells=[c.strip() for c in line.strip('|').split('|')]
            if len(cells)>=2 and cells[0] and cells[0] not in('单词/词组','英文','术语','编码','单词') and not re.match(r'^[\s\-:]+$',cells[0]):
                cur['items'].append([cells[0],cells[1] if len(cells)>1 else '',cells[2] if len(cells)>2 else ''])
                cur['empty']=False
    if cur:secs.append(cur)
    return secs

def parse_knowledge(text):
    secs,cur,sub,cl=[],None,None,[]
    for line in text.split('\n'):
        if line.startswith('## '):
            if cur:
                if sub:sub["html"]=''.join(cl);cur.setdefault('subs',[]).append(sub);sub=None;cl=[]
                secs.append(cur)
            t=line.strip('# ').strip()
            if t=='目录':cur=None;continue  # skip 目录
            cur={"id":"k-"+re.sub(r'[^\w\u4e00-\u9fff]+','-',t).strip('-').lower(),"label":t,"subs":[]}
        elif cur and line.startswith('### '):
            if sub:sub["html"]=''.join(cl);cur['subs'].append(sub);cl=[]
            st=line.strip('# ').strip()
            sk=cur['id']+'-'+re.sub(r'[^\w\u4e00-\u9fff]+','-',st).strip('-').lower()
            sub={"id":sk,"label":st,"html":''}
        elif sub:cl.append(line+'\n')
        elif cur and '*暂无内容*' in line:cur["empty"]=True
    if cur:
        if sub:sub["html"]=''.join(cl);cur.setdefault('subs',[]).append(sub)
        secs.append(cur)
    return secs

def parse_abbreviation(text):
    secs, cur, sub = [], None, None
    for line in text.split('\n'):
        if line.startswith('## '):
            if cur:
                if sub: cur.setdefault('subs',[]).append(sub); sub = None
                if not cur.get('subs') and not cur.get('items'): cur['empty'] = True
                secs.append(cur)
            t = line.strip('# ').strip()
            cur = {"id": "a-"+re.sub(r'[^\w\u4e00-\u9fff]+','-',t).strip('-').lower(), "label": t, "empty": True}
            if 'items' in cur: del cur['items']
            sub = None
        elif cur and line.startswith('### '):
            if sub: cur.setdefault('subs',[]).append(sub)
            st = line.strip('# ').strip()
            sk = cur['id']+'-'+re.sub(r'[^\w\u4e00-\u9fff]+','-',st).strip('-').lower()
            sub = {"id": sk, "label": st, "items": []}
        elif cur and '|' in line and line.strip().startswith('|') and line.strip().endswith('|'):
            cells = [c.strip() for c in line.strip('|').split('|')]
            if len(cells)>=2 and cells[0] and cells[0] not in ('缩写','缩写/代码') and not re.match(r'^[\s\-:]+$',cells[0]):
                it = [cells[0], cells[1] if len(cells)>1 else '', cells[2] if len(cells)>2 else '']
                if sub:
                    sub['items'].append(it)
                    cur['empty'] = False
                else:
                    cur.setdefault('items',[]).append(it)
                    cur['empty'] = False
    if cur:
        if sub: cur.setdefault('subs',[]).append(sub)
        if not cur.get('subs') and not cur.get('items'): cur['empty'] = True
        secs.append(cur)
    return secs

def parse_guide(text):
    secs,cur,cl=[],None,[]
    for line in text.split('\n'):
        if line.startswith('## '):
            if cur:cur["content"]=''.join(cl);secs.append(cur);cl=[]
            t=line.strip('# ').strip()
            if t=='目录':cur=None;continue  # skip 目录
            cur={"id":"g-"+re.sub(r'[^\w\u4e00-\u9fff]+','-',t).strip('-').lower(),"label":t,"content":''}
        elif cur:cl.append(line+'\n')
    if cur:cur["content"]=''.join(cl);secs.append(cur)
    return secs

def md2html(md):
    l,o=md.split('\n'),[]
    i=0
    while i<len(l):
        ln=l[i]
        if '|' in ln and ln.strip().startswith('|') and ln.strip().endswith('|'):
            cells=[c.strip() for c in ln.strip('|').split('|')]
            o.append('<div class="tbl-wrap"><table class="info-tbl"><tr>'+''.join(f'<th>{h}</th>' for h in cells)+'</tr>')
            i+=1
            while i<len(l) and '|' in l[i] and l[i].strip().startswith('|'):
                cs=[c.strip() for c in l[i].strip('|').split('|')]
                if re.match(r'^[\s\-:]+$',cs[0]):i+=1;continue  # skip separator
                o.append('<tr>'+''.join(f'<td>{c}</td>' for c in cs)+'</tr>')
                i+=1
            o.append('</table></div>')
            continue
        s=ln.strip()
        if s.startswith('#### '):o.append(f'<h4>{s[5:]}</h4>')
        elif s.startswith('### '):o.append(f'<h3>{s[4:]}</h3>')
        elif s.startswith('> '):o.append(f'<blockquote>{s[2:]}</blockquote>')
        elif s.startswith(('- ','* ')):o.append(f'<li>{s[2:]}</li>')
        elif s and s[0].isdigit() and '. ' in s[:4]:o.append(f'<li>{s.split(".",1)[1].strip()}</li>')
        elif s=='---':o.append('<hr>')
        elif s:o.append(f'<p>{s}</p>')
        i+=1
    return '\n'.join(o)

def build():
    w=parse_words(rd('words'))
    k=parse_knowledge(rd('knowledge'))
    g=parse_guide(rd('guide'))
    a=parse_abbreviation(rd('abbreviations'))
    for sec in k:
        if sec.get('empty'):continue
        for sub in sec.get('subs',[]):
            sub['html']=md2html(sub.get('html',''))
    for sec in g:
        sec['content']=md2html(sec.get('content',''))
    return {"words":{"title":"单词本","sections":w},
            "knowledge":{"title":"知识本","sections":k},
            "guide":{"title":"指南本","sections":g},
            "abbreviations":{"title":"缩略词","sections":a}}

def gen_js():
    return 'const DATA = '+json.dumps(build(),ensure_ascii=False)+';'

def main():
    with open(HTML,encoding='utf-8') as f:
        html=f.read()
    js=gen_js()
    m=re.search(r'const DATA\s*=\s*\{',html)
    if not m:print('[ERR] const DATA not found');return
    start=m.start()
    brace=m.end()-1
    depth,i=1,brace+1
    while i<len(html) and depth>0:
        if html[i]=='{':depth+=1
        elif html[i]=='}':depth-=1
        i+=1
    end=i
    if end<len(html) and html[end]==';':end+=1
    html=html[:start]+js+html[end:]
    with open(HTML,'w',encoding='utf-8') as f:
        f.write(html)
    d=build()
    for k,v in d.items():
        n=sum(len(s.get('items',[])) for s in v['sections'])
        b=sum(len(s.get('subs',[])) for s in v['sections'])
        # also count items inside subs
        si=sum(sum(len(sb.get('items',[])) for sb in s.get('subs',[])) for s in v['sections'])
        tot=n+si
        print(f'  {k}: {tot} items, {b} subs, {len(v["sections"])} sections')
    print('[OK]')

if __name__=='__main__':main()
