#!/usr/bin/env python3
"""Verify an EMS signed JSON receipt using its embedded Ed25519 signature."""
import base64, hashlib, json, subprocess, sys, tempfile
from pathlib import Path
p = Path(sys.argv[1])
data = json.loads(p.read_text(encoding="utf-8"))
sig = data.pop("signature")
canonical = json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
actual = hashlib.sha256(canonical).hexdigest()
if actual != sig["canonical_payload_sha256"]:
    raise SystemExit(f"FAIL payload SHA-256: {actual} != {sig['canonical_payload_sha256']}")
key = p.parent / sig["public_key_file"]
key_sha = hashlib.sha256(key.read_bytes()).hexdigest()
if key_sha != sig["public_key_sha256"]:
    raise SystemExit(f"FAIL public-key SHA-256: {key_sha} != {sig['public_key_sha256']}")
with tempfile.NamedTemporaryFile() as msg, tempfile.NamedTemporaryFile() as rawsig:
    msg.write(canonical); msg.flush()
    rawsig.write(base64.b64decode(sig["signature_base64"])); rawsig.flush()
    cp = subprocess.run(["openssl","pkeyutl","-verify","-pubin","-inkey",str(key),"-rawin","-in",msg.name,"-sigfile",rawsig.name], capture_output=True, text=True)
    if cp.returncode:
        raise SystemExit("FAIL Ed25519 signature: " + (cp.stderr or cp.stdout))
print(f"PASS {p}: {actual}")
