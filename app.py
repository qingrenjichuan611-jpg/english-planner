import random
import pandas as pd
import streamlit as st

st.set_page_config(page_title="英語学習計画ジェネレーター", layout="wide")

st.title("📚 英語学習計画ジェネレーター")
st.caption("時間が少ない週の優先度調整から、時間が多い週の追加メニュー配分まで自動最適化します。")

# 初期メニュー定義
DEFAULT_TASKS = [
    {"学習名": "DMM英会話", "時間(分)": 40, "週回数": 2, "性質": "output", "必ずやる": True, "1日1回まで": True, "週超過可": False, "優先度": 10},
    {"学習名": "英語日記", "時間(分)": 30, "週回数": 2, "性質": "output", "必ずやる": True, "1日1回まで": True, "週超過可": True, "優先度": 10},
    {"学習名": "5600 後半", "時間(分)": 15, "週回数": 7, "性質": "vocabulary", "必ずやる": True, "1日1回まで": True, "週超過可": True, "優先度": 10},
    {"学習名": "リスニング対策", "時間(分)": 30, "週回数": 3, "性質": "input", "必ずやる": False, "1日1回まで": False, "週超過可": True, "優先度": 8},
    {"学習名": "TOEFL Reading", "時間(分)": 50, "週回数": 1, "性質": "input", "必ずやる": False, "1日1回まで": False, "週超過可": True, "優先度": 8},
    {"学習名": "TOEFL Listening", "時間(分)": 50, "週回数": 1, "性質": "input", "必ずやる": False, "1日1回まで": False, "週超過可": True, "優先度": 8},
    {"学習名": "TOEFL Speaking L&R", "時間(分)": 20, "週回数": 1, "性質": "output", "必ずやる": False, "1日1回まで": False, "週超過可": True, "優先度": 8},
    {"学習名": "TOEFL Speaking TI", "時間(分)": 20, "週回数": 1, "性質": "output", "必ずやる": False, "1日1回まで": False, "週超過可": True, "優先度": 8},
    {"学習名": "TOEFL Writing Email", "時間(分)": 30, "週回数": 1, "性質": "output", "必ずやる": False, "1日1回まで": False, "週超過可": True, "優先度": 7},
    {"学習名": "TOEFL Writing AD", "時間(分)": 30, "週回数": 1, "性質": "output", "必ずやる": False, "1日1回まで": False, "週超過可": True, "優先度": 7},
    {"学習名": "5600 前半", "時間(分)": 30, "週回数": 2, "性質": "input", "必ずやる": False, "1日1回まで": False, "週超過可": True, "優先度": 7},
    {"学習名": "シンクロリーディング", "時間(分)": 20, "週回数": 1, "性質": "output", "必ずやる": False, "1日1回まで": False, "週超過可": True, "優先度": 6},
    {"学習名": "リピーティング", "時間(分)": 20, "週回数": 1, "性質": "output", "必ずやる": False, "1日1回まで": False, "週超過可": True, "優先度": 6},
]

DAYS = ["月", "火", "水", "木", "金", "土", "日"]
DEFAULT_MINUTES = [90, 90, 90, 90, 90, 120, 120]

# --- サイドバー：今週の勉強可能時間とバランス設定 ---
with st.sidebar:
    st.header("🗓️ 今週の勉強可能時間（分）")
    st.write("曜日ごとに確保できる時間を入力してください（0分〜600分）。")
    daily_caps = []
    for day, default_min in zip(DAYS, DEFAULT_MINUTES):
        val = st.number_input(f"{day}曜日（分）", min_value=0, max_value=600, value=default_min, step=5)
        daily_caps.append(int(val))

    total_available = sum(daily_caps)
    st.info(f"**今週の合計可能時間： {total_available} 分**（{total_available // 60}時間{total_available % 60}分）")

    st.divider()
    st.header("⚖️ 性質の目標比率")
    r_voc = st.slider("vocabulary 比率", 1, 10, 3)
    r_in = st.slider("input 比率", 1, 10, 6)
    r_out = st.slider("output 比率", 1, 10, 8)
    io_strictness = st.slider(
        "input : output バランス重視度",
        min_value=0.0,
        max_value=1.0,
        value=0.35,
        step=0.05,
        help="高いほど input と output の比率（6:8）を厳密に保ちます。",
    )

