# korean-developer-skills

한국인 개발자를 위한 Claude Code 스킬 모음입니다.

AI 도구는 대부분 영어권 개발자를 기준으로 만들어집니다. 그래서 한국어로 일하는 개발자에게는 어색한 결과물이 자주 나옵니다. 번역투 문장, 개발자가 쓰지 않는 번역어("통합 시험", "공개 client") 같은 것들입니다. 이 저장소는 그런 틈을 메우는 스킬을 모읍니다.

## 스킬

| 스킬 | 하는 일 |
|---|---|
| `korean-sentences` | AI가 쓴 한국어 문서(Markdown, HTML, PR 본문 등)를 한국 개발자가 읽기 쉽게 고칩니다. 규칙(`references/rules.md`)과 개발 용어 목록(`references/terms/`)을 따르고, 고친 뒤 `scripts/check.py`로 코드, 링크, 숫자가 빠지지 않았는지 검사합니다. |
| `korean-sentences-rules` | `korean-sentences`가 고친 문장을 사람이 어색하다고 짚으면, 그 문장을 만든 규칙이나 용어 목록을 고치고 사례(`references/cases.md`)로 남깁니다. |

`korean-sentences`의 규칙과 용어 목록은 사람이 결과물을 읽다가 이상하다고 짚은 것만 더합니다. 쓰는 사람마다 규칙이 자라는 구조입니다.

## 설치

플러그인으로 설치하면 모든 스킬이 함께 들어옵니다.

```
claude plugin marketplace add handyskr/korean-developer-skills
claude plugin install korean-developer-skills@korean-developer-skills
```

플러그인 설치본은 캐시에 복사되므로, `korean-sentences-rules`가 고친 규칙은 업데이트할 때 덮어써질 수 있습니다. 규칙을 직접 키워 갈 생각이면 저장소를 clone한 뒤 스킬 폴더를 링크해서 쓰세요.

```
git clone https://github.com/handyskr/korean-developer-skills.git
ln -s "$PWD/korean-developer-skills/skills/korean-sentences" ~/.claude/skills/korean-sentences
ln -s "$PWD/korean-developer-skills/skills/korean-sentences-rules" ~/.claude/skills/korean-sentences-rules
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
    scripts/check.py   정적 검사 (파이썬 표준 라이브러리만 사용)
  korean-sentences-rules/
    SKILL.md           규칙 고치기 절차
```

## 스킬 더하기

새 스킬은 `skills/<스킬 이름>/SKILL.md`로 더합니다. 플러그인을 다시 설치하거나 업데이트하면 함께 들어옵니다. 한국인 개발자가 겪는 문제를 푸는 스킬이면 무엇이든 좋습니다.

## 라이선스

MIT. `LICENSE` 파일을 보세요.
