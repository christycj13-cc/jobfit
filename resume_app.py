import streamlit as st
import json
import os
import anthropic

DATA_FILE = "experience.json"
CONVERSATION_FILE = "conversation.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"基础信息": [], "技能": [], "经历片段": [], "性格与软实力": []}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_conversation():
    if os.path.exists(CONVERSATION_FILE):
        with open(CONVERSATION_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return None

def save_conversation(messages, keywords):
    with open(CONVERSATION_FILE, "w", encoding="utf-8") as f:
        json.dump({"messages": messages, "keywords": keywords}, f, ensure_ascii=False, indent=2)

def clear_conversation():
    if os.path.exists(CONVERSATION_FILE):
        os.remove(CONVERSATION_FILE)

def extract_confirmed_keywords(client, messages):
    if len(messages) < 2:
        return []
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=512,
        system="""从对话中提取用户已完整分享的职业亮点（有具体细节的经历）。
每个亮点一行，格式：关键词||一句话描述
只输出格式内容，没有就输出"无"。""",
        messages=[{"role": "user", "content": f"对话记录：\n{json.dumps(messages[-4:], ensure_ascii=False)}"}]
    )
    text = response.content[0].text.strip()
    if text == "无" or not text:
        return []
    keywords = []
    for line in text.split('\n'):
        if '||' in line:
            parts = line.split('||', 1)
            if len(parts) == 2:
                keywords.append({"keyword": parts[0].strip(), "detail": parts[1].strip()})
    return keywords

def extract_pending_topic(client, messages):
    if len(messages) < 2:
        return None
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=100,
        system="""根据对话，AI顾问正在追问用户关于哪个话题？用3-6个字概括正在挖掘的主题。
只输出主题词，没有正在追问的话题就输出"无"。""",
        messages=[{"role": "user", "content": f"对话记录：\n{json.dumps(messages[-2:], ensure_ascii=False)}"}]
    )
    text = response.content[0].text.strip()
    return None if text == "无" else text

ONBOARDING_SYSTEM = """你是一名经验丰富的职业顾问，通过轻松的对话了解用户的背景和经历，帮助他们发现简历中值得强调的亮点。

行为规则：
1. 语气平等、友好、中立，像朋友聊天一样自然
2. 主动引导用户分享具体经历（时间、背景、你的贡献、结果）
3. 当用户累计分享了3个有价值的经历后，主动询问是否结束并生成总结

开场白：先用一句话介绍自己的角色，然后问用户最近在关注什么类型的工作机会。"""

data = load_data()
client = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])

# 侧边栏：只在了解我Tab激活时显示关键词
if "onboarding_started" in st.session_state and st.session_state.onboarding_started:
    with st.sidebar:
        st.subheader("已发现的亮点")
        if st.session_state.get("onboarding_keywords"):
            for kw in st.session_state.onboarding_keywords:
                with st.popover(f"✅ {kw['keyword']}"):
                    st.write(kw["detail"])
        else:
            st.caption("已确认的亮点将在这里显示")
        pending = st.session_state.get("pending_topic")
        if pending:
            st.divider()
            st.caption("正在挖掘...")
            st.info(f"⏳ {pending}")

st.title("JobFit")
st.caption("把你的经历精准匹配到每个职位")

# 语言设置
lang_output_map = {
    "中文": "用中文回答，包括翻译经验库内容。",
    "English": "Reply in English, including translating any Chinese content from the experience database.",
    "日本語": "日本語で回答し、経験データベースの中国語コンテンツも日本語に翻訳してください。"
}

col_ui_lang, col_out_lang = st.columns([1, 2])

with col_ui_lang:
    ui_lang = st.radio("界面语言 / UI Language", ["中文", "English", "日本語"], horizontal=True)

with col_out_lang:
    custom_output = st.checkbox("自定义输出语言 / Custom output language")
    if custom_output:
        custom_lang = st.text_input("输出语言 / Output language", placeholder="e.g. French, Spanish, 한국어...")
        if custom_lang:
            lang_instruction = f"Please reply in {custom_lang}, translating all content regardless of input language."
        else:
            lang_instruction = lang_output_map[ui_lang]
    else:
        lang_instruction = lang_output_map[ui_lang]

