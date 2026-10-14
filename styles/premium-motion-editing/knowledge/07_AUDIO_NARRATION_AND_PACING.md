# 07 · Narration, rhythm and sound

## Preserve selected work

The repair recovered the exact nine previously selected MP3 clips from immutable Git source and verified their hashes. It did not ask for another voice selection or synthesize new narration merely because local render caches were missing. V5 and V6 use natural 1.0× speech pace.

For a new script, do not reuse the old Einstein words. Reuse a voice preference/reference where appropriate, but obey the current speech tool's registration requirements. Session voice IDs are not guaranteed portable across chats. Existing audio files are durable assets; a remembered tool ID is not the audio itself.

## Let the voice establish the edit

Measure actual decoded audio. In the case, source clips were decoded to 48kHz mono for timing, leading/trailing quiet was tightened with small safety margins, and durations were rounded to the 30fps frame grid by adding quiet—not by cutting phonemes. Clip starts, trims and ends are preserved in each timeline.

The observed analysis used 10ms RMS windows, a 0.012 activity threshold, approximately 65ms leading margin and 130ms trailing margin. Those values are a case recipe, not a universal voice detector. Quiet consonants and breath require listening/inspection; never blindly reuse a threshold on a different recording.

Retiming the picture per semantic beat is preferable to global voice speed-up merely to match an English video's length. The case became 63.1 seconds while preserving the natural dub. The two clocks, violin/flow transitions, car/runner contrast and closing argument must follow the sentence that gives them meaning.

## Sound accents, not audio clutter

The case used a restrained procedural tonal floor, filtered-noise cut accents and small type taps. V6 added quiet clock/chalk/running cues and a closing rise. These are sound-design accents, **not** a claimed recording of Mozart. Use licensed/provided music if actual music is required; do not pretend a spoken-word synthesis tool sings or produces orchestral music.

Prioritize intelligible narration. Keep accents below dialogue, use pan sparingly, retain headroom and inspect final encoded audio. Loudness normalization does not fix a mistranslated script, distorted source or wrongly timed effect.

## Export and measurement

The case mix targeted FFmpeg loudnorm I=-16, TP=-1.5, LRA=9 and encoded AAC stereo at 192kbps / 48kHz. Decoded sample peaks were -1.52dBFS for V5 and -1.97dBFS for V6; both had roughly -19.57dBFS RMS. **RMS is not integrated LUFS, and sample peak is not automatically true peak.** State exactly which measurement was made.

Earlier QA decoded, timed and level-checked the output; it did not claim an independent human listening pass. Preserve that scope honestly. Record any final listening review actually performed rather than filling an approval field from intention.
