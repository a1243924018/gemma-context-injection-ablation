#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 【执行脑: fuxiao-a】可复现性闸门：用 shipped judge 重算 v1..v4，逐版与 summary_v*.json 对账。
# 只读 + --dry，不写任何文件。任一行不一致 => exit 1。
import json, os, subprocess, sys

BASE = os.path.dirname(os.path.abspath(__file__))
VERSIONS = ["v1", "v2", "v3", "v4"]


def recompute(v):
    out = subprocess.run([sys.executable, os.path.join(BASE, "rescore_rubric.py"),
                          "--rubric=rubric_%s.json" % v, "--dry", "--json"],
                         capture_output=True, text=True, cwd=BASE)
    if out.returncode != 0:
        raise RuntimeError("rescore_rubric.py rc=%s stderr=%s" % (out.returncode, out.stderr[-400:]))
    line = [l for l in out.stdout.strip().splitlines() if l.startswith("{")][-1]
    return json.loads(line)


def main():
    print("%-4s %-18s %-18s %-10s %s" % ("ver", "published(A/B/C)", "recomputed(A/B/C)", "rubric_field", "verdict"))
    bad = 0
    for v in VERSIONS:
        pub = json.load(open(os.path.join(BASE, "summary_%s.json" % v), encoding="utf-8"))
        rec = recompute(v)
        p = {a: pub["arms"][a]["pass"] for a in sorted(pub["arms"])}
        r = {a: rec[a]["pass"] for a in sorted(rec)}
        rf_ok = pub.get("rubric") == "rubric_%s.json" % v
        ok = p == r and rf_ok
        bad += 0 if ok else 1
        print("%-4s %-18s %-18s %-10s %s" % (v, "".join(str(p[a]) for a in "ABC"),
                                             "".join(str(r[a]) for a in "ABC"),
                                             "OK" if rf_ok else "MISMATCH(%s)" % pub.get("rubric"),
                                             "PASS" if ok else "FAIL"))
    print("\nREPRO_OK=%s (%d/%d versions reproduce)" % (bad == 0, len(VERSIONS) - bad, len(VERSIONS)))
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
