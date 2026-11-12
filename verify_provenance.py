#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 【执行脑: fuxiao-a】 brain_id=fuxiao-a  判据溯源闸门（知微 ZW_A_KAGGLE_PAPER_V2_20261112_R1 §Q2 验收门槛）
"""判据溯源闸门 —— 把知微 ZW_A_KAGGLE_PAPER_V2_20261112_R1 §Q2 的验收门槛机器化。

她给的门槛（逐条对应本脚本的 CHECK）：
  T1 24 条原始回答全部能定位                     -> raw.jsonl 24 格 + key 映射 S01..S24 全覆盖
  T2 每版总体结果均可从逐行标签重新计算          -> 用 shipped judge(rescore_rubric.py) 重算 v1..v4，
                                                   逐条与 traceability_24.csv 对账，聚合与 summary_v*.json 对账
  T3 两个人工分歧项不被静默剔除                  -> 分歧项必须出现在表里且 final_metric_included=no(保守口径计违规)
  T4 κ=0.80 能从两名评审原始标签复算             -> 用 verdicts_*.jsonl 现算 agree/kappa
  T5 (她机读块的硬要求) 2/24 必须版本绑定        -> 只有 v4 是 2/24；正文里 "2 of 24" 附近必须写明版本

非真空对照：--control 会把 S15 的一个标签翻转，闸门必须从 PASS 翻成 FAIL，否则判闸门失效。
只读：不写任何文件（--control 只在内存里改）。
"""
import csv
import json
import os
import re
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
SEM = "/mnt/d/fuxiao/tmp/semantic_blind"
KEY = "/mnt/d/fuxiao/tmp/blind_semantic_key.json"
PAPER = os.path.join(BASE, "PAPER_KAGGLE_CONDENSED.md")
CSV = os.path.join(BASE, "traceability_24.csv")
VERS = ("v1", "v2", "v3", "v4")


def judge_pairs(ver):
    """调用唯一判分实现，解析逐条结果。禁在本地重写判据（PIT-0002）。"""
    import subprocess
    out = subprocess.run([sys.executable, os.path.join(BASE, "rescore_rubric.py"),
                          "--rubric=rubric_%s.json" % ver, "--dry", "--json"],
                         capture_output=True, text=True, cwd=BASE)
    if out.returncode != 0:
        raise RuntimeError("rescore_rubric %s rc=%s %s" % (ver, out.returncode, out.stderr[-400:]))
    pairs, agg = {}, None
    for line in out.stdout.splitlines():
        m = re.match(r"^\s+([ABC])\s+(\S+)\s+(PASS|FAIL)", line)
        if m:
            pairs[(m.group(2), m.group(1))] = m.group(3)
        if line.startswith("{"):
            agg = json.loads(line)
    return pairs, agg


def load_humans():
    def rd(p):
        d = {}
        for line in open(p, encoding="utf-8"):
            line = line.strip()
            if line:
                o = json.loads(line)
                d[o["id"]] = "PASS" if str(o.get("verdict", "")).upper().startswith("PASS") else "FAIL"
        return d
    return rd(os.path.join(SEM, "verdicts_zhixing.jsonl")), rd(os.path.join(SEM, "verdicts_fuxiao-test.jsonl"))


def cohen_kappa(a, b):
    n = len(a)
    pa = sum(1 for x, y in zip(a, b) if x == y) / n
    p1, p2 = sum(a) / n, sum(b) / n
    pe = p1 * p2 + (1 - p1) * (1 - p2)
    return (pa - pe) / (1 - pe)


