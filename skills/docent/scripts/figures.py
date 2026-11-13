"""mermaid 그림과 비유 신호어 검사. 같은 폴더의 check.py 가 쓴다.

그림 규칙은 references/rules.md 4장에 있다.
파이썬 표준 라이브러리만 쓴다.
"""
import json
import os
import re
import shutil
import subprocess
import tempfile

MERMAID = 'https://cdn.jsdelivr.net/npm/mermaid@11.4.1/dist/mermaid.min.js'
RENDER_NOTE = '렌더 못 함'

# 비유 신호어 (2-5). "처럼"은 "작업 결과처럼", "아래처럼" 같은 맞는 쓰임이 많아 넣지 않는다.
ANALOGY = [re.compile(p) for p in (r'마치 ', r'비유하자면', r'비유하면', r'(이)?라고 생각하면', r'(이)?라고 보면', r'에 빗대')]

FENCE = re.compile(r'^(?P<prefix>[ \t]*(?:>[ \t]?)*[ \t]*)(?P<fence>`{3,}|~{3,})[ \t]*(?P<lang>[\w-]*)[^\n]*$')
SEQ_ARROW = re.compile(r'^\s*[\w가-힣]+\s*(-{1,2}>>|-{1,2}>|-{1,2}x|-{1,2}\))[+-]?\s*[\w가-힣]+\s*(:\s*(.*))?$')
FLOW_ARROW = re.compile(r'<?(?:-\.+->|-{2,}>|={2,}>|-{3,}|={3,})')
PIPE_LABEL = re.compile(r'\|[^|]*\|')                      # A -->|글씨| B
INLINE_LABEL = re.compile(r'--\s*[^-=.>|\s][^>|]*?\s*(?:-->|---)|-\.\s*[^-.>\s][^>]*?\s*\.->|==\s*[^=>\s][^>]*?\s*==>')  # A -- 글씨 --> B
NODE_LABEL = re.compile(r'"[^"]*"|\[[^\[\]]*\]|\([^()]*\)|\{[^{}]*\}')
FLOW_SKIP = ('classDef', 'class ', 'style ', 'linkStyle', 'subgraph', 'end', 'direction', 'click ')


def find_chrome():
    """mermaid 를 렌더할 브라우저를 찾는다. CHROME_BIN 환경 변수가 가장 먼저다."""
    candidates = [os.environ.get('CHROME_BIN'), os.path.expanduser('~/.local/bin/chrome-headless-shell')]
    candidates += [shutil.which(n) for n in ('chrome-headless-shell', 'chromium', 'chromium-browser', 'google-chrome')]
    for c in candidates:
        if c and os.path.exists(c):
            return c
    return None


def split_fences(text):
    """글을 줄 단위로 읽어 (코드 밖 줄 목록, mermaid 블록 목록)을 돌려준다.

    코드 밖 줄 목록은 (줄 번호, 줄) 이다. ``` 와 ~~~ 펜스, 들여쓴 펜스, 인용(>)이나
    옵시디언 callout 안의 펜스를 모두 본다. callout 안 블록은 앞의 > 를 떼고 돌려준다.
    """
    prose, blocks = [], []
    fence = None  # (펜스 글자, 길이, 앞에 붙은 것, 언어, 모은 줄)
    for i, line in enumerate(text.split('\n'), 1):
        m = FENCE.match(line)
        if fence is None:
            if m:
                fence = (m.group('fence')[0], len(m.group('fence')), m.group('prefix'), m.group('lang'), [])
            else:
                prose.append((i, line))
            continue
        char, size, prefix, lang, body = fence
        if m and m.group('fence')[0] == char and len(m.group('fence')) >= size and not m.group('lang'):
            if lang == 'mermaid':
                blocks.append('\n'.join(body))
            fence = None
            continue
        stripped = prefix.strip()
        if stripped and line.lstrip().startswith('>'):
            line = re.sub(r'^[ \t]*(?:>[ \t]?)*', '', line)
        body.append(line)
    return prose, blocks