# --- メイン画面：メニュー設定（画面上で直接編集可能） ---
with st.expander("🛠️ 学習メニュー・回数・制限ルールの確認／編集（クリックで開閉）", expanded=False):
    st.write("セルをダブルクリックすると、時間・目標回数・1日上限・週超過可否・優先度をその場で変更できます。")
    edited_df = st.data_editor(
        pd.DataFrame(DEFAULT_TASKS),
        num_rows="dynamic",
        hide_index=True,
        column_config={
            "性質": st.column_config.SelectboxColumn("性質", options=["vocabulary", "input", "output"], required=True),
            "時間(分)": st.column_config.NumberColumn("時間(分)", min_value=5, max_value=240, step=5),
            "週回数": st.column_config.NumberColumn("目標週回数", min_value=1, max_value=7, step=1),
            "優先度": st.column_config.NumberColumn("優先度(1-10)", min_value=1, max_value=10, step=1),
        },
    )

tasks_df = edited_df.dropna(subset=["学習名", "時間(分)", "週回数", "性質"]).reset_index(drop=True)
for col in ["必ずやる", "1日1回まで", "週超過可"]:
    tasks_df[col] = tasks_df[col].fillna(False).astype(bool)
tasks_df["時間(分)"] = tasks_df["時間(分)"].fillna(20).astype(int)
tasks_df["週回数"] = tasks_df["週回数"].fillna(1).astype(int)
tasks_df["優先度"] = tasks_df["優先度"].fillna(5).astype(int)
tasks = tasks_df.to_dict("records")


