#!/usr/bin/env python3
"""docent 검사. 사용: check.py <문서.md> [<문서.md> ...] [--no-render]

글자만 보고 찾을 수 있는 것만 검사한다. 통과했다고 규칙을 다 지킨 것은 아니다.
그림 검사와 비유 검사는 같은 폴더의 figures.py 에 있다.

실패 (exit 1):
  1. mermaid 블록이 렌더되지 않는다 (chrome-headless-shell + mermaid 11.4.1) (4-9)
     브라우저는 CHROME_BIN, ~/.local/bin/chrome-headless-shell, PATH 순서로 찾는다.
     찾지 못하거나 결과를 받지 못하면 실패가 아니라 "렌더 못 함" 경고로 적는다.

경고:
  2. 화살표에 글씨가 없다. sequenceDiagram 은 ':' 뒤가 비었는지, flowchart 는 화살표 수보다 글씨 수가 적은지 본다 (4-4)
  3. mermaid 블록 하나의 노드가 아홉 개를 넘는다 (4-7)
  4. 노드 글씨가 네 줄 이상이다 (4-7)
  5. 비유 신호어 (2-5)
  6. 무엇인지 붙이지 않은 번호와 지시어: "4번은", "이 ref", "해당 값" 같은 것 (2-4)
  7. 지어낸 이름이기 쉬운 말: "옛 API", "같은 아이디", "새 경로" 같은 것 (2-2)
  8. 원본 문서를 주어로 쓴 말: "원문은", "보고서에 따르면" 같은 것. "## 출처" 아래는 보지 않는다 (1-4)

파이썬 표준 라이브러리만 쓴다.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import figures  # noqa: E402

B = r'(?<![가-힣\w])'   # 낱말의 앞 경계
E = r'(?![가-힣\w])'    # 낱말의 뒤 경계 (조사가 붙으면 맞지 않으므로 이름 뒤에만 쓴다)
VAGUE = [B + r'이 ref', B + r'그 ref', B + r'해당 (값|파일|컬럼|테이블|API|코드|부분)', B + r'위의 것', B + r'앞의 것',
         B + r'그 경로', B + r'이 경로']
SOURCE_REF = re.compile(B + r'(원문|원본 문서|보고서|제안서)(은|는|이|가|에서는|에 따르면|의 말|에 없)')
COINED = [B + r'옛 API', B + r'구 API', B + r'같은 아이디', B + r'새 경로',
          ]
NUMBER_REF = re.compile(r'(?<![\w.-])(\d+(?:-[A-Z0-9]+)?)번(은|는|이|가|을|를|에서|도|만)(?!\s*\()')


def check_file(path, do_render=True):
    text = open(path, encoding='utf-8').read()
    errors, warns = [], []
    prose, blocks = figures.split_fences(text)
    if do_render:
        for e in figures.render(blocks):
            (warns if e.startswith(figures.RENDER_NOTE) else errors).append(f'mermaid {e} (4-9)')
    for bi, b in enumerate(blocks, 1):
        warns += figures.check_block(bi, b)

    in_source = False
    for i, line in prose:
        if re.match(r'^##\s*출처', line):
            in_source = True
        elif line.startswith('## '):
            in_source = False
        plain = figures.strip_code(line)
        warns += figures.check_analogy(i, plain)
        for p in VAGUE:
            m = re.search(p, plain)
            if m:
                warns.append(f'{i}: 무엇을 가리키는지 붙이지 않은 말 "{m.group(0)}" (2-4)')
        for m in NUMBER_REF.finditer(plain):
            warns.append(f'{i}: 번호만 쓴 "{m.group(0)}". 번호 뒤에 무엇인지 붙인다 (2-4)')
        if not in_source and not line.startswith(('title:', '원문:', '출처:')):
            for m in SOURCE_REF.finditer(plain):
                warns.append(f'{i}: 원본 문서를 주어로 쓴 "{m.group(0)}". 주제를 주어로 쓰고 출처는 맨 끝에 (1-4)')
        for p in COINED:
            m = re.search(p, plain)
            if m:
                warns.append(f'{i}: 지어낸 이름일 수 있는 "{m.group(0)}". 실제 이름으로 쓴다 (2-2)')
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