tab1, tab2, tab3, tab4 = st.tabs(["经验库", "简历优化", "面试准备", "了解我"])

with tab1:
    st.header("我的经验库")
    category = st.selectbox("选择分类", ["基础信息", "技能", "经历片段", "性格与软实力"])
    st.subheader(f"现有内容 - {category}")
    if data[category]:
        for i, item in enumerate(data[category]):
            col1, col2 = st.columns([5, 1])
            col1.write(f"**{item['title']}**：{item['content']}")
            if col2.button("删除", key=f"del_{i}"):
                data[category].pop(i)
                save_data(data)
                st.rerun()
    else:
        st.write("暂无内容，请添加")
    st.divider()
    st.subheader("添加新条目")
    new_title = st.text_input("标题（关键词）", placeholder="例：产品经理经验")
    new_content = st.text_area("详细描述", placeholder="例：2年B端产品经理经验，负责...")
    if st.button("添加"):
        if new_title and new_content:
            data[category].append({"title": new_title, "content": new_content})
            save_data(data)
            st.success("添加成功！")
            st.rerun()
        else:
            st.warning("请填写标题和描述")

with tab2:
    st.header("简历优化")

    if "jd_input" not in st.session_state:
        st.session_state.jd_input = "AI Strategy / AI Product Manager - 负责AI产品策略设计，推动AI在业务中的落地应用，具备结构化思维和数据分析能力，有LLM/Agent相关经验优先。"
    if "resume_input" not in st.session_state:
        st.session_state.resume_input = ""
    if "optimized_resume" not in st.session_state:
        st.session_state.optimized_resume = None
    if "generated_resume" not in st.session_state:
        st.session_state.generated_resume = None

    jd_input = st.text_area("粘贴职位描述（JD）", height=150,
                             placeholder="把招聘要求粘贴到这里...",
                             value=st.session_state.jd_input)
    if st.button("确认JD"):
        if jd_input:
            st.session_state.jd_input = jd_input
            st.success("JD已保存")
        else:
            st.warning("请先粘贴JD")

    st.divider()
    st.subheader("你的简历")
    resume_source = st.radio("简历来源", ["从经验库自动生成", "我要手动输入简历"], horizontal=True)

    if resume_source == "我要手动输入简历":
        resume_input = st.text_area("粘贴你的简历", height=200,
                                     placeholder="粘贴你现有的简历内容...",
                                     value=st.session_state.resume_input)
        if resume_input != st.session_state.resume_input:
            st.session_state.resume_input = resume_input

    # 从经验库生成简历
    if resume_source == "从经验库自动生成":
        if st.button("预览自动生成的简历"):
            all_experience = json.dumps(data, ensure_ascii=False, indent=2)
            with st.spinner("生成简历中..."):
                response = client.messages.create(
                    model="claude-haiku-4-5-20251001",
                    max_tokens=2048,
                    system=f"""你是一个专业的简历撰写顾问。根据用户的经验库，生成一份格式标准的简历。

规则：
- 只输出有实际内容的部分，没有信息的字段直接跳过，不要写"（如有）"或空白占位符
- 不加任何分析、建议或说明文字
- 格式清晰
- {lang_instruction}

按以下顺序输出（有内容才写）：
【基础信息】【教育背景】【工作经历】【项目经历】【技能】【性格与软实力】""",
                    messages=[{"role": "user", "content": f"经验库：\n{all_experience}"}]
                )
            st.session_state.generated_resume = response.content[0].text
            st.rerun()

        if st.session_state.generated_resume:
            with st.expander("查看自动生成的简历", expanded=True):
                st.text(st.session_state.generated_resume)
            st.download_button(
                label="下载简历（txt）",
                data=st.session_state.generated_resume,
                file_name="resume.txt",
                mime="text/plain"
            )

    if st.button("生成优化建议", type="primary"):
        if not jd_input:
            st.warning("请先粘贴JD")
        else:
            all_experience = json.dumps(data, ensure_ascii=False, indent=2)
            if resume_source == "从经验库自动生成":
                resume_text = st.session_state.generated_resume or f"经验库内容：\n{all_experience}"
            else:
                resume_text = st.session_state.resume_input or f"经验库内容：\n{all_experience}"

            with st.spinner("AI分析中..."):
                response = client.messages.create(
                    model="claude-haiku-4-5-20251001",
                    max_tokens=2048,
                    system=f"""你是一个专业的简历优化顾问。只做简历优化，不涉及面试准备。

根据候选人的简历和JD，输出两个部分：

## 优化分析
分析JD核心要求，指出简历中哪些地方需要调整，哪些亮点应该强调。

## 优化后的简历
直接输出一份完整的、针对该JD优化后的简历文本，可以直接复制使用。

{lang_instruction}格式清晰。""",
                    messages=[{"role": "user", "content": f"我的简历：\n{resume_text}\n\n职位描述：\n{jd_input}"}]
                )
            st.session_state.optimized_resume = response.content[0].text
            st.rerun()

    if st.session_state.optimized_resume:
        # 分析和简历分开显示
        full_text = st.session_state.optimized_resume
        if "## 优化后的简历" in full_text:
            parts = full_text.split("## 优化后的简历", 1)
            analysis_part = parts[0]
            resume_part = "## 优化后的简历" + parts[1]
        else:
            analysis_part = full_text
            resume_part = None

        st.subheader("优化分析")
        st.write(analysis_part)

        if resume_part:
            st.divider()
            st.subheader("优化后的简历")
            st.text(resume_part.replace("## 优化后的简历\n", ""))
            st.download_button(
                label="下载优化后的简历（txt）",
                data=resume_part.replace("## 优化后的简历\n", ""),
                file_name="optimized_resume.txt",
                mime="text/plain"
            )

        st.info("简历已准备好，前往「面试准备」Tab可直接使用此简历。")

