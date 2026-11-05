#!/usr/bin/env python3
"""korean-sentences 정적 검사. 사용: check.py <문서.md|문서.html> [--before <고치기 전 파일>]

글자만 보고 맞고 틀림이 정해지는 것만 검사한다. 맥락이나 판단이 필요한 것
(낱말이 그 글에 맞는지, 수에 단위가 필요한지, 말투, 시점 표현)은 넣지 않는다.
그런 것은 korean-sentences 의 SKILL.md "직접 읽고 확인한다" 단계에서 본다.

파일 확장자가 .html/.htm 이면 HTML, 그 밖에는 Markdown 으로 읽는다.
파이썬 표준 라이브러리만 쓴다.

문장 (경고):
  1. 영어·코드·링크 뒤에 띄어 쓴 조사: `Spring` 이, GitHub 에서, ]] 에 (5-2)
     HTML 은 <style> 을 빼고 태그를 걷어 낸 글자에서 본다. <script> 안 문자열도 화면에 나오는
     글일 수 있어 함께 본다.

--before 를 주면 내용이 빠지지 않았는지 본다:
  2. 코드 블록이 한 글자도 다르지 않은가 (다르면 실패)
     Markdown: mermaid 가 아닌 ``` 블록. HTML: class 에 mermaid 가 없는 <pre> 블록
  3. 그림(mermaid) 블록 수가 같은가 (다르면 실패)
     Markdown: ```mermaid 블록. HTML: class 에 mermaid 가 있는 요소
  4. 인라인 코드, [[링크]], 숫자가 사라지지 않았는가 (경고. 의도한 변경인지는 사람이 본다)
     Markdown: `백틱`. HTML: <code> 안 글자

실패가 있으면 exit 1. 경고만 있으면 exit 0. 파일을 읽지 못하면 exit 2.
"""
import re
import sys
from collections import Counter

PARTICLE = re.compile(
    r'(`|\]\]|[A-Za-z])'
    r' (이|가|을|를|은|는|의|에|에서|에는|에도|로|으로|와|과|도|만|부터|까지|보다|이다|입니다|이고)'
    r'(?=[\s.,)·:;]|$)')
NUMBER = r'\d+(?:[.,]\d+)*'


def is_html(path):
    return path.lower().endswith(('.html', '.htm'))


# ---------- Markdown ----------

def md_split(text):
    """줄마다 (번호, 줄, 구역). 구역: front, code, mermaid, fence, text."""
    out, fence, front = [], None, False
    for i, line in enumerate(text.splitlines(), 1):
        s = line.strip()
        if i == 1 and s == '---':
            front = True
            out.append((i, line, 'front'))
            continue
        if front:
            out.append((i, line, 'front'))
            if s == '---':
                front = False
            continue
        if s.startswith('```'):
            if fence is None:
                fence = 'mermaid' if s.startswith('```mermaid') else 'code'
            else:
                fence = None
            out.append((i, line, 'fence'))
            continue
        out.append((i, line, fence or 'text'))
    return out


def md_lines(text):
    return [(i, line) for i, line, zone in md_split(text) if zone not in ('front', 'code', 'fence')]


def md_blocks(text, kind):
    found, cur = [], None
    for _, line, zone in md_split(text):
        if zone == kind:
            cur = (cur or []) + [line]
        elif zone == 'fence' and cur is not None:
            found.append('\n'.join(cur))
            cur = None
    return found


def md_parts(text):
    prose = '\n'.join(line for _, line, zone in md_split(text) if zone not in ('code', 'mermaid', 'fence'))
    return {
        'code': md_blocks(text, 'code'),
        'figures': md_blocks(text, 'mermaid'),
        'inline': re.findall(r'`([^`\n]+)`', prose),
        'links': re.findall(r'\[\[([^\]|#]+)', prose),
        'numbers': re.findall(NUMBER, prose),
    }


# ---------- HTML ----------

STYLE = re.compile(r'<style\b.*?</style>', re.S | re.I)
PRE = re.compile(r'<pre\b([^>]*)>(.*?)</pre>', re.S | re.I)
MERMAID = re.compile(r'<(\w+)\b[^>]*class="[^"]*\bmermaid\b[^"]*"[^>]*>', re.I)
CODE = re.compile(r'<code\b[^>]*>(.*?)</code>', re.S | re.I)
TAG = re.compile(r'<[^>]+>')


def html_text(text):
    """<style> 을 빼고, 태그 자리를 줄바꿈 없이 걷어 낸 글자. 줄 번호를 지키려고 줄 단위로 둔다."""
    text = STYLE.sub(lambda m: '\n' * m.group(0).count('\n'), text)
    return TAG.sub('', text)


def html_lines(text):
    return list(enumerate(html_text(text).splitlines(), 1))


def html_parts(text):
    body = STYLE.sub('', text)
    code = [inner for attrs, inner in PRE.findall(body) if 'mermaid' not in attrs]
    prose = PRE.sub('', body)
    return {
        'code': code,
        'figures': MERMAID.findall(body),
        'inline': [TAG.sub('', c) for c in CODE.findall(prose)],
        'links': [],
        'numbers': re.findall(NUMBER, TAG.sub(' ', prose)),
    }


# ---------- 공통 ----------

def lint(lines):
    warns = []
    for i, line in lines:
        for m in PARTICLE.finditer(line):
            warns.append(f'{i}: [5-2] 띄어 쓴 조사 "…{line[max(0, m.start() - 12):m.end()].strip()}"')
    return warns


def compare(before, after):
    fails, warns = [], []
    if before['code'] != after['code']:
        fails.append(f'코드 블록이 달라졌다 (전 {len(before["code"])}개, 후 {len(after["code"])}개)')
    if len(before['figures']) != len(after['figures']):
        fails.append(f'그림(mermaid) 수가 달라졌다 ({len(before["figures"])} → {len(after["figures"])})')
    for key, name in [('inline', '인라인 코드'), ('links', '링크'), ('numbers', '숫자')]:
        lost = Counter(before[key]) - Counter(after[key])
        if lost:
            warns.append(f'{name}가 줄었다: ' + ', '.join(f'{k}×{v}' for k, v in lost.items()))
    return fails, warns


def read(path):
    try:
        with open(path, encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        sys.exit(f'파일이 없다: {path}')
    except UnicodeDecodeError:
        sys.exit(f'UTF-8 로 읽을 수 없다: {path}')


def main():
    args = sys.argv[1:]
    before_path = None
    if '--before' in args:
        k = args.index('--before')
        if k + 1 >= len(args):
            sys.exit(__doc__)
        before_path = args[k + 1]
        del args[k:k + 2]
    if len(args) != 1:
        sys.exit(__doc__)
    path = args[0]
    html = is_html(path)
    text = read(path)
    print(f'== {path} ({"HTML" if html else "Markdown"})')
    warns = lint(html_lines(text) if html else md_lines(text))
    fails = []
    if before_path:
        parts = html_parts if html else md_parts
        f, w = compare(parts(read(before_path)), parts(text))
        fails += f
        warns += w
    for f in fails:
        print('실패', f)
    for w in warns:
        print('경고', w)
    if not fails and not warns:
        print('통과')
    sys.exit(1 if fails else 0)


if __name__ == '__main__':
    try:
        main()
    except SystemExit as e:
        if isinstance(e.code, str):
            print(e.code, file=sys.stderr)
            sys.exit(2)
        raise
