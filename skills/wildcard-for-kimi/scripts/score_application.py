#!/usr/bin/env python3
"""Kimi Talk 报名小助手 — 深度用户规则打分。

用法:
  python3 score_application.py '<proof-json 字符串>'
  python3 score_application.py proof.json          # 或文件路径
  echo '<json>' | python3 score_application.py -   # 或标准输入

proof JSON 字段（均可缺省）:
  plan               当前套餐名称（含"会员/Pro/Ultra/Max"等视为付费）
  usage              当前用量描述（如 "850/1000"、"高强度"）
  member_since       最早订阅时间（YYYY-MM / YYYY年M月 / ISO 均可）
  subscription_count 历史订阅条数（int 或数字字符串）
  note               备注（如 "手工解析"）

输出（stdout，紧凑 JSON）: {"score": int, "decision": fast_pass|fast_review|standard, "reasons": [...]}
退出码恒为 0；输入非法时 decision=standard 并给出原因。
"""
import json
import re
import sys
from datetime import datetime, timezone


def load_proof() -> dict:
    arg = sys.argv[1] if len(sys.argv) > 1 else "-"
    raw = sys.stdin.read() if arg == "-" else (open(arg, encoding="utf-8").read() if arg.endswith(".json") else arg)
    try:
        data = json.loads(raw)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def months_since(value) -> int:
    if not value:
        return 0
    s = str(value)
    m = re.search(r"(20\d{2})\D{0,2}(\d{1,2})", s)
    if not m:
        return 0
    try:
        start = datetime(int(m.group(1)), int(m.group(2)), 1, tzinfo=timezone.utc)
    except ValueError:
        return 0
    now = datetime.now(timezone.utc)
    return max(0, (now.year - start.year) * 12 + now.month - start.month)


def main() -> None:
    proof = load_proof()
    score, reasons = 0, []

    plan = str(proof.get("plan") or "")
    # 付费梯级：现行 Go/Plus/Pro/Max + 存量 Andante/Moderato/Allegro（2026-09 实测页面梯级名）
    if re.search(r"会员|Go\b|Plus|Pro\b|Ultra|Max|付费|premium|Allegro|Moderato|Andante", plan, re.I):
        score += 40
        reasons.append(f"付费套餐(+40): {plan}")

    # 订阅仍在有效期内（valid_until 为未来日期）才算数，过期套餐不加分
    vu = str(proof.get("valid_until") or "")
    vm = re.match(r"(20\d{2})-(\d{2})-(\d{2})", vu)
    if vm:
        try:
            from datetime import date
            expiry = date(int(vm.group(1)), int(vm.group(2)), int(vm.group(3)))
            if expiry >= date.today():
                score += 20
                reasons.append(f"订阅在有效期内(+20): 至 {vu}")
        except ValueError:
            pass

    months = months_since(proof.get("member_since"))
    if months >= 12:
        score += 40
        reasons.append(f"订阅 {months} 个月(+40)")
    elif months >= 6:
        score += 30
        reasons.append(f"订阅 {months} 个月(+30)")
    elif months >= 3:
        score += 20
        reasons.append(f"订阅 {months} 个月(+20)")

    try:
        count = int(proof.get("subscription_count") or 0)
    except (TypeError, ValueError):
        count = 0
    if count >= 2:
        score += 10
        reasons.append(f"历史订阅 {count} 条(+10)")

    usage = str(proof.get("usage") or "")
    um = re.search(r"(\d+(?:\.\d+)?)\s*/\s*(\d+)", usage)
    if um and float(um.group(2)) > 0 and float(um.group(1)) / float(um.group(2)) >= 0.5:
        score += 20
        reasons.append(f"用量活跃(+20): {usage}")
    elif re.search(r"高|活跃|heavy|active", usage, re.I):
        score += 20
        reasons.append(f"用量活跃(+20): {usage}")

    # usage_percent：订阅页「总使用量」百分比（2026-09 实测字段），>=50% 视为活跃
    up = proof.get("usage_percent")
    try:
        if up is not None and float(up) >= 50:
            score += 20
            reasons.append(f"用量活跃(+20): 总使用量 {up}%")
    except (TypeError, ValueError):
        pass

    # code_usage：Kimi Code 分窗口用量，任一窗口 >=30% 加 10（深度使用的辅助信号）
    cu = proof.get("code_usage") or {}
    try:
        if any(float(cu.get(k)) >= 30 for k in ("hours5", "days7") if cu.get(k) is not None):
            score += 10
            reasons.append(f"Code 用量活跃(+10): {cu}")
    except (TypeError, ValueError):
        pass

    if not reasons:
        reasons.append("无有效订阅证明，回落普通通道")

    decision = "fast_pass" if score >= 60 else ("fast_review" if score >= 40 else "standard")
    print(json.dumps({"score": score, "decision": decision, "reasons": reasons}, ensure_ascii=False))


if __name__ == "__main__":
    main()