with tab3:
    st.header("面试准备")

    jd_for_interview = st.session_state.get("jd_input", "")
    optimized_resume = st.session_state.get("optimized_resume", None)

    if "interview_questions" not in st.session_state:
        st.session_state.interview_questions = None
    if "show_answers" not in st.session_state:
        st.session_state.show_answers = False
    if "practice_feedback" not in st.session_state:
        st.session_state.practice_feedback = None

    # 简历确认
    st.subheader("使用的简历")
    if optimized_resume:
        st.success("将使用「简历优化」中生成的优化简历")
        # 只显示简历部分，不含分析
        if "## 优化后的简历" in optimized_resume:
            resume_only = optimized_resume.split("## 优化后的简历", 1)[1].strip()
        else:
            resume_only = optimized_resume
        with st.expander("查看简历"):
            st.text(resume_only)
        if st.checkbox("我要换一份简历"):
            interview_resume = st.text_area("粘贴简历", height=150, key="interview_resume_override")
        else:
            interview_resume = resume_only
    else:
        st.info("未检测到优化简历，将使用经验库。你也可以手动输入。")
        manual_resume = st.text_area("手动输入简历（可选）", height=150,
                                      placeholder="留空则使用经验库...", key="manual_interview_resume")
        interview_resume = manual_resume if manual_resume else json.dumps(data, ensure_ascii=False)

    # JD确认
    st.subheader("职位描述")
    if jd_for_interview:
        st.success("已从「简历优化」读取JD")
        with st.expander("查看JD"):
            st.write(jd_for_interview)
        if st.checkbox("我要换一个JD"):
            interview_jd = st.text_area("粘贴新JD", height=150, key="interview_jd_override")
        else:
            interview_jd = jd_for_interview
    else:
        interview_jd = st.text_area("粘贴职位描述（JD）", height=150,
                                     placeholder="把招聘要求粘贴到这里...", key="interview_jd_input")

    st.divider()

    # 预测面试问题
    st.subheader("预测面试问题")
    show_answers = st.toggle("立刻显示推荐答案")

    if st.button("生成面试问题", type="primary"):
        if not interview_jd:
            st.warning("请先输入JD")
        else:
            with st.spinner("AI预测面试问题中..."):
                response = client.messages.create(
                    model="claude-haiku-4-5-20251001",
                    max_tokens=2048,
                    system=f"""你是一个资深面试官。根据JD和候选人简历，预测8个面试问题。

不要输出任何标题或开场白，直接按以下格式输出8道题，每道题之间用===分隔：

问题：[问题内容]
考察点：[这道题在考察什么]
推荐回答：[基于候选人具体经历的详细回答建议，至少3句话]

===

问题：[问题内容]
考察点：...
推荐回答：...

包含：行为类（2题）、能力类（2题）、情景类（2题）、动机类（1题）、压力测试类（1题）。{lang_instruction}""",
                    messages=[{"role": "user", "content": f"候选人简历：\n{interview_resume}\n\n职位描述：\n{interview_jd}"}]
                )
            st.session_state.interview_questions = response.content[0].text
            st.rerun()

    if st.session_state.interview_questions:
        questions_text = st.session_state.interview_questions
        blocks = [q.strip() for q in questions_text.split("===") if q.strip()]

        for i, q_block in enumerate(blocks):
            # 提取各字段（支持多行内容）
            question_val = ""
            kaochadian_val = ""
            answer_val = ""

            current_field = None
            current_lines = []

            for line in q_block.split('\n'):
                if line.startswith("问题："):
                    current_field = "question"
                    current_lines = [line.replace("问题：", "").strip()]
                elif line.startswith("考察点："):
                    if current_field == "question":
                        question_val = " ".join(current_lines)
                    current_field = "kaochadian"
                    current_lines = [line.replace("考察点：", "").strip()]
                elif line.startswith("推荐回答："):
                    if current_field == "kaochadian":
                        kaochadian_val = " ".join(current_lines)
                    current_field = "answer"
                    current_lines = [line.replace("推荐回答：", "").strip()]
                elif line.strip() and current_field:
                    current_lines.append(line.strip())

            if current_field == "answer":
                answer_val = " ".join(current_lines)
            elif current_field == "kaochadian":
                kaochadian_val = " ".join(current_lines)

            if not question_val:
                continue

            with st.expander(f"Q{i+1}：{question_val}", expanded=False):
                st.markdown(f"**考察点：** {kaochadian_val}")
                if show_answers:
                    st.divider()
                    st.markdown(f"**推荐回答思路：**\n\n{answer_val}")
                else:
                    st.caption("开启「立刻显示推荐答案」查看回答思路")

        st.divider()

        # 答题练习
        st.subheader("答题练习")
        practice_question = st.text_input("输入你想练习的问题", placeholder="复制上面的问题粘贴到这里...")
        practice_answer = st.text_area("输入你的回答思路", height=150,
                                        placeholder="写下你会怎么回答这个问题...")

        if st.button("AI点评"):
            if not practice_question or not practice_answer:
                st.warning("请输入问题和你的回答思路")
            else:
                with st.spinner("AI点评中..."):
                    feedback_response = client.messages.create(
                        model="claude-haiku-4-5-20251001",
                        max_tokens=1024,
                        system=f"""你是一个资深面试教练。评估候选人的回答思路，给出：
1. 亮点
2. 不足
3. 优化建议
4. 优化后的示范回答（基于候选人的真实经历）

语气友好鼓励。{lang_instruction}""",
                        messages=[{"role": "user", "content": f"面试问题：{practice_question}\n\n候选人回答：{practice_answer}\n\n候选人背景：{interview_resume}"}]
                    )
                st.session_state.practice_feedback = feedback_response.content[0].text
                st.rerun()

        if st.session_state.practice_feedback:
            st.subheader("AI点评")
            st.write(st.session_state.practice_feedback)

