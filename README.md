# korean-developer-skills

한국인 개발자를 위한 Claude Code 스킬 모음입니다.

AI 도구는 대부분 영어권 개발자를 기준으로 만들어집니다. 그래서 한국어로 일하는 개발자에게는 어색한 결과물이 자주 나옵니다. 번역투 문장, 개발자가 쓰지 않는 번역어("통합 시험", "공개 client") 같은 것들입니다. 문장이 매끄러워도 읽는 사람이 모르는 낱말과 지어낸 이름으로 채워져 되묻게 되는 글도 많습니다. 이 저장소는 그런 틈을 메우는 스킬을 모읍니다.

## 스킬

| 스킬 | 언제 쓰나 | 하는 일 |
|---|---|---|
| `korean-sentences` | 내용은 이해되는데 문장이 어색할 때 | AI가 쓴 한국어 문서(Markdown, HTML, PR 본문 등)를 한국 개발자가 읽기 쉽게 고칩니다. 규칙(`references/rules.md`)과 개발 용어 목록(`references/terms/`)을 따르고, 고친 뒤 `scripts/check.py`로 코드, 링크, 숫자가 빠지지 않았는지 검사합니다. 다섯 번 쓸 때마다 고친 문장이 어땠는지 평가를 받아 쌓습니다. |
| `korean-sentences-rules` | 고친 문장이 여전히 어색할 때 | 사람이 어색하다고 짚은 문장을 만든 규칙이나 용어 목록을 고치고 사례(`references/cases.md`)로 남깁니다. |
| `docent` | 문서, 대화 내용, 작업 결과물이 읽기 어려울 때 | 원본이 이야기하는 것을 사람이 읽기 편한 형태로 풀어서 설명하는 새 글을 씁니다. 원본을 평가하거나 풀이하지 않고 주제 자체를 설명합니다. 구성은 주제에 맞게 다시 짜되 원본의 주장, 사실, 숫자는 그대로 둡니다. 읽는 데 필요한 지식은 짧은 주석, 덧붙인 절, 한두 문장으로 보탭니다. |
| `make-textbook` | 기반 지식을 처음부터 배우고 싶을 때 | 한 권을 정독하면 되는 학습용 교과서를 옵시디언 노트 여러 장으로 만듭니다. 전제 사다리에서 "여기까지는 안다"를 고르게 해서 깊이를 정하고, 고정 뼈대로 장을 쓴 뒤, 다른 에이전트가 공식 문서와 소스로 사실을 확인합니다. 근거를 찾지 못한 주장은 "미확인"으로 남깁니다. |

`docent`와 `make-textbook`은 서로의 파일을 읽지 않는 독립된 스킬입니다. `docent`는 글을 쓰면서 `korean-sentences`의 문장 규칙과 용어 목록을 함께 따릅니다.

규칙과 용어 목록은 사람이 결과물을 읽다가 이상하다고 짚은 것만 더합니다. 쓰는 사람마다 규칙이 자라는 구조입니다.

## 품질 평가

`korean-sentences`는 문서 하나를 고칠 때마다 사용을 기록합니다. 다섯 번 쓰면 보고 끝에서 "최근 다섯 번 고친 문장은 어땠나요?"를 한 번 묻습니다. 답은 "그대로 썼다", "조금 손봤다", "많이 손봐야 했다", "건너뛰기" 가운데 하나입니다. 낮은 점수와 함께 어색했던 문장을 짚으면 `korean-sentences-rules`가 그 문장을 만든 규칙을 고칩니다.

- 기록 위치는 `~/.claude/korean-sentences/feedback.jsonl`입니다. 스킬 폴더 밖이라 플러그인을 업데이트해도 남습니다. 환경 변수 `KOREAN_SENTENCES_DATA`로 폴더를 바꿉니다.
- 기록에는 문서의 내용과 경로가 들어가지 않습니다. 문서 형식과 글자 수, 점수, 사용자가 남긴 메모만 적습니다. 기록은 이 컴퓨터에만 있습니다.
- 묻는 간격은 환경 변수 `KOREAN_SENTENCES_RATE_EVERY`로 바꿉니다.
- 쌓인 평가는 아래 명령으로 봅니다.

```
python3 skills/korean-sentences/scripts/feedback.py summary
```

## 설치

플러그인으로 설치하면 모든 스킬이 함께 들어옵니다.

```
claude plugin marketplace add handyskr/korean-developer-skills
claude plugin install korean-developer-skills@korean-developer-skills
```

플러그인 설치본은 캐시에 복사되므로, `korean-sentences-rules`가 고친 규칙은 업데이트할 때 덮어써질 수 있습니다. 규칙을 직접 키워 갈 생각이면 저장소를 clone한 뒤 스킬 폴더를 링크해서 쓰세요. `docent`는 옆 폴더의 `korean-sentences`를 읽으므로 둘을 함께 링크합니다.

```
git clone https://github.com/handyskr/korean-developer-skills.git
for s in korean-sentences korean-sentences-rules docent make-textbook; do
  ln -s "$PWD/korean-developer-skills/skills/$s" ~/.claude/skills/$s
done
```

### 그림 검사에 필요한 것

`docent`와 `make-textbook`의 `scripts/check.py`는 mermaid 그림이 깨지지 않는지 헤드리스 브라우저로 렌더해 봅니다. 브라우저는 환경 변수 `CHROME_BIN`, `~/.local/bin/chrome-headless-shell`, `PATH`의 `chrome-headless-shell`·`chromium`·`google-chrome` 순서로 찾습니다. 찾지 못하면 그림 검사만 건너뛰고 "렌더 못 함" 경고를 냅니다. 렌더할 때 mermaid를 CDN에서 받으므로 네트워크가 필요합니다.

```
npx @puppeteer/browsers install chrome-headless-shell
export CHROME_BIN=<설치된 chrome-headless-shell 경로>
```

## 구조

```
.claude-plugin/        plugin.json, marketplace.json
skills/
  korean-sentences/
    SKILL.md           적용 절차, 영역별 용어 파일 목록
    references/
      rules.md         문장 규칙
      cases.md         규칙이 생긴 사례
      terms/           개발 용어 목록 (common, auth-oauth, database, spring, aws)
    scripts/
      check.py         정적 검사
      feedback.py      사용 기록과 품질 평가
  korean-sentences-rules/
    SKILL.md           규칙 고치기 절차
  docent/
    SKILL.md           왜 있는지, 쓰는 절차
    references/
      rules.md         읽는 사람이 한 번에 이해하는 글의 규칙
      skeletons.md     글 종류별 뼈대
      cases.md         규칙이 생긴 사례
    scripts/
      check.py         지시어·지어낸 이름·원본 풀이 검사
      figures.py       그림 렌더, 화살표·노드·비유 검사
  make-textbook/
    SKILL.md           왜 있는지, 만드는 절차
    references/style.md  출력 규격
    templates/         목차, 장, 현황 노트 뼈대
    scripts/
      check.py         장 뼈대·용어·문장 검사
      figures.py       그림 렌더, 화살표·노드·비유 검사
```

스크립트는 모두 파이썬 표준 라이브러리만 씁니다.

## 스킬 더하기

새 스킬은 `skills/<스킬 이름>/SKILL.md`로 더합니다. 플러그인을 다시 설치하거나 업데이트하면 함께 들어옵니다. 한국인 개발자가 겪는 문제를 푸는 스킬이면 무엇이든 좋습니다.

## 라이선스

MIT. `LICENSE` 파일을 보세요.
