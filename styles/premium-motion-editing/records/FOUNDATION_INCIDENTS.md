# Foundation implementation incidents

1. The screenshot was visible inline, but its advertised workspace path was absent. The actual Drive folder was independently searched/read; no screenshot bytes were fabricated.
2. Broad Notion searches included body mentions and produced oversized results; exact schema-backed Workflows/Projects filters were used before creating WF-05, preventing duplicates.
3. First PDF build assumed DejaVuSans-Oblique.ttf was installed. It was absent. The builder now uses bundled documentation fonts and the included licensed Barlow italic font; only documentation export was retried. No video/source/voice was regenerated.

Video-history failures and fixes remain separately enumerated in data/lessons.json.

4. The first source-inventory audit checked its own coverage before writing the initial inventory. It correctly reported two missing references at that instant. The writer now rechecks the newly written file before computing final counts; no missing evidence check was suppressed.

5. Native Doc readback initially ran under system Python without the documentation venv dependency; the check was rerun in .venv, with 100% required-word coverage. No remote upload was duplicated.
6. The optional Google Docs insert-before-tab argument was rejected by the API. No tab was created by that failed call. The existing complete codex was preserved and a normal live-links section was used instead; no repeated invalid call or fabricated tab ID.