with tab4:
    st.header("了解我")
    st.write("通过轻松的对话，让AI深入了解你的经历和优势，帮你发现简历中被忽视的亮点。")

    with st.expander("💡 使用提示"):
        st.markdown("""
        - **像聊天一样自然分享**，不需要整理格式
        - AI会主动提问，引导你说出有价值的经历
        - 左侧边栏会实时显示AI发现的亮点，鼠标悬停可查看详情
        - ✅ 表示已确认的亮点，⏳ 表示正在深入挖掘的话题
        - 分享3个经历后可以生成总结，一键加入经验库
        """)

    if "onboarding_messages" not in st.session_state:
        st.session_state.onboarding_messages = []
    if "onboarding_keywords" not in st.session_state:
        st.session_state.onboarding_keywords = []
    if "onboarding_started" not in st.session_state:
        st.session_state.onboarding_started = False
    if "onboarding_summary" not in st.session_state:
        st.session_state.onboarding_summary = None
    if "pending_topic" not in st.session_state:
        st.session_state.pending_topic = None

    if not st.session_state.onboarding_started:
        st.write("")
        saved = load_conversation()
        if saved:
            st.info(f"你有一次未完成的对话，共 {len(saved['messages'])} 条记录，已发现 {len(saved['keywords'])} 个亮点。")
            col_a, col_b = st.columns(2)
            if col_a.button("继续上次对话", type="primary"):
                st.session_state.onboarding_messages = saved["messages"]
                st.session_state.onboarding_keywords = saved["keywords"]
                st.session_state.onboarding_started = True
                st.rerun()
            if col_b.button("开始新对话"):
                clear_conversation()
                st.session_state.onboarding_started = True
                with st.spinner("启动中..."):
                    response = client.messages.create(
                        model="claude-haiku-4-5-20251001",
                        max_tokens=512,
                        system=ONBOARDING_SYSTEM,
                        messages=[{"role": "user", "content": "你好"}]
                    )
                reply = response.content[0].text
                st.session_state.onboarding_messages = [
                    {"role": "user", "content": "你好"},
                    {"role": "assistant", "content": reply}
                ]
                st.session_state.onboarding_keywords = []
                st.rerun()
        else:
            if st.button("开始对话", type="primary"):
                st.session_state.onboarding_started = True
                with st.spinner("启动中..."):
                    response = client.messages.create(
                        model="claude-haiku-4-5-20251001",
                        max_tokens=512,
                        system=ONBOARDING_SYSTEM,
                        messages=[{"role": "user", "content": "你好"}]
                    )
                reply = response.content[0].text
                st.session_state.onboarding_messages = [
                    {"role": "user", "content": "你好"},
                    {"role": "assistant", "content": reply}
                ]
                st.rerun()
    else:
        for msg in st.session_state.onboarding_messages:
            if msg["role"] == "user":
                st.chat_message("user").write(msg["content"])
            else:
                st.chat_message("assistant").write(msg["content"])

        user_input = st.chat_input("分享你的经历...")

        if user_input:
            st.session_state.onboarding_messages.append({"role": "user", "content": user_input})
            with st.spinner("思考中..."):
                response = client.messages.create(
                    model="claude-haiku-4-5-20251001",
                    max_tokens=1024,
                    system=ONBOARDING_SYSTEM,
                    messages=st.session_state.onboarding_messages
                )
            reply = response.content[0].text
            st.session_state.onboarding_messages.append({"role": "assistant", "content": reply})

            new_kws = extract_confirmed_keywords(client, st.session_state.onboarding_messages)
            for kw in new_kws:
                if kw["keyword"] not in [k["keyword"] for k in st.session_state.onboarding_keywords]:
                    st.session_state.onboarding_keywords.append(kw)

            st.session_state.pending_topic = extract_pending_topic(client, st.session_state.onboarding_messages)
            save_conversation(st.session_state.onboarding_messages, st.session_state.onboarding_keywords)
            st.rerun()

        if st.button("结束并生成总结"):
            with st.spinner("生成总结中..."):
                summary_response = client.messages.create(
                    model="claude-haiku-4-5-20251001",
                    max_tokens=1024,
                    system=f"你是一个简历顾问，根据对话内容生成结构化的用户信息总结，分为：基础信息、技能、经历片段、性格与软实力四个类别。简洁清晰。{lang_instruction}",
                    messages=st.session_state.onboarding_messages + [
                        {"role": "user", "content": "请根据我们的对话，生成我的信息总结"}
                    ]
                )
            st.session_state.onboarding_summary = summary_response.content[0].text
            st.session_state.pending_topic = None
            st.rerun()

        if st.session_state.onboarding_summary:
            st.divider()
            st.subheader("对话总结")
            st.write(st.session_state.onboarding_summary)
            if st.button("将总结加入经验库"):
                data["经历片段"].append({
                    "title": "AI对话发现的亮点",
                    "content": st.session_state.onboarding_summary
                })
                save_data(data)
                st.success("已加入经验库！")
                st.session_state.onboarding_summary = None
                clear_conversation()
                st.rerun()