def generate_day_patterns(tasks_list, cap):
    """1日あたりの制限時間内で可能なメニュー組み合わせ候補を生成する"""
    n = len(tasks_list)
    zero_pat = (0,) * n
    if cap <= 0 or n == 0:
        return [zero_pat]

    durations = [t["時間(分)"] for t in tasks_list]
    max_daily = []
    for t in tasks_list:
        if durations[len(max_daily)] > cap:
            max_daily.append(0)
        elif t["1日1回まで"]:
            max_daily.append(1)
        else:
            weekly_cap = 4 if t["週超過可"] else t["週回数"]
            max_daily.append(min(cap // t["時間(分)"], weekly_cap))

    patterns = {zero_pat}
    current = [0] * n

    # 1. 深さ優先探索で基本組み合わせを収集（同日重複なし〜1回重複まで優先）
    def dfs(idx, rem):
        if len(patterns) >= 900:
            return
        if idx == n:
            patterns.add(tuple(current))
            return
        limit = min(max_daily[idx], rem // durations[idx])
        # 多様性を出すため「1回 -> 0回 -> 2回以上」の順で探索
        order = []
        if limit >= 1:
            order.append(1)
        order.append(0)
        for c in range(2, limit + 1):
            order.append(c)

        for cnt in order:
            current[idx] = cnt
            dfs(idx + 1, rem - cnt * durations[idx])
            if len(patterns) >= 900:
                break
        current[idx] = 0

    dfs(0, cap)

    # 2. 時間が長い日でも空き時間をしっかり埋めるためのランダム貪欲候補を追加
    rng = random.Random(42 + cap)
    indices = list(range(n))
    for _ in range(350):
        rem = cap
        pat = [0] * n
        rng.shuffle(indices)
        for i in indices:
            if max_daily[i] > 0 and durations[i] <= rem:
                pat[i] = 1
                rem -= durations[i]
        # さらに余り時間があれば追加可能タスクを詰める
        rng.shuffle(indices)
        for i in indices:
            while pat[i] < max_daily[i] and durations[i] <= rem:
                pat[i] += 1
                rem -= durations[i]
        patterns.add(tuple(pat))

    return list(patterns)


def solve_schedule(tasks_list, caps, ratio_v, ratio_i, ratio_o, io_weight):
    """7日間の最適スケジュールをビームサーチ＋局所改善で探索する"""
    n = len(tasks_list)
    if n == 0:
        return {d: [] for d in range(7)}, []

    durations = [t["時間(分)"] for t in tasks_list]
    targets = [t["週回数"] for t in tasks_list]
    mandatory = [t["必ずやる"] for t in tasks_list]
    allow_extra = [t["週超過可"] for t in tasks_list]
    priorities = [t["優先度"] for t in tasks_list]
    cats = [t["性質"] for t in tasks_list]

    day_candidates = [generate_day_patterns(tasks_list, c) for c in caps]

    def score_plan(day_pats):
        num_d = len(day_pats)
        counts = [sum(day_pats[d][i] for d in range(num_d)) for i in range(n)]

        t_voc = 0
        t_in = 0
        t_out = 0
        base_score = 0.0
        extra_score = 0.0

        for i in range(n):
            c = counts[i]
            if not allow_extra[i] and c > targets[i]:
                return -1e18

            base_c = min(c, targets[i])
            extra_c = max(0, c - targets[i])
            mins = c * durations[i]

            if cats[i] == "vocabulary":
                t_voc += mins
            elif cats[i] == "input":
                t_in += mins
            else:
                t_out += mins

            if mandatory[i]:
                base_score += 3000.0 * base_c
            else:
                base_score += priorities[i] * durations[i] * base_c

            extra_score += 0.35 * priorities[i] * durations[i] * extra_c

        # 目標比率（特に input : output）とのズレを評価
        io_diff = abs(ratio_o * t_in - ratio_i * t_out) / max(1.0, (ratio_i + ratio_o) / 2.0)
        voc_diff = abs((ratio_i + ratio_o) * t_voc - ratio_v * (t_in + t_out)) / max(1.0, float(ratio_v + ratio_i + ratio_o))

        # 1日ごとの偏り・同日同メニュー重複・連続日の偏りを軽く抑制
        day_imb_pen = 0.0
        repeat_pen = 0.0
        consec_pen = 0.0

        for d in range(num_d):
            d_in = 0
            d_out = 0
            for i in range(n):
                cnt = day_pats[d][i]
                if cnt > 0:
                    if cats[i] == "input":
                        d_in += cnt * durations[i]
                    elif cats[i] == "output":
                        d_out += cnt * durations[i]
                    if cnt > 1:
                        repeat_pen += 22.0 * (cnt - 1)
                    if d > 0 and day_pats[d - 1][i] > 0 and targets[i] <= 3:
                        consec_pen += 12.0
            day_imb_pen += abs(d_in - d_out)

        penalty = (
            (io_weight * 14.0) * io_diff
            + 1.5 * voc_diff
            + 0.35 * day_imb_pen
            + repeat_pen
            + consec_pen
        )
        return base_score + extra_score - penalty

    # 7日間のビームサーチ
    beam = [((0,) * n, [])]  # (週間累計回数タプル, 日別パターンリスト)
    BEAM_WIDTH = 140

    for d in range(7):
        next_states = {}
        for counts_tup, hist in beam:
            for pat in day_candidates[d]:
                valid = True
                new_counts = [0] * n
                for i in range(n):
                    nc = counts_tup[i] + pat[i]
                    if not allow_extra[i] and nc > targets[i]:
                        valid = False
                        break
                    new_counts[i] = nc
                if not valid:
                    continue

                new_hist = hist + [pat]
                sc = score_plan(new_hist)
                key = tuple(new_counts)
                if key not in next_states or sc > next_states[key][0]:
                    next_states[key] = (sc, new_hist)

        ranked = sorted(next_states.items(), key=lambda kv: kv[1][0], reverse=True)[:BEAM_WIDTH]
        beam = [(k, v[1]) for k, v in ranked]

    best_hist = beam[0][1]
    best_sc = score_plan(best_hist)

    # 仕上げの局所改善（各曜日ごとにさらに良い組み合わせがないか総点検）
    for _ in range(2):
        improved = False
        for d in range(7):
            for pat in day_candidates[d]:
                if pat == best_hist[d]:
                    continue
                cand_hist = list(best_hist)
                cand_hist[d] = pat
                sc = score_plan(cand_hist)
                if sc > best_sc + 1e-6:
                    best_hist = cand_hist
                    best_sc = sc
                    improved = True
        if not improved:
            break

    schedule = {d: [] for d in range(7)}
    final_counts = [0] * n
    for d in range(7):
        for i in range(n):
            cnt = best_hist[d][i]
            if cnt > 0:
                schedule[d].append((tasks_list[i], cnt))
                final_counts[i] += cnt

    return schedule, final_counts


schedule, counts = solve_schedule(tasks, daily_caps, r_voc, r_in, r_out, io_strictness)

# --- 結果の表示 ---
st.subheader("📅 生成された週間学習スケジュール")

daily_rows = []
cat_totals = {"vocabulary": 0, "input": 0, "output": 0}

for d, day_name in enumerate(DAYS):
    day_items = schedule[d]
    day_items_sorted = sorted(day_items, key=lambda item: (not item[0]["必ずやる"], -item[0]["時間(分)"]))
    used_min = sum(t["時間(分)"] * cnt for t, cnt in day_items_sorted)
    for t, cnt in day_items_sorted:
        cat_totals[t["性質"]] += t["時間(分)"] * cnt

    menu_parts = []
    for t, cnt in day_items_sorted:
        star = "★" if t["必ずやる"] else ""
        mult = f"×{cnt}" if cnt > 1 else ""
        menu_parts.append(f"{star}{t['学習名']}({t['時間(分)']}分){mult}")

    menu_str = " / ".join(menu_parts)
    daily_rows.append(
        {
            "曜日": f"{day_name}曜",
            "可能時間": f"{daily_caps[d]}分",
            "計画合計": f"{used_min}分",
            "余り": f"{daily_caps[d] - used_min}分",
            "実施メニュー（★は必須）": menu_str if menu_str else "（休み・時間なし）",
        }
    )

st.dataframe(pd.DataFrame(daily_rows), hide_index=True)

# 2カラムでバランス分析と達成回数を表示
col1, col2 = st.columns([1, 1.4])

with col1:
    st.subheader("📊 性質バランス分析")
    total_planned = sum(cat_totals.values())
    st.metric("週間計画合計", f"{total_planned} 分（{total_planned // 60}時間{total_planned % 60}分）")

    if total_planned > 0:
        base = cat_totals["vocabulary"] / r_voc if cat_totals["vocabulary"] > 0 else (total_planned / (r_voc + r_in + r_out))
        actual_ratio_str = f"{cat_totals['vocabulary']/base:.1f} : {cat_totals['input']/base:.1f} : {cat_totals['output']/base:.1f}" if base > 0 else "-"
        st.write(f"**目標比率：** `{r_voc} : {r_in} : {r_out}` ／ **実績比率：** `{actual_ratio_str}`")

        balance_df = pd.DataFrame(
            {
                "性質": ["vocabulary", "input", "output"],
                "合計時間(分)": [cat_totals["vocabulary"], cat_totals["input"], cat_totals["output"]],
                "構成比(%)": [
                    round(cat_totals["vocabulary"] / total_planned * 100, 1),
                    round(cat_totals["input"] / total_planned * 100, 1),
                    round(cat_totals["output"] / total_planned * 100, 1),
                ],
            }
        )
        st.dataframe(balance_df, hide_index=True)

with col2:
    st.subheader("✅ メニュー別の計画回数")
    summary_rows = []
    for i, t in enumerate(tasks):
        target = int(t["週回数"])
        done = counts[i]
        if done > target:
            status = f"追加実施 (+{done - target}回)"
        elif done == target:
            status = "目標達成"
        elif done > 0:
            status = "一部調整"
        else:
            status = "今週見送り"

        summary_rows.append(
            {
                "学習名": f"{'★' if t['必ずやる'] else ''}{t['学習名']}",
                "性質": t["性質"],
                "計画 / 目標": f"{done} / {target} 回",
                "状態": status,
            }
        )
    summary_df = pd.DataFrame(summary_rows)
    st.dataframe(summary_df, hide_index=True)

# CSVダウンロード
csv_data = pd.DataFrame(daily_rows).to_csv(index=False).encode("utf-8-sig")
st.download_button("📥 この週間スケジュールをCSVで保存", data=csv_data, file_name="english_study_plan.csv", mime="text/csv")