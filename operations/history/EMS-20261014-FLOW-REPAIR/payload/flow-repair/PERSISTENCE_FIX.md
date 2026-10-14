# Interrupted workspace export persistence fix

The completed 46,387,458-byte MP4 and runtime clips were lost in a workspace reset before Drive upload because they were Git-ignored. A checkpoint/receipt alone does not preserve those bytes. No output was actually presented/uploaded; the prior wording claiming presentation was corrected in the journal.

Pending-upload reference, cleaned motion clips and the master now live in a bounded non-ignored spool under this task until cloud checksums verify. Nonessential review frames, audio mix caches and dependencies remain ignored/rebuildable. Total expected critical spool is about 110 MB, below the 128 MB patch budget. Once uploaded and verified, heavy source media must return to ignored storage or be removed from Git scope; Drive becomes the durable authority.

A completed stage may be skipped only if both its receipt/fingerprint and its required artifacts exist. Cleanup now checks all fourteen clips/receipts, not only the last filename. Local encoding never closes DELIVERY_GATE.json.

Recovery is deterministic from the preserved selected speech and code; no new images, voice selection or script rewrite is needed.
