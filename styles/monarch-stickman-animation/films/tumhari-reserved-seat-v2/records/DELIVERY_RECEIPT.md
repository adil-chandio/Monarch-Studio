# Signed delivery receipt — TUMHARI RESERVED SEAT · WF-01 · V2 MONARCH CINEMA TABAHI

**Task:** `EMS-20261011-003`
**Issued:** 2026-10-11T06:56:02+05:00
**Status:** **FINAL / ACCEPTED**
**Workflow:** WF-01 · Monarch Stickman Animation

## Locked continuity

- 74.00 s · 34 beats · 1920×1080 · 30 fps · 16:9 landscape.
- Exact un-stretched `voice-00`; SHA-256 `c411bfae2b12b194cf2107c556b2604e82f3e763c9e6fea94a6186ac650ca972`.
- Timeline SHA-256 `75838e71c598c04bb322fabbe080d71641853aa9fc2cf2dc6341a73e42698c0b`.
- Immutable V1 tree SHA-256 `b3bb861b1166fdfc11eadf4705703da5d476520fb7523aff81e0ae6aabcbe6fe`.

## Accepted master

- `TUMHARI_RESERVED_SEAT_WF01_V2_MONARCH_CINEMA_TABAHI.mp4`
- Bytes: `87,041,066`
- SHA-256: `fb78611106ecf008d400961aa29318a950091b7aa130a108cd9d797b0b41138f`
- MD5: `1aebd8e3a5d843abb7df6595e6d1e713`
- Drive: https://drive.google.com/file/d/1MsD3Fibj_XhU7_3TJdb7L4MqCI2CxDWH/view

## Deterministic source

- `TUMHARI_RESERVED_SEAT_WF01_V2_SOURCE.zip` · `2,878,045` bytes
- SHA-256: `2833a9310d38a683af5d1576d0a473204128017192cdb91060420103ccb7a174`
- MD5: `725ef48e0b4cd597ce3218f2e0f11974`
- Drive: https://drive.google.com/file/d/1eQVcET-z9yKdkIszaRjHcgfsgcctzNGU/view

## Acceptance

- **44/44** delivery gates PASS
- **30/30** freshness PASS
- **33/33** transition-boundary smoke PASS
- Full decode and manually inspected final-master contact sheet: PASS

## Uploaded evidence

- `delivery_gates` — SHA-256 `4a7227433496eb60bfb692a40fa94d9f25f7b370b06b213c44bc3963a305e942` · MD5 `5c8753a78318f0028f4a1525c393893a` · Drive `1-sntm8SeL1el4FguDxZxoL7KDmSgdQmb`
- `look_sheet` — SHA-256 `3f7f3e3099f06f646aef9f2885b3295c54a3d5826c43c085ea71764bdff13cf8` · MD5 `dc3d0114e477db5bcc17b980fbe73d86` · Drive `1TF283cW1Xbl0jMtKYqFoccMHhtBLbBgu`
- `final_qc_contact_sheet` — SHA-256 `8cdf91c6ed5305cf641dc4219d939f9225c7d4ffbf9de8f0dd44f746729e3b34` · MD5 `a02dc5203f7881922f5aae299267f812` · Drive `17Mgw9hH_fnY2b-HgHHM_OnnNXIoqOpi-`
- `provenance` — SHA-256 `3ddd977ad19031ef9712c7ccc1b125436a973649b8f1749554704d6658f7e07d` · MD5 `061e8afec4340976b27dd71531b8575a` · Drive `16Uw62pTyDgOprSbsmOd6Iqfiaa7hLY4n`

## Authority and signature

- Production commit: [9b4d6fca4338fbd9d8de34e354a5ba15819ef33e](https://github.com/adil-chandio/Monarch-Studio/commit/9b4d6fca4338fbd9d8de34e354a5ba15819ef33e)
- Repository package: `styles/monarch-stickman-animation/films/tumhari-reserved-seat-v2`
- Signed JSON: `records/DELIVERY_RECEIPT.json`
- Canonical payload SHA-256: `a2b5f93c99c082ca751e62fdb219661dea317283e5e9e043c795f50b539d6bf6`
- Signature: Ed25519; public key `records/RECEIPT_PUBLIC_KEY.txt` (SHA-256 `5e6288f9b7ac03a8e0804d78cb56bf3ca5c873cec8d473d76d59a577ba1bf58b`).
- Verify: `python3 records/verify_receipt.py records/DELIVERY_RECEIPT.json` from the package root.

The signature is a task-scoped cryptographic integrity seal. The production commit and the later archival synchronization commit provide repository authority and history.