def render(blocks):
    """깨진 그림의 목록을 돌려준다. 렌더하지 못했으면 RENDER_NOTE 로 시작하는 한 줄을 돌려준다."""
    if not blocks:
        return []
    chrome = find_chrome()
    if not chrome:
        return [RENDER_NOTE + ': 브라우저 없음. chrome-headless-shell 을 설치하거나 CHROME_BIN 에 경로를 준다']
    page = ('<!doctype html><meta charset=utf-8><title>pending</title><script src="' + MERMAID + '"></script>'
            '<body><script>const B=' + json.dumps(blocks).replace('</', '<\\/') + ';(async()=>{mermaid.initialize({startOnLoad:false});'
            'const r=[];for(let i=0;i<B.length;i++){try{await mermaid.render("m"+i,B[i]);r.push("m"+(i+1)+" ok")}'
            'catch(e){r.push("m"+(i+1)+" ERR "+String(e.message||e).slice(0,160).replace(/\\n/g," "))}}'
            'document.title=r.join(" | ")})()</script></body>')
    with tempfile.NamedTemporaryFile('w', suffix='.html', delete=False, encoding='utf-8') as f:
        f.write(page)
        path = f.name
    try:
        out = subprocess.run([chrome, '--headless', '--disable-gpu', '--virtual-time-budget=20000', '--dump-dom', 'file://' + path],
                             capture_output=True, text=True, timeout=120).stdout
    except (OSError, subprocess.TimeoutExpired) as e:
        return [RENDER_NOTE + f': 브라우저 실행 실패 ({e})']
    finally:
        os.unlink(path)
    m = re.search(r'<title>([^<]*)</title>', out)
    if not m or m.group(1) == 'pending':
        return [RENDER_NOTE + ': 결과 없음 (네트워크나 브라우저 문제)']
    return [s for s in m.group(1).split(' | ') if 'ERR' in s]


def check_block(bi, block):
    """그림 하나의 경고: 글씨 없는 화살표(4-4), 아홉 개 넘는 노드(4-7), 네 줄 이상인 노드 글씨(4-7), 라벨 안 < >."""
    warns = []
    lines = [l.strip() for l in block.split('\n') if l.strip() and not l.strip().startswith('%%')]
    kind = lines[0].split()[0] if lines else ''
    for s in lines[1:]:
        if re.search(r'"[^"]*<(?!br\s*/?>)[A-Za-z][^"]*"', s):
            warns.append(f'mermaid m{bi}: 라벨 안 < > "{s[:60]}"')
    if kind == 'sequenceDiagram':
        participants = set()
        for s in lines[1:]:
            m = re.match(r'(participant|actor)\s+([\w가-힣]+)', s)
            if m:
                participants.add(m.group(2))
                continue
            a = SEQ_ARROW.match(s)
            if a:
                participants.update(re.findall(r'[\w가-힣]+', s.split(':')[0].replace(a.group(1), ' ')))
                if not (a.group(3) or '').strip():
                    warns.append(f'mermaid m{bi}: 글씨 없는 화살표 "{s[:60]}" (4-4)')
        if len(participants) > 9:
            warns.append(f'mermaid m{bi}: 참여자 {len(participants)}개, 아홉 개를 넘음 (4-7)')
    elif kind in ('flowchart', 'graph'):
        nodes = set()
        for s in lines[1:]:
            if s.startswith(FLOW_SKIP):
                continue
            labels = len(PIPE_LABEL.findall(s)) + len(INLINE_LABEL.findall(s))
            bare = PIPE_LABEL.sub(' ', s)           # 화살표 뒤에 붙은 글씨를 지운다
            bare = INLINE_LABEL.sub(' --> ', bare)  # 글씨를 품은 화살표를 맨 화살표로 바꾼다
            for _ in range(4):                       # 노드 글씨를 지운다 (겹친 괄호까지)
                bare = NODE_LABEL.sub('', bare)
            arrows = len(FLOW_ARROW.findall(bare))
            if arrows > labels:
                warns.append(f'mermaid m{bi}: 글씨 없는 화살표 "{s[:60]}" (4-4)')
            for part in FLOW_ARROW.split(bare):
                nodes.update(re.findall(r'[A-Za-z_가-힣][\w가-힣]*', part.split(':::')[0]))
            for label in NODE_LABEL.findall(s):
                if len(re.findall(r'<br\s*/?>', label)) >= 3:
                    warns.append(f'mermaid m{bi}: 노드 글씨 네 줄 이상 "{s[:60]}" (4-7)')
        if len(nodes) > 9:
            warns.append(f'mermaid m{bi}: 노드 {len(nodes)}개, 아홉 개를 넘음 (4-7)')
    return warns


def check_analogy(i, plain):
    """백틱 안을 뺀 글 한 줄에서 비유 신호어를 찾는다."""
    return [f'{i}: 비유 신호어 "{m.group(0).strip()}" (2-5)' for p in ANALOGY for m in p.finditer(plain)]


def strip_code(line):
    return re.sub(r'`[^`]*`', '', line)
