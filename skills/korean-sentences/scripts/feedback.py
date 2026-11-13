#!/usr/bin/env python3
"""korean-sentences 사용 기록과 품질 평가. 사용: feedback.py <명령> [옵션]

스킬을 몇 번 쓸 때마다 사용자에게 고친 문장의 품질을 묻고, 그 답을 쌓는다.
파이썬 표준 라이브러리만 쓴다.

명령:
  use [--doc <고친 문서>] [--every N]   문서 하나를 고칠 때마다 한 번 부른다. 사용 한 번을 적고,
                                        평가를 물을 차례인지 알려 준다.
  rate --score {1,2,3} [--note <메모>]  사용자의 평가를 적는다. 평가를 적으면 차례를 다시 센다.
                                        3 그대로 썼다 / 2 조금 손봤다 / 1 많이 손봐야 했다
  skip                                  사용자가 평가를 건너뛰었다고 적는다. 차례를 다시 센다.
  status [--every N]                    아무것도 적지 않고, 평가를 물을 차례인지만 알려 준다.
  summary                               쌓인 평가를 요약한다.

평가를 묻는 간격은 --every, 환경 변수 KOREAN_SENTENCES_RATE_EVERY, 기본값 5 순서로 정한다.

기록은 스킬 폴더 밖에 둔다. 플러그인을 업데이트해도 지워지지 않게 하기 위해서다.
  기본 위치: ~/.claude/korean-sentences/feedback.jsonl
  바꾸려면: 환경 변수 KOREAN_SENTENCES_DATA 에 폴더 경로를 준다.

기록에는 문서의 내용과 경로를 넣지 않는다. 문서 형식(md, html)과 글자 수만 적는다.
기록은 이 컴퓨터에만 있고 어디로도 보내지 않는다.

파일을 쓰지 못하면 exit 2. 그 밖에는 exit 0.
"""
import argparse
import json
import os
import sys
from collections import Counter
from datetime import datetime

DEFAULT_EVERY = 5
LABELS = {3: '그대로 썼다', 2: '조금 손봤다', 1: '많이 손봐야 했다'}


def data_path():
    folder = os.environ.get('KOREAN_SENTENCES_DATA') or os.path.expanduser('~/.claude/korean-sentences')
    return os.path.join(folder, 'feedback.jsonl')


def load():
    """기록을 읽는다. 깨진 줄은 건너뛴다."""
    events = []
    try:
        with open(data_path(), encoding='utf-8') as f:
            for line in f:
                try:
                    e = json.loads(line)
                except ValueError:
                    continue
                if isinstance(e, dict) and e.get('event') in ('use', 'rating', 'skip'):
                    events.append(e)
    except FileNotFoundError:
        pass
    return events


def append(event):
    event = {'ts': datetime.now().astimezone().isoformat(timespec='seconds'), **event}
    path = data_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'a', encoding='utf-8') as f:
        f.write(json.dumps(event, ensure_ascii=False) + '\n')


def every(arg):
    if arg:
        return arg
    try:
        n = int(os.environ.get('KOREAN_SENTENCES_RATE_EVERY', ''))
    except ValueError:
        n = 0
    return n if n > 0 else DEFAULT_EVERY


def counts(events):
    """(전체 사용 수, 마지막 평가나 건너뛰기 뒤의 사용 수)"""
    total = pending = 0
    for e in events:
        if e['event'] == 'use':
            total += 1
            pending += 1
        else:
            pending = 0
    return total, pending


def print_status(events, n):
    total, pending = counts(events)
    print(f'사용 {total}번 · 마지막 평가 뒤 {pending}번 · 평가 간격 {n}번')
    if pending >= n:
        print('평가 요청: 예')
        print(f'  사용자에게 최근 {pending}번 고친 문장이 어땠는지 묻고, 답을 rate 나 skip 으로 적는다.')
    else:
        print('평가 요청: 아니오')


def cmd_use(args):
    event = {'event': 'use'}
    if args.doc:
        event['kind'] = os.path.splitext(args.doc)[1].lstrip('.').lower() or 'text'
        try:
            with open(args.doc, encoding='utf-8') as f:
                event['chars'] = len(f.read())
        except (OSError, UnicodeDecodeError):
            pass
    append(event)
    print_status(load(), every(args.every))


def cmd_rate(args):
    _, pending = counts(load())
    event = {'event': 'rating', 'score': args.score, 'label': LABELS[args.score], 'uses': pending}
    if args.note and args.note.strip():
        event['note'] = args.note.strip()
    append(event)
    print(f'평가를 적었습니다: {args.score} ({LABELS[args.score]}), 최근 {pending}번 사용')


def cmd_skip(args):
    _, pending = counts(load())
    append({'event': 'skip', 'uses': pending})
    print('건너뛰었다고 적었습니다.')


def cmd_status(args):
    print_status(load(), every(args.every))


def cmd_summary(args):
    events = load()
    total, pending = counts(events)
    ratings = [e for e in events if e['event'] == 'rating' and e.get('score') in LABELS]
    skips = sum(1 for e in events if e['event'] == 'skip')
    print(f'기록 위치: {data_path()}')
    print(f'사용 {total}번 · 평가 {len(ratings)}번 · 건너뛰기 {skips}번 · 마지막 평가 뒤 {pending}번')
    if not ratings:
        print('아직 평가가 없습니다.')
        return
    scores = [e['score'] for e in ratings]
    print(f'평균 {sum(scores) / len(scores):.2f} / 3')
    recent = scores[-5:]
    print(f'최근 {len(recent)}번 평균 {sum(recent) / len(recent):.2f} / 3')
    by_score = Counter(scores)
    for s in (3, 2, 1):
        print(f'  {s} {LABELS[s]}: {by_score[s]}번')
    notes = [e for e in ratings if e.get('note')]
    if notes:
        print('메모 (최근 것부터):')
        for e in reversed(notes[-20:]):
            print(f"  {e['ts'][:10]} [{e['score']}] {e['note']}")


def main():
    parser = argparse.ArgumentParser(description='korean-sentences 사용 기록과 품질 평가')
    sub = parser.add_subparsers(dest='command')
    p = sub.add_parser('use')
    p.add_argument('--doc')
    p.add_argument('--every', type=int)
    p.set_defaults(func=cmd_use)
    p = sub.add_parser('rate')
    p.add_argument('--score', type=int, choices=sorted(LABELS), required=True)
    p.add_argument('--note')
    p.set_defaults(func=cmd_rate)
    p = sub.add_parser('skip')
    p.set_defaults(func=cmd_skip)
    p = sub.add_parser('status')
    p.add_argument('--every', type=int)
    p.set_defaults(func=cmd_status)
    p = sub.add_parser('summary')
    p.set_defaults(func=cmd_summary)
    args = parser.parse_args()
    if not args.command:
        print(__doc__)
        sys.exit(2)
    if getattr(args, 'every', None) is not None and args.every < 1:
        parser.error('--every 는 1 이상이어야 한다')
    try:
        args.func(args)
    except OSError as e:
        print(f'기록 파일을 쓰지 못함: {e}')
        sys.exit(2)


if __name__ == '__main__':
    main()
