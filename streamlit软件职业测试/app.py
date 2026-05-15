# app.py
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly.express as px
import time
import json
import random
from data_processing import load_all_data  # 导入数据加载函数


# --- 0. 加载数据 ---
@st.cache_data
def get_data():
    """缓存数据加载，避免重复读取文件"""
    return load_all_data()


tests_data_raw, holland_jobs_db = get_data()

# --- 1. 初始化 Session State ---
if 'current_test_index' not in st.session_state:
    st.session_state.current_test_index = 0
if 'answers' not in st.session_state:
    st.session_state.answers = {k: [] for k in tests_data_raw.keys()}
if 'completed_tests' not in st.session_state:
    st.session_state.completed_tests = []
if 'results' not in st.session_state:
    st.session_state.results = {}
if 'user_id' not in st.session_state:
    st.session_state.user_id = f"user_{int(time.time())}"
if 'all_tests_completed' not in st.session_state:
    st.session_state.all_tests_completed = False
if 'final_report' not in st.session_state:
    st.session_state.final_report = {}
if 'start_time' not in st.session_state:
    st.session_state.start_time = time.time()

# --- 2. 测试配置 (更新霍兰德题目数量为18) ---
TESTS_CONFIG = [
    {"id": "mbti", "name": "MBTI 性格测试", "num_questions": 6, "options": ["倾向于前者", "倾向于后者"]},
    {"id": "holland", "name": "霍兰德职业兴趣测试", "num_questions": 18,
     "options": ["非常不符合", "比较不符合", "不确定", "比较符合", "非常符合"]},  # 使用全部18题
    {"id": "interest", "name": "兴趣倾向测试", "num_questions": 6,
     "options": ["非常不符合", "比较不符合", "不确定", "比较符合", "非常符合"]},
    {"id": "values", "name": "价值观测试", "num_questions": 6,
     "options": ["非常不重要", "比较不重要", "一般", "比较重要", "非常重要"]},
    {"id": "talent", "name": "才能测试", "num_questions": 6,
     "options": ["非常不符合", "比较不符合", "不确定", "比较符合", "非常符合"]},
    {"id": "gallup", "name": "盖洛普优势测试", "num_questions": 6,
     "options": ["非常不符合", "比较不符合", "不确定", "比较符合", "非常符合"]}
]


# --- 3. 计算函数 ---
def calculate_mbti_result(answers):
    """根据答案计算 MBTI 类型"""
    if not answers or len(answers) < 6: return {'type': 'Unknown', 'scores': {}}

    # 假设题目严格按照 E/I, S/N, T/F, J/P 顺序交替
    # 答案 0 代表 "倾向于前者" (E, S, T, J)，答案 4 代表 "倾向于后者" (I, N, F, P)
    e_score = sum(1 for i, a in enumerate(answers) if i % 2 == 0 and a < 2) + \
              sum(1 for i, a in enumerate(answers) if i % 2 == 1 and a > 2)
    i_score = sum(1 for i, a in enumerate(answers) if i % 2 == 0 and a > 2) + \
              sum(1 for i, a in enumerate(answers) if i % 2 == 1 and a < 2)
    s_score = sum(1 for i, a in enumerate(answers) if i % 4 in [0, 1] and a < 2) + \
              sum(1 for i, a in enumerate(answers) if i % 4 in [2, 3] and a > 2)
    n_score = sum(1 for i, a in enumerate(answers) if i % 4 in [0, 1] and a > 2) + \
              sum(1 for i, a in enumerate(answers) if i % 4 in [2, 3] and a < 2)
    t_score = sum(1 for i, a in enumerate(answers) if i % 4 in [0, 2] and a < 2) + \
              sum(1 for i, a in enumerate(answers) if i % 4 in [1, 3] and a > 2)
    f_score = sum(1 for i, a in enumerate(answers) if i % 4 in [0, 2] and a > 2) + \
              sum(1 for i, a in enumerate(answers) if i % 4 in [1, 3] and a < 2)
    j_score = sum(1 for i, a in enumerate(answers) if i % 4 in [0, 3] and a < 2) + \
              sum(1 for i, a in enumerate(answers) if i % 4 in [1, 2] and a > 2)
    p_score = sum(1 for i, a in enumerate(answers) if i % 4 in [0, 3] and a > 2) + \
              sum(1 for i, a in enumerate(answers) if i % 4 in [1, 2] and a < 2)

    mbti_type = (
        "E" if e_score >= i_score else "I" +
                                       "S" if s_score >= n_score else "N" +
                                                                      "T" if t_score >= f_score else "F" +
                                                                                                     "J" if j_score >= p_score else "P"
    )
    scores = {'E': e_score, 'I': i_score, 'S': s_score, 'N': n_score, 'T': t_score, 'F': f_score, 'J': j_score,
              'P': p_score}
    return {'type': mbti_type, 'scores': scores}