def main():
    control = "--control" in sys.argv
    key = json.load(open(KEY, encoding="utf-8"))
    h1, h2 = load_humans()
    rows = list(csv.DictReader(open(CSV, encoding="utf-8")))
    checks = []

    def chk(name, ok, detail=""):
        checks.append((name, bool(ok), detail))

    # T1 覆盖
    ids = [r["id"] for r in rows]
    chk("T1_24_CELLS_PRESENT", len(rows) == 24 and len(set(ids)) == 24,
        "rows=%d unique=%d key=%d" % (len(rows), len(set(ids)), len(key)))
    chk("T1_KEY_BIJECTIVE", set(ids) == set(key.keys()),
        "only_csv=%s only_key=%s" % (sorted(set(ids) - set(key))[:3], sorted(set(key) - set(ids))[:3]))

    # 逐版重算 + 逐行对账 + 聚合对账
    by_ver = {}
    for v in VERS:
        pairs, agg = judge_pairs(v)
        by_ver[v] = pairs
        mism = [(r["id"], v, pairs.get((r["case_id"], r["arm"])), r[v]) for r in rows
                if pairs.get((r["case_id"], r["arm"])) != r[v]]
        chk("T2_ROWMATCH_%s" % v, not mism, "mismatch=%d %s" % (len(mism), mism[:3]))
        pub = json.load(open(os.path.join(BASE, "summary_%s.json" % v), encoding="utf-8"))
        agg_ok = all(agg[a]["pass"] == pub["arms"][a]["pass"] for a in "ABC")
        chk("T2_AGG_%s" % v, agg_ok,
            "recomputed=%s published=%s" % ("".join(str(agg[a]["pass"]) for a in "ABC"),
                                            "".join(str(pub["arms"][a]["pass"]) for a in "ABC")))

    # T3 分歧项不被剔除
    split = [i for i in ids if h1[i] != h2[i]]
    split_rows = [r for r in rows if r["id"] in split]
    chk("T3_SPLITS_KEPT", len(split) == 2 and len(split_rows) == 2
        and all(r["final_metric_included"].startswith("no") for r in split_rows)
        and all(r["agreement"] == "SPLIT" for r in split_rows), "splits=%s" % split)

    # T4 一致率 / kappa / 分臂率
    a = [h1[i] == "PASS" for i in ids]
    b = [h2[i] == "PASS" for i in ids]
    if control:                      # 非真空对照：翻转一条，指标必须动
        idx = ids.index("S15")
        b[idx] = not b[idx]
    agree = sum(1 for x, y in zip(a, b) if x == y)
    kap = cohen_kappa(a, b)
    chk("T4_AGREEMENT_22_OF_24", agree == 22, "agree=%d/%d" % (agree, len(ids)))
    chk("T4_KAPPA_0_80", abs(kap - 0.80) <= 0.005, "kappa=%.4f" % kap)

    def rates(consistent_only):
        out = {}
        for arm in "ABC":
            tot = viol = 0
            for r in rows:
                if r["arm"] != arm:
                    continue
                i = r["id"]
                if consistent_only and h1[i] != h2[i]:
                    continue
                tot += 1
                if h1[i] == "FAIL" or (not consistent_only and h2[i] == "FAIL"):
                    viol += 1
            out[arm] = (viol, tot)
        return out
    cons, consv = rates(True), rates(False)
    chk("T4_CONSENSUS_RATES", cons == {"A": (5, 8), "B": (1, 7), "C": (0, 7)},
        str({k: "%d/%d" % v for k, v in cons.items()}))
    chk("T4_CONSERVATIVE_RATES", consv == {"A": (5, 8), "B": (2, 8), "C": (1, 8)},
        str({k: "%d/%d" % v for k, v in consv.items()}))

    # T5 版本绑定
    dis = {}
    for v in VERS:
        dis[v] = sorted(i for i in ids
                        if h1[i] == h2[i] and by_ver[v][(key[i]["case_id"], key[i]["arm"])] != h1[i])
    chk("T5_DISAGREE_COUNTS", {v: len(x) for v, x in dis.items()} == {"v1": 9, "v2": 9, "v3": 5, "v4": 2},
        str({v: len(x) for v, x in dis.items()}))
    chk("T5_V4_PAIR_IS_C01", [key[i]["arm"] for i in dis["v4"]] == ["A", "B"]
        and all(key[i]["case_id"].startswith("C01") for i in dis["v4"]), str(dis["v4"]))

    # 正文断言：语义不一致数必须带版本 + 必须用「两位读者一致」的 22 分母
    # 2026-11-12 知微 P0-1 裁决：consensus 的分母只能是 22（C04·B / C04·C 单列），
    # 原 "2 of 24" 口径在统计上不成立（不同版本临时选用不同评审标签）⇒ 判据同步收窄，
    # 并额外禁止裸 24 分母回潮。
    paper = open(PAPER, encoding="utf-8").read()
    bound = False
    for m in re.finditer(r"2 of 22", paper):
        win = paper[max(0, m.start() - 220): m.end() + 220]
        if "v4" in win:
            bound = True
    chk("T5_PAPER_BINDS_V4", bound, "occurrences=%d" % len(re.findall(r"2 of 22", paper)))
    naked = re.findall(r"2 of 24|5/24|9/24", paper)
    chk("T5_NO_BARE_24_DENOM", not naked, "hits=%s" % naked)
    chk("PAPER_TITLE_METHODOLOGICAL",
        "When the Rubric Changes the Winner" in paper, paper.splitlines()[0][:80])
    missing = [r["id"] for r in rows
               if not re.search(r"\|\s*%s\s*\|\s*(?:S\d+\s*\|\s*)?%s\s*\|" % (r["case"], r["arm"]), paper)]
    chk("PAPER_APPENDIX_24_ROWS", not missing, "missing=%s" % missing)

    bad = [c for c in checks if not c[1]]
    print("%-28s %-6s %s" % ("CHECK", "RESULT", "DETAIL"))
    for name, ok, detail in checks:
        print("%-28s %-6s %s" % (name, "PASS" if ok else "FAIL", detail))
    print("\nPROVENANCE_OK=%s  (%d/%d)" % (not bad, len(checks) - len(bad), len(checks)))
    if control:
        print("CONTROL_MODE=1 -> 期望整体 FAIL；实得 %s" % ("FAIL(正确)" if bad else "PASS(闸门失效!)"))
        return 0 if bad else 3
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
