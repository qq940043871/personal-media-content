# AGENTS.md

## Project: 《时间裂隙：2089》(Time Rift: 2089)

600-chapter sci-fi novel across 10 volumes. **ALL 600 CHAPTERS COMPLETE**. This is a **creative writing / revision** project — no build or test steps.

## Core workflow

**Before writing or editing a chapter, read these 6 files in order:**
1. `novel/world-building.md`
2. `novel/characters.md`
3. `novel/timeline.md`
4. `novel/plot-outline.md`
5. `novel/writing-notes.md` (memory backbone — chapter summaries, continuity, pending issues)
6. Latest chapter in `novel/chapters/`

**After writing/editing, update these immediately:**
- `novel/timeline.md` — new events with timestamps
- `novel/writing-notes.md` — summary, character changes, new settings, foreshadowing, continuity, progress stats
- `novel/characters.md` — state/relationship changes; new characters under `## 新生角色`
- `novel/plot-outline.md` — mark completed plot points with ✅

## Chapter format

```
# 第X章 [标题]

[正文, 3000–5000 words, key chapters 5500–8000]

---
**本章关键点：**
- Event 1
- Event 2
- Character state changes
```

Always include the `本章关键点` footer. Minimum 3000 words per chapter.

## File naming

- Chapters: `novel/chapters/chapter-XXX.md` (3-digit zero-padded, e.g. `chapter-002.md`, `chapter-437.md`)
- Storyboards: `novel/storyboards/第X章-标题-分镜脚本.md`
- **Mismatch warning**: older storyboards exist at repo root, `分镜/`, and `storyboard/`. Canonical location is `novel/storyboards/`.

## Batch writing workflow

1. Plan chapter arc (key events for each chapter)
2. Write in batches of 3–5 per tool call
3. Update supporting files **after each batch**, not every chapter
4. For batches of 10+, fix progress stats and character states in the final batch update

## Key reference files

- `novel/unified-settings.md` — detail consistency reference (ARIA's eye color, mechanical arm color, character name disambiguation)
- `review/review-report.md` — comprehensive review (quality assessment, problem areas)
- `review/审稿报告-全书章节审查.md` — per-chapter length audit
- `.claude/skills/scifi-novel-writer.md` — full skill instructions, initialization flow, consistency check format

## Known issues (from review)

- The novel is complete. Primary work is **editing/rewriting** — especially chapters 60–300 (worldview expansion is too rapid) and 340–480 (template-heavy writing, lacks concrete conflict at medium scale)
- Do NOT introduce new characters, factions, or technology until checked against existing world-building
- Do NOT use 2-digit chapter numbers — always 3-digit
- Some chapter files have `-merged`, `-expanded`, or `-b` variants (e.g. `chapter-017b.md`, `chapter-458-merged.md`) — these are rewrites, check both before editing