def calculate_holland_result(answers):
    """根据答案计算霍兰德 Top 3 代码 (使用18题)"""
    if not answers or len(answers) < 18: return {'top_codes': [], 'scores': {}}

    # 霍兰德代码顺序: R, I, A, S, E, C (循环 3次，共18题)
    codes_order = ['R', 'I', 'A', 'S', 'E', 'C'] * 3
    holland_scores = {'R': 0, 'I': 0, 'A': 0, 'S': 0, 'E': 0, 'C': 0}

    for i, raw_answer_score in enumerate(answers):
        # 将 likert 量表 (0-4) 转换为计分 (1-5)，更符合霍兰德理论
        score = raw_answer_score + 1
        code = codes_order[i]
        holland_scores[code] += score

    sorted_codes = sorted(holland_scores.items(), key=lambda x: x[1], reverse=True)
    top_three = [code for code, _ in sorted_codes[:3]]
    return {'top_codes': top_three, 'scores': holland_scores}


def calculate_generic_result(answers):
    """计算其他测试的总分和平均分"""
    if not answers: return {'total_score': 0, 'average_score': 0, 'raw_answers': answers}
    total_score = sum(answers)
    average_score = total_score / len(answers)
    return {'total_score': total_score, 'average_score': round(average_score, 2), 'raw_answers': answers}


# --- 4. 职业推荐函数 ---
def recommend_jobs(mbti_type, holland_top_codes, interest_scores, values_scores, talent_scores, gallup_scores,
                   holland_jobs_db):
    """基于所有测试结果推荐 Top 5 职业"""
    job_scores = {}

    # 1. 霍兰德匹配 (权重最高)
    for code in holland_top_codes:
        if code in holland_jobs_db:
            for job in holland_jobs_db[code]:
                if job not in job_scores:
                    job_scores[job] = 0
                job_scores[job] += 3  # 给Top3代码的职业高分

    # 2. 其他维度简单加权 (可以根据需要调整)
    # 这里仅为示例，实际应用中需要更复杂的模型
    # 假设兴趣、价值观、才能得分越高越好
    generic_score = interest_scores.get('total_score', 0) + \
                    values_scores.get('total_score', 0) + \
                    talent_scores.get('total_score', 0)

    # 对所有已评分职业增加通用分数
    for job in job_scores:
        job_scores[job] += generic_score * 0.01  # 简单加权，避免压倒霍兰德分数

    # 排序并返回 Top 5
    sorted_jobs = sorted(job_scores.items(), key=lambda x: x[1], reverse=True)
    top_5_jobs = sorted_jobs[:5]

    return [{'job': job, 'score': score} for job, score in top_5_jobs]


