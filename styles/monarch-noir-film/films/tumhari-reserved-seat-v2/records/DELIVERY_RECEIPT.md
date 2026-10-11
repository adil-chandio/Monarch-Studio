# Signed delivery receipt — TUMHARI RESERVED SEAT · WF-03 · V2 NOIR IMAX TABAHI

**Task:** `EMS-20261011-003`
**Issued:** 2026-10-11T06:56:02+05:00
**Status:** **FINAL / ACCEPTED**
**Workflow:** WF-03 · Monarch Noir Film · Intentionally unassigned; historical Film-#3 conflict remains unresolved.

## Locked continuity

- 74.00 s · 34 beats · 1920×1080 · 24 fps · 16:9 landscape.
- Exact un-stretched `voice-00`; SHA-256 `c411bfae2b12b194cf2107c556b2604e82f3e763c9e6fea94a6186ac650ca972`.
- Timeline SHA-256 `75838e71c598c04bb322fabbe080d71641853aa9fc2cf2dc6341a73e42698c0b`.
- Immutable V1 tree SHA-256 `789e386e018d9d797bd3824f1e55c6052f5bcee776b47a3fa5f966ef040f03b2`.

## Accepted master

- `TUMHARI_RESERVED_SEAT_WF03_V2_NOIR_IMAX_TABAHI.mp4`
- Bytes: `46,549,431`
- SHA-256: `bc52e242a21c4001d6dd2e0612457c74de7865f726598c5ae75c6f6c70533ed3`
- MD5: `cbf4d9c5f3c77a9137d8f96755613956`
- Drive: https://drive.google.com/file/d/1r-gXHPGr0LRQuuDsOLlbyagoC3kJnj6r/view

## Deterministic source

- `TUMHARI_RESERVED_SEAT_WF03_V2_SOURCE.zip` · `2,500,332` bytes
- SHA-256: `8da94ab0e52635e2310a6185d3c7ebe3f619f9df1e3150259a4b8ed598ab7f1d`
- MD5: `7fcaffb3b0e052c137647c9383e4b4d6`
- Drive: https://drive.google.com/file/d/11tdG-ZzGaWajUufWC5TwfRTtUzVMSIrF/view

## Acceptance

- **44/44** delivery gates PASS
- **30/30** freshness PASS
- **33/33** transition-boundary smoke PASS
- Full decode and manually inspected final-master contact sheet: PASS

## Uploaded evidence

- `delivery_gates` — SHA-256 `edb35e2e2c515cbaccbc3943d0a5f4106f20ce3a9058a4120805b88fda4517ef` · MD5 `60a08cf73794bbd4430e64dcdb84b1a5` · Drive `1UrUZuklMh8GtUGv1d-_LLiogwPS7aZyM`
- `look_sheet` — SHA-256 `fff01e8975b2be37a6882d338ffdcab9a51f2c24da7a1fbd8f3b63f03df9f509` · MD5 `2d220be79afce5ba956ea568cd25ddaa` · Drive `1G0XozHjIfAfkC47kCLymyA7KtPjGaFdj`
- `final_qc_contact_sheet` — SHA-256 `4ff2cdd248d70c2394dd98cb343631eca26478879a61d2bc961639823cdd96a2` · MD5 `f161afd8f69a38a74da75985caed44e4` · Drive `1yrlycTk0CjqEAxqZi1WNcCuJ7VtZPCcy`
- `provenance` — SHA-256 `6157d206bf67fcf9aa86d4448bd34b0ed550c622b6e92a99ee0c1c0d45d3b7cc` · MD5 `72cae2997adcaacfeb4622873975ae30` · Drive `1p0tv3rHyzL4jTrY3Hh2Ny_0woDm-ELWN`

## Authority and signature

- Production commit: [9b4d6fca4338fbd9d8de34e354a5ba15819ef33e](https://github.com/adil-chandio/Monarch-Studio/commit/9b4d6fca4338fbd9d8de34e354a5ba15819ef33e)
- Repository package: `styles/monarch-noir-film/films/tumhari-reserved-seat-v2`
- Signed JSON: `records/DELIVERY_RECEIPT.json`
- Canonical payload SHA-256: `587547376773653995c53f41793027737f6fb0b2d14dcc67e2b9596d81f7d751`
- Signature: Ed25519; public key `records/RECEIPT_PUBLIC_KEY.txt` (SHA-256 `5e6288f9b7ac03a8e0804d78cb56bf3ca5c873cec8d473d76d59a577ba1bf58b`).
- Verify: `python3 records/verify_receipt.py records/DELIVERY_RECEIPT.json` from the package root.

The signature is a task-scoped cryptographic integrity seal. The production commit and the later archival synchronization commit provide repository authority and history.
