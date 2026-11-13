#!/usr/bin/env python3
"""make-textbook 검사. 사용: check.py <노트.md> [<노트.md> ...] [--no-render]

그림 검사와 비유 검사는 같은 폴더의 figures.py 에 있다. 규격은 references/style.md 다.

1. mermaid 블록을 모두 렌더해 깨진 것을 찾는다 (chrome-headless-shell + mermaid 11.4.1)
   브라우저는 CHROME_BIN, ~/.local/bin/chrome-headless-shell, PATH 순서로 찾는다.
   찾지 못하거나 결과를 받지 못하면 실패가 아니라 "렌더 못 함" 경고로 적는다.
2. 뼈대: 한 줄 결론 / 용어 표 / 큰 그림 / 되짚기 / 정할 것 이 있는가, 되짚기가 다섯 줄 이내인가
   장 노트(파일 이름이나 title 이 "N장"으로 시작)에서만 본다. 목차·현황·설계 노트는 뼈대가 다르다.
3. 문장: 비유 신호어, 번역투·한자어. 백틱 안은 보지 않는다
4. 그림: 글씨 없는 화살표, 라벨 안 < >, 네 줄 이상인 노드 글씨, 아홉 개 넘는 노드
5. 용어: 대문자로 시작하는 백틱 식별자가 처음 나올 때 바로 뒤에 종류 태그 *(...)* 가 붙었는가.
   표 줄에서 처음 나온 것은 표가 종류를 적었다고 본다

깨진 mermaid 는 실패(exit 1). 나머지는 경고로 적는다. 파일을 읽지 못하면 exit 2.
파이썬 표준 라이브러리만 쓴다.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import figures  # noqa: E402

TRANSLATIONESE = ['에 대해', '에 있어서는', '에 있어 ', '되어진', '됨으로써', '함으로써', '기술한다', '기술하', '명시하', '도출', '수행하', '제반', '요구된다', '필요로 한다', '존재한다', '가능하다']
SKELETON = [
    ('한 줄 결론', r'\[!abstract\]'),
    ('용어 표', r'\[!info\]-?\s*.*(약어|용어)'),
    ('큰 그림', r'^##\s*0\.|큰 그림'),
    ('되짚기', r'\[!summary\]'),
    ('지금 정할 것', r'^##.*정할 것'),
]
IDENT = re.compile(r'`([A-Za-z][A-Za-z0-9_.:/-]{2,})`')
KIND_TAG = re.compile(r'\s*\*\([^)*]+\)\*')  # *(클래스)* 같은 종류 태그. 종류 목록은 references/style.md 4장
CHAPTER = re.compile(r'^\d+장')


def check_file(path, do_render=True):
    text = open(path, encoding='utf-8').read()
    errors, warns = [], []
    prose, blocks = figures.split_fences(text)
    if do_render:
        for e in figures.render(blocks):
            (warns if e.startswith(figures.RENDER_NOTE) else errors).append(f'mermaid {e}')

    title = re.search(r'^title:\s*(.+)$', text, re.M)
    title = title.group(1).strip().strip('"\'') if title else ''
    if CHAPTER.match(os.path.basename(path)) or CHAPTER.match(title):
        for name, pat in SKELETON:
            if not re.search(pat, text, re.M):
                warns.append(f'뼈대: "{name}" 없음')
    m = re.search(r'\[!summary\][^\n]*\n((?:>.*\n?)+)', text)
    if m:
        n = sum(1 for l in m.group(1).split('\n') if l.strip().startswith('> -'))
        if n > 5:
            warns.append(f'되짚기 {n}줄 (다섯 줄 이내)')

    seen_ids = set()
    for i, line in prose:
        plain = figures.strip_code(line)
        warns += figures.check_analogy(i, plain)
        for w in TRANSLATIONESE:
            if w in plain:
                warns.append(f'{i}: 번역투·한자어 "{w.strip()}"')
        in_table = line.lstrip().lstrip('> ').startswith('|')
        for m in IDENT.finditer(line):
            ident = m.group(1)
            if ident in seen_ids:
                continue
            seen_ids.add(ident)
            if in_table or not re.match(r'[A-Z][A-Za-z0-9]+$', ident):
                continue
            if not KIND_TAG.match(line, m.end()):
                warns.append(f'{i}: `{ident}` 첫 등장에 종류 태그 없음')

    for bi, b in enumerate(blocks, 1):
        warns += figures.check_block(bi, b)
    return errors, warns


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    do_render = '--no-render' not in sys.argv
    if not args:
        print(__doc__)
        sys.exit(2)
    failed = False
    for p in args:
        try:
            errors, warns = check_file(p, do_render)
        except (OSError, UnicodeDecodeError) as e:
            print(f'== {p}\n  읽지 못함: {e}')
            sys.exit(2)
        print(f'== {p}')
        for e in errors:
            print('  실패', e)
        for w in warns:
            print('  경고', w)
        if not errors and not warns:
            print('  통과')
        failed |= bool(errors)
    sys.exit(1 if failed else 0)


if __name__ == '__main__':
    main()
