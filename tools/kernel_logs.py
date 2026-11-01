#!/usr/bin/env python3
"""Kaggle kernel logs ko saaf text me badlo.

Kaggle `kernels logs` ek stream deta hai jisme ek hi line par kai JSON objects
jude hote hain: {"stream_name":"stdout","time":..,"data":".."},{".."}

Yeh script stdin se woh stream padhta hai, har object ka `data` nikalta hai,
escape sequences theek karta hai, aur jo JSON nahi hai use waise hi chhod deta hai.
Taa-ke `grep` se asli error mil sake (warna traceback JSON me chhup jata hai).

    kaggle kernels logs user/slug 2>&1 | python3 tools/kernel_logs.py
"""
from __future__ import annotations

import json
import sys


def extract(stream: str) -> str:
    out: list[str] = []
    dec = json.JSONDecoder()
    i, n = 0, len(stream)
    while i < n:
        # skip separators / whitespace / stray commas
        while i < n and stream[i] in " \t\r\n,":
            i += 1
        if i >= n:
            break
        if stream[i] != "{":
            j = stream.find("\n", i)
            j = n if j < 0 else j
            out.append(stream[i:j] + "\n")
            i = j + 1
            continue
        try:
            obj, end = dec.raw_decode(stream, i)
        except json.JSONDecodeError:
            j = stream.find("\n", i)
            j = n if j < 0 else j
            out.append(stream[i:j] + "\n")
            i = j + 1
            continue
        if isinstance(obj, dict) and "data" in obj:
            out.append(str(obj["data"]))
        i = end
    return "".join(out)


def main() -> int:
    text = sys.stdin.read()
    if text.lstrip().startswith("{") and '"stream_name"' in text[:400]:
        text = extract(text)
    sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
