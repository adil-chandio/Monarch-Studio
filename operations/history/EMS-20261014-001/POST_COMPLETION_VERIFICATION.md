# Post-completion verification · KAANTA / WF-02

Production date: 15 October 2026, Asia/Karachi. Task ID retains its UTC start date.

## Delivered and read back

A final Drive listing returned exactly five files in release folder `1SqX_S44eVowdTAyBVzAFerYUYFJd6NtF`, under the confirmed WF-02 parent `1LTkHpkEUFSui8Lqyy8I0j5-1AceSziWX`:

| Deliverable | Real Drive ID | Bytes | Remote MD5 |
|---|---|---:|---|
| Final MP4 | `10YyHXoz1avbHTrSzOW7xWZwiZUvTEMOT` | 20075498 | `31d3955099bd8f9c05307c94179a5e04` |
| Editable source ZIP | `16umpzS8tqzlQTLspAL2dQzEAO2dlh6WN` | 4953476 | `3adcac7be57eb00bf0b364aa6a1a1ee3` |
| Script / production notes | `1fmgHBgWUVEpmzHzR5eNJEHeW3QIkx6ry` | 7446 | `8445aa2e8b607a2faf6358d3f7799872` |
| Roman Urdu SRT | `1qrGS8EduNiDqd5mrDcosw8hgYbb8MX5b` | 1047 | `6fbea4787171d1289e898491ac2b8043` |
| Delivery receipt | `1YUZKEpAVScbVvJBlCXEQ63V9vPOKZVyF` | 2312 | `b86826c32174ca60215bf702a8983f2b` |

The video was opened in the user's file viewer. Its master remains in the ignored `.runtime/wf02-master/` directory and on Drive; it is not added to Git. Earlier Drive files and sharing permissions are unchanged.

## Measured production checks

- Actual final MP4: native 1080 × 1920; H.264, yuv420p; 24 fps; 30.5 seconds.
- All **732** frames decoded; 732 distinct downsampled anatomy-region frame hashes; continuous timestamps.
- Complete AAC audio decoded; stereo 48 kHz; **−16.03 LUFS**, **−2.57 dBTP**, 4.1 LU LRA.
- Actual-master gate: **12/12** passed.
- Production source contracts: **7/7** passed after promotion.
- GLB validation: **0 errors, 0 warnings**, 15 informational unused-UV notices.
- Repeated/out-of-order anatomy-region render regression passed. A tiny initial brand-mark rasterization difference in the earlier full-frame diagnostic is preserved and documented, not concealed.
- Ten encoded-frame samples visually inspected. This does not certify every pronunciation, user artistic approval, exact reference matching or clinical validity.

## Repository checks

- Permanent source: `styles/monarch-zackd-3d/projects/EMS-20261014-001/splinter-v2`.
- WF-02 added to current registries, with the older Powerful Personality legacy snapshot explicitly preserved.
- Portable WF-02 hydration copies source without rewriting it.
- Test cleanup is scoped to its own compatibility runtimes; it did not erase the delivered video.
- Dependency virtual environments are excluded from integrity manifests.
- `python3 tools/studio.py validate --json`: **21 passed, 0 errors**, one disclosed existing historical-absolute-path warning.
- Repository unit suite: **10/10 passed**.
- Current branch remains `arena/eba29c7c-monarch-studio`; no other branch was created/switched/pushed. No commit, push or PR was needed for this request.
- Active task is now idle; full task transcript/journal is archived here.

## Remote-sync scope

Final outbox checkpoint `0009-20261014T212447Z` marks Google Drive complete using the real delivery-receipt ID. Earlier Drive checkpoint entries are superseded by this delivery. GitHub remote, Docs, Notion and Linear are explicitly **not requested**, not falsely marked synced. Local source changes are saved in the working branch.
