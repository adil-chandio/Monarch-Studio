# Privacy and asset policy

## Character identity assets

The supplied Drive hierarchy includes personal face-reference videos, a Snapchat look-target video and a voice sample. These are production authorities but potentially sensitive identity data.

Repository policy:

- do not check raw face videos or voice samples into Git;
- do not publish them through third-party model/tooling repositories;
- record their Drive identities only where needed for provenance;
- use the locked generated sheets/Bible/Board for routine production;
- require explicit authorization before voice cloning, biometric processing or public redistribution.

## Character masters

The lossless REAL/STICK character sheets remain authoritative on Drive. The repository carries:

- Character Bible v2 (PDF);
- Master Board v2 (PNG);
- compact JPEG previews of the four current sheets;
- state and selected generation/spec code.

The JPEGs are review proxies, not replacements for the lossless Drive masters. Their filenames deliberately include `_preview`.

## Rendered masters

Full delivered videos are not committed to Git because of size, duplication and publication/privacy concerns. Workflow records preserve exact Drive IDs and MD5 hashes. Rebuild outputs belong in ignored `build/`/`.runtime/` directories.

## Fonts and bundled media

WF-01 contains the exact fonts and production media in its source package because they are part of the historical renderer. Do not extract or redistribute those files independently unless their upstream license permits it. The repository's proprietary license does not grant rights the studio does not own.

## Third-party repositories

Submodules retain their own licenses. Do not copy prompt catalogues or model/tool branding into Monarch-authored materials in a way that obscures source attribution. Any external adapter must keep workflow data local by default and document what leaves the machine.

## Secrets

Never commit API keys, Drive cookies, connector tokens, `.env` files or credentials. `.gitignore` includes common secret patterns, but human review remains required before push.