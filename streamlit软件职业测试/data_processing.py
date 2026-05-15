# data_processing.py
import pandas as pd
import docx
import re
import json


# --- 1. 清洗 Excel 文件 (职业匹配库_霍兰德代码完整版.xlsx) ---
def load_holland_jobs(file_path):
    """
    加载 Excel 文件，提取霍兰德代码与职业的对应关系。
    返回一个字典，键是霍兰德三字母代码，值是职业列表。
    """
    try:
        df = pd.read_excel(file_path)
        # 假设第一列是霍兰德代码，第二列是职业名称
        # 请根据你的实际 Excel 表头调整列名
        # 示例：如果表头是 'Code' 和 'Job'
        jobs_dict = {}
        for _, row in df.iterrows():
            code = str(row.iloc[0]).strip()  # 第一列作为代码
            job = str(row.iloc[1]).strip()  # 第二列作为职业
            if code in jobs_dict:
                jobs_dict[code].append(job)
            else:
                jobs_dict[code] = [job]
        print(f"成功加载 {len(jobs_dict)} 个霍兰德代码及其对应的职业。")
        return jobs_dict
    except Exception as e:
        print(f"加载 Excel 文件时出错: {e}")
        return {}


# --- 2. 解析 Word 文档中的题目 ---
def extract_questions_from_docx(file_path, test_type):
    """
    从 Word 文档中提取题目。
    test_type: 用于区分不同类型的测试 ('mbti', 'holland', 'interest', 'values', 'talent', 'gallup')
    """
    try:
        doc = docx.Document(file_path)
        full_text = []
        for para in doc.paragraphs:
            full_text.append(para.text)
        text = '\n'.join(full_text)

        # 根据不同测试类型使用不同的正则表达式
        if test_type == 'holland':
            # 霍兰德可能有编号，如 "1. 我喜欢动手制作..."
            pattern = r'\d+\.\s*(.*?)(?=\n\d+\.|$)'
        else:
            # 其他测试通常没有编号，直接分行
            pattern = r'(.*?)(?=\n\s*\n|$)'  # 匹配非空行

        questions = re.findall(pattern, text, re.DOTALL)
        # 过滤掉空字符串和标题等无关内容
        questions = [q.strip() for q in questions if
                     q.strip() and not any(keyword in q.lower() for keyword in ['测试', '精简', '版', '题目', '说明'])]

        print(f"从 {file_path} 成功提取 {len(questions)} 个问题。")
        return questions
    except Exception as e:
        print(f"解析 Word 文件 {file_path} 时出错: {e}")
        return []


# --- 3. 加载所有数据 ---
def load_all_data():
    """
    加载所有测试题目和职业库。
    """
    print("--- 开始数据加载与清洗 ---")

    # 加载职业库
    holland_jobs = load_holland_jobs('职业匹配库_霍兰德代码完整版.xlsx')

    # 加载测试题目
    tests_data = {}
    tests_data['mbti'] = extract_questions_from_docx('MBTI 测试・精简版.docx', 'mbti')
    tests_data['holland'] = extract_questions_from_docx('霍兰德精简测试18.docx', 'holland')  # 现在加载全部18题
    tests_data['interest'] = extract_questions_from_docx('兴趣测试精简版.docx', 'interest')
    tests_data['values'] = extract_questions_from_docx('价值观测试精简版.docx', 'values')
    tests_data['talent'] = extract_questions_from_docx('才能测试精简版.docx', 'talent')
    tests_data['gallup'] = extract_questions_from_docx('盖洛普优势精简测试.docx', 'gallup')

    print("--- 数据加载与清洗完成 ---")
    return tests_data, holland_jobs


# --- 4. 保存清洗后的数据 (可选) ---
def save_processed_data(tests_data, holland_jobs, output_file='processed_data.json'):
    """
    将处理好的数据保存为 JSON 文件，方便主应用加载。
    """
    combined_data = {
        'tests_data': tests_data,
        'holland_jobs': holland_jobs
    }
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(combined_data, f, ensure_ascii=False, indent=2)
    print(f"处理后的数据已保存到 {output_file}")


if __name__ == "__main__":
    # 当直接运行此脚本时，执行数据加载和保存
    tests_data, holland_jobs = load_all_data()
    save_processed_data(tests_data, holland_jobs)