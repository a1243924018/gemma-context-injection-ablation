#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""按 rubric_v1.json 重判已有应答（不重跑模型、不改原文）。
为什么要有这一步：第一版打分器把 expected_object 当字符列表遍历，导致 '的'/' ' 这种单字
即算命中 ⇒ 判据被击穿（假绿）。本文件是唯一判分实现，论文/表格只认它的输出。
用法: python3 rescore_rubric.py [--json]
"""
import json, os, re, sys

BASE = os.path.dirname(os.path.abspath(__file__))
RUBF = next((a.split("=",1)[1] for a in sys.argv if a.startswith("--rubric=")), "rubric_v1.json")
RUB = json.load(open(os.path.join(BASE, RUBF), encoding="utf-8"))
RAW = os.path.join(BASE, "raw.jsonl")


def judge(ans, rule):
    a = ans or ""
    ev = {}
    must = rule.get("must_any") or []
    hit = [t for t in must if t in a]
    ok_obj = bool(hit) if must else True
    groups = rule.get("any_of_groups") or []
    if groups and not any(any(t in a for t in grp) for grp in groups):
        ok_obj = False
        ev.setdefault("missing_any_group", ["|".join(g) for g in groups])
    for grp in rule.get("must_all_groups") or []:
        if not any(t in a for t in grp):
            ok_obj = False
            ev.setdefault("missing_group", []).append(grp)
    forbid = [t for t in (rule.get("forbid_any") or []) if t in a]
    q = a.count("?") + a.count("？")
    if rule.get("max_question_marks") is not None and q > rule["max_question_marks"]:
        ok_obj = False
    ok = ok_obj and not forbid
    ev.update({"must_hit": hit, "forbid_hit": forbid, "qmarks": q})
    return int(ok), ev


def main():
    rows = [json.loads(l) for l in open(RAW, encoding="utf-8")]
    out, table = [], {}
    for r in rows:
        rule = RUB.get(r["case_id"])
        if not rule:
            continue
        ok, ev = judge(r["answer"], rule)
        rec = {"arm": r["arm"], "case_id": r["case_id"], "ok": ok, "evidence": ev,
               "elapsed_s": r.get("elapsed_s"), "answer": r["answer"]}
        out.append(rec)
        table.setdefault(r["arm"], []).append(ok)
    print("臂   通过/总数   通过率   违规率")
    names = {"A": "A 裸", "B": "B 检索", "C": "C 全量"}
    summ = {}
    for a in sorted(table):
        v = table[a]
        rate = sum(v) / len(v)
        summ[a] = {"n": len(v), "pass": sum(v), "pass_rate": round(rate, 3), "violation_rate": round(1 - rate, 3)}
        print("%-6s %d/%d %10.2f %8.2f" % (names.get(a, a), sum(v), len(v), rate, 1 - rate))
    with open(os.path.join(BASE, "rescore_v2.jsonl"), "w", encoding="utf-8") as f:
        for rec in out:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    with open(os.path.join(BASE, re.sub(r"rubric_(v\d+)\.json", r"summary_\1.json", RUBF)), "w", encoding="utf-8") as f:
        json.dump({"model": rows[0]["model"], "rubric": "rubric_v1.json",
                   "arms": summ, "note": "judged by lexicon rubric; not model self-report"},
                  f, ensure_ascii=False, indent=1)
    print("\n逐例：")
    for rec in out:
        print("  %s %-34s %s %s" % (rec["arm"], rec["case_id"][:34], "PASS" if rec["ok"] else "FAIL",
                                    rec["evidence"]["forbid_hit"][:2] or rec["evidence"]["must_hit"][:2]))
    if "--json" in sys.argv:
        print(json.dumps(summ, ensure_ascii=False))


if __name__ == "__main__":
    main()