# --- 5. 主应用 UI ---
st.markdown(
    """
    <style>
    .stApp {
        background-color: #E6F3FF; /* 淡蓝色背景 */
    }
    .stRadio > div, .stSelectbox > div {
        background-color: #FFF8DC !important; /* 米色选项背景 */
        border-radius: 5px;
        padding: 5px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("🧠 欢迎参加职业性格测试！")

# 计算总进度和时间
total_questions = sum(t['num_questions'] for t in TESTS_CONFIG)
answered_questions = sum(len(st.session_state.answers[t['id']]) for t in TESTS_CONFIG)
remaining_questions = total_questions - answered_questions
elapsed_time = time.time() - st.session_state.start_time
estimated_total_time = (elapsed_time / answered_questions) * total_questions if answered_questions > 0 else 0
remaining_time = estimated_total_time - elapsed_time

if not st.session_state.all_tests_completed:
    current_test_config = TESTS_CONFIG[st.session_state.current_test_index]
    current_test_id = current_test_config["id"]
    current_test_name = current_test_config["name"]
    num_q = current_test_config["num_questions"]
    options = current_test_config["options"]

    # 获取当前测试的题目（取指定数量）
    questions = tests_data_raw[current_test_id][:num_q]

    st.header(current_test_name)
    st.progress((st.session_state.current_test_index + 1) / len(TESTS_CONFIG))
    st.caption(f"模块 {st.session_state.current_test_index + 1}/{len(TESTS_CONFIG)} | "
               f"题目 {answered_questions + 1}/{total_questions} | "
               f"剩余 {remaining_questions} 题 | "
               f"预计剩余时间: {max(0, int(remaining_time))} 秒")

    answers_for_current_test = st.session_state.answers[current_test_id].copy()

    for i, q_text in enumerate(questions):
        key = f"{current_test_id}_q{i}"
        while len(answers_for_current_test) <= i:
            answers_for_current_test.append(None)

        selected_option = st.radio(
            label=f"Q{i + 1}: {q_text}",
            options=options,
            index=answers_for_current_test[i] if answers_for_current_test[i] is not None else 0,
            key=key,
            horizontal=True
        )
        answers_for_current_test[i] = options.index(selected_option)

    st.session_state.answers[current_test_id] = answers_for_current_test

    col1, col2 = st.columns(2)
    with col1:
        if st.button("上一个") and st.session_state.current_test_index > 0:
            st.session_state.current_test_index -= 1
            st.rerun()
    with col2:
        if st.button("提交并进入下一个"):
            if any(ans is None for ans in answers_for_current_test):
                st.warning("请完成所有题目后再提交！")
            else:
                # 计算当前测试结果
                if current_test_id == "mbti":
                    result = calculate_mbti_result(answers_for_current_test)
                elif current_test_id == "holland":
                    result = calculate_holland_result(answers_for_current_test)  # 现在会处理18个答案
                else:
                    result = calculate_generic_result(answers_for_current_test)

                st.session_state.results[current_test_id] = result
                if current_test_id not in st.session_state.completed_tests:
                    st.session_state.completed_tests.append(current_test_id)

                if st.session_state.current_test_index < len(TESTS_CONFIG) - 1:
                    st.session_state.current_test_index += 1
                    st.rerun()
                else:
                    st.session_state.all_tests_completed = True
                    st.rerun()

else:
    # --- 结果展示页 ---
    st.header("📊 测试完成！这是您的综合报告")

    if not st.session_state.final_report:
        # 生成综合报告
        report = {
            "user_id": st.session_state.user_id,
            "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "summary": {
                "title": "全能职业性格综合分析报告",
                "date": time.strftime("%Y年%m月%d日"),
                "location": "互联网"
            },
            "sections": {},
            "top_jobs": []
        }

        # 添加各个模块的结果
        for test_cfg in TESTS_CONFIG:
            test_id = test_cfg["id"]
            if test_id in st.session_state.results:
                res = st.session_state.results[test_id]
                report["sections"][test_id] = {
                    "title": test_cfg["name"],
                    "result": res
                }

        # 生成职业推荐
        mbti_res = st.session_state.results.get("mbti", {})
        holland_res = st.session_state.results.get("holland", {})
        interest_res = st.session_state.results.get("interest", {})
        values_res = st.session_state.results.get("values", {})
        talent_res = st.session_state.results.get("talent", {})
        gallup_res = st.session_state.results.get("gallup", {})

        top_jobs = recommend_jobs(
            mbti_res.get('type', ''),
            holland_res.get('top_codes', []),
            interest_res, values_res, talent_res, gallup_res,
            holland_jobs_db
        )
        report["top_jobs"] = top_jobs
        st.session_state.final_report = report

    # 显示 Top 5 职业
    st.subheader("🏆 您的 Top 5 推荐职业")
    if st.session_state.final_report["top_jobs"]:
        for i, job_info in enumerate(st.session_state.final_report["top_jobs"]):
            st.metric(label=f"第 {i + 1} 名", value=job_info['job'], delta=f"匹配度: {job_info['score']:.2f}")
    else:
        st.write("未能生成职业推荐，请检查数据或算法。")

    # --- 可视化部分 ---
    st.subheader("📈 结果可视化")

    # 1. MBTI 雷达图
    if "mbti" in st.session_state.results:
        mbti_res = st.session_state.results["mbti"]
        if mbti_res['scores']:
            fig_mbti = go.Figure(data=go.Scatterpolar(
                r=list(mbti_res['scores'].values()),
                theta=list(mbti_res['scores'].keys()),
                fill='toself',
                name='MBTI Scores',
                line_color='#007ACC',  # 淡蓝色
                fillcolor='#ADD8E6'  # 更浅的蓝色填充
            ))
            fig_mbti.update_layout(
                polar=dict(
                    radialaxis=dict(
                        visible=True,
                        range=[0, max(mbti_res['scores'].values()) * 1.2]  # 设置合适的范围
                    )),
                showlegend=False,
                title="MBTI 维度得分",
                height=400
            )
            st.plotly_chart(fig_mbti, use_container_width=True)

    # 2. 霍兰德柱状图 (现在显示6个维度的得分)
    if "holland" in st.session_state.results:
        holland_res = st.session_state.results["holland"]
        if holland_res['scores']:
            df_holland = pd.DataFrame(list(holland_res['scores'].items()), columns=['Code', 'Score'])
            fig_holland = px.bar(df_holland, x='Code', y='Score',
                                 title='霍兰德六边形得分 (基于18题)',
                                 color_discrete_sequence=['#007ACC'])  # 淡蓝色
            fig_holland.update_layout(height=400)
            st.plotly_chart(fig_holland, use_container_width=True)

    # 3. 其他测试得分柱状图
    other_tests = ['interest', 'values', 'talent', 'gallup']
    for test_id in other_tests:
        if test_id in st.session_state.results:
            res = st.session_state.results[test_id]
            if 'average_score' in res:
                st.subheader(f"{TESTS_CONFIG[[t['id'] for t in TESTS_CONFIG].index(test_id)]['name']} - 平均得分")
                st.metric(label="平均分", value=res['average_score'])

    # 下载报告
    json_str = json.dumps(st.session_state.final_report, ensure_ascii=False, indent=2)
    st.download_button(
        label="📥 下载完整报告 (JSON)",
        data=json_str,
        file_name=f"career_test_report_{st.session_state.user_id}.json",
        mime="application/json"
    )

    if st.button("重新开始测试"):
        for key in list(st.session_state.keys()):
            if key != 'start_time':  # 保留 start_time 以便计算总用时
                del st.session_state[key]
        st.session_state.start_time = time.time()
        st.rerun()