# 06 · Typography and the rejected caption treatment

## The approved hierarchy

The scene carries the idea. Type highlights its meaning. Use a short kicker, a dominant condensed word or phrase, and a small connective line only when needed. Anton supplies the headline weight; Barlow Condensed Medium/Medium Italic supplies connectors and optional plain text. Font licenses are bundled.

Observed case headline sizes were approximately 64–124 at a 720×1280 design base, rendered at 1.5× for the 1080×1920 output. These numbers are not a license to force every phrase into one line. Fit the word count and line breaks to a readable minimum. The reusable compositor refuses unreadable overflow rather than shrinking indefinitely.

Top, bottom and side anchors are valid when the subject leaves room. The case needed a higher brain heading and careful separation around the violinist's feet and final pen nibs. New projects must declare their own geometry and review collisions instead of copying those special cases blindly.

## Latest user correction

V6 added a recurring dark rounded caption pill and active-word highlight at the bottom. The user explicitly rejected that treatment while accepting the other improvements. Therefore the production module has **no pill/word-strip renderer**. Its default is integrated scene type, with the separate subtitle overlay off.

A V5-like plain subtitle line is available only when requested in the brief and explicitly acknowledged by `plain_subtitles_requested=true`. It has no box, no pill and no active-word highlighting. A separate SRT may be delivered without burning an unwanted UI band into the picture.

## Avoid the common mistakes

- Do not overlay a full translated paragraph at a tiny size.
- Do not leave the old English behind and add a second competing text layer.
- Do not fill every lower-third gap with a permanent caption bar.
- Do not treat “newest version” as “approved version.” V6's technical pass did not override user feedback.
- Do not ban integrated lower-positioned headlines just because bottom caption pills were rejected.
- Do not claim proportional word highlighting is exact ASR alignment.

## Language capability

This reusable adapter is tested for Latin/Roman Urdu typography. Actual Urdu script requires a tested RTL/shaping/font backend. Do not render broken glyphs or microscopic substitutes and call it accurate localization. Keep phonetic clarity and meaning in the audio independent of the display script.

## Regression contract

Tests must reject `pill`, `karaoke`, `word_highlight`, `caption_pills=true` and `word_highlighting=true` in the approved production profile. They must allow normal bottom-positioned integrated titles. Tests must also ensure a new project does not copy Einstein text/audio and that a second project cannot inherit cached typography from the first.
