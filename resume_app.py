import streamlit as st
import json
import os
import anthropic

DATA_FILE = "experience.json"
CONVERSATION_FILE = "conversation.json"

# ==================== 翻译字典 ====================
TRANSLATIONS = {
    "app_caption": {
        "中文": "把你的经历精准匹配到每个职位",
        "English": "Match your experience to every job opportunity",
        "日本語": "あなたの経験を各職位に的確にマッチング"
    },
    "ui_lang_label": {
        "中文": "界面语言",
        "English": "UI Language",
        "日本語": "UI言語"
    },
    "custom_output_label": {
        "中文": "自定义输出语言",
        "English": "Custom output language",
        "日本語": "出力言語をカスタマイズ"
    },
    "output_lang_label": {
        "中文": "输出语言",
        "English": "Output language",
        "日本語": "出力言語"
    },
    "output_lang_placeholder": {
        "中文": "例如：French, Spanish, 한국어...",
        "English": "e.g. French, Spanish, 한국어...",
        "日本語": "例：French, Spanish, 한국어..."
    },
    # Tab names
    "tab_experience": {"中文": "经验库", "English": "Experience", "日本語": "経験庫"},
    "tab_resume": {"中文": "简历优化", "English": "Resume", "日本語": "履歴書最適化"},
    "tab_interview": {"中文": "面试准备", "English": "Interview Prep", "日本語": "面接準備"},
    "tab_aboutme": {"中文": "了解我", "English": "About Me", "日本語": "私について"},
    # Categories
    "cat_basic": {"中文": "基础信息", "English": "Basic Info", "日本語": "基本情報"},
    "cat_skills": {"中文": "技能", "English": "Skills", "日本語": "スキル"},
    "cat_episodes": {"中文": "经历片段", "English": "Experiences", "日本語": "経験エピソード"},
    "cat_personality": {"中文": "性格与软实力", "English": "Personality & Soft Skills", "日本語": "性格とソフトスキル"},
    # Tab 1
    "my_experience": {"中文": "我的经验库", "English": "My Experience Library", "日本語": "私の経験庫"},
    "select_category": {"中文": "选择分类", "English": "Select category", "日本語": "カテゴリを選択"},
    "existing_content": {"中文": "现有内容", "English": "Existing Content", "日本語": "既存コンテンツ"},
    "delete": {"中文": "删除", "English": "Delete", "日本語": "削除"},
    "no_content": {"中文": "暂无内容，请添加", "English": "No content yet. Please add.", "日本語": "コンテンツがありません。追加してください。"},
    "add_new": {"中文": "添加新条目", "English": "Add New Entry", "日本語": "新規追加"},
    "title_label": {"中文": "标题（关键词）", "English": "Title (keyword)", "日本語": "タイトル（キーワード）"},
    "title_placeholder": {"中文": "例：产品经理经验", "English": "e.g. Product Manager experience", "日本語": "例：プロダクトマネージャー経験"},
    "content_label": {"中文": "详细描述", "English": "Detailed description", "日本語": "詳細説明"},
    "content_placeholder": {"中文": "例：2年B端产品经理经验，负责...", "English": "e.g. 2 years B2B PM experience, responsible for...", "日本語": "例：2年間のBtoB PM経験、担当..."},
    "add": {"中文": "添加", "English": "Add", "日本語": "追加"},
    "added_success": {"中文": "添加成功！", "English": "Added successfully!", "日本語": "追加成功！"},
    "fill_both": {"中文": "请填写标题和描述", "English": "Please fill in both title and description", "日本語": "タイトルと説明を両方入力してください"},
    # Tab 2
    "resume_optimize": {"中文": "简历优化", "English": "Resume Optimization", "日本語": "履歴書最適化"},
    "paste_jd": {"中文": "粘贴职位描述（JD）", "English": "Paste Job Description (JD)", "日本語": "職務記述書（JD）を貼り付け"},
    "jd_placeholder": {"中文": "把招聘要求粘贴到这里...", "English": "Paste the job requirements here...", "日本語": "求人要件をここに貼り付け..."},
    "confirm_jd": {"中文": "确认JD", "English": "Confirm JD", "日本語": "JDを確認"},
    "jd_saved": {"中文": "JD已保存", "English": "JD saved", "日本語": "JD保存済み"},
    "please_paste_jd": {"中文": "请先粘贴JD", "English": "Please paste JD first", "日本語": "先にJDを貼り付けてください"},
    "your_resume": {"中文": "你的简历", "English": "Your Resume", "日本語": "あなたの履歴書"},
    "resume_source": {"中文": "简历来源", "English": "Resume Source", "日本語": "履歴書の出所"},
    "auto_generate": {"中文": "从经验库自动生成", "English": "Auto-generate from experience", "日本語": "経験庫から自動生成"},
    "manual_input": {"中文": "我要手动输入简历", "English": "I'll input manually", "日本語": "手動で入力する"},
    "paste_resume": {"中文": "粘贴你的简历", "English": "Paste your resume", "日本語": "履歴書を貼り付け"},
    "resume_placeholder": {"中文": "粘贴你现有的简历内容...", "English": "Paste your existing resume content...", "日本語": "既存の履歴書内容を貼り付け..."},
    "preview_resume": {"中文": "预览自动生成的简历", "English": "Preview auto-generated resume", "日本語": "自動生成された履歴書をプレビュー"},
    "generating_resume": {"中文": "生成简历中...", "English": "Generating resume...", "日本語": "履歴書を生成中..."},
    "view_resume": {"中文": "查看自动生成的简历", "English": "View auto-generated resume", "日本語": "自動生成された履歴書を表示"},
    "download_resume": {"中文": "下载简历（txt）", "English": "Download resume (txt)", "日本語": "履歴書をダウンロード (txt)"},
    "generate_optimization": {"中文": "生成优化建议", "English": "Generate Optimization", "日本語": "最適化提案を生成"},
    "ai_analyzing": {"中文": "AI分析中...", "English": "AI analyzing...", "日本語": "AI分析中..."},
    "optimization_analysis": {"中文": "优化分析", "English": "Optimization Analysis", "日本語": "最適化分析"},
    "optimized_resume_header": {"中文": "优化后的简历", "English": "Optimized Resume", "日本語": "最適化された履歴書"},
    "download_optimized": {"中文": "下载优化后的简历（txt）", "English": "Download optimized resume (txt)", "日本語": "最適化された履歴書をダウンロード (txt)"},
    "resume_ready": {"中文": "简历已准备好，前往「面试准备」Tab可直接使用此简历。", "English": "Resume ready. Go to 'Interview Prep' tab to use it.", "日本語": "履歴書が準備できました。「面接準備」タブでそのまま使用できます。"},
    # Tab 3
    "interview_prep": {"中文": "面试准备", "English": "Interview Preparation", "日本語": "面接準備"},
    "resume_used": {"中文": "使用的简历", "English": "Resume in Use", "日本語": "使用中の履歴書"},
    "using_optimized": {"中文": "将使用「简历优化」中生成的优化简历", "English": "Using the optimized resume from 'Resume Optimization'", "日本語": "「履歴書最適化」で生成された履歴書を使用します"},
    "view_resume_expander": {"中文": "查看简历", "English": "View resume", "日本語": "履歴書を表示"},
    "change_resume": {"中文": "我要换一份简历", "English": "I want to use a different resume", "日本語": "別の履歴書を使いたい"},
    "paste_resume_short": {"中文": "粘贴简历", "English": "Paste resume", "日本語": "履歴書を貼り付け"},
    "no_optimized": {"中文": "未检测到优化简历，将使用经验库。你也可以手动输入。", "English": "No optimized resume found. Will use experience library, or input manually.", "日本語": "最適化された履歴書が見つかりません。経験庫を使用するか、手動で入力してください。"},
    "manual_resume_optional": {"中文": "手动输入简历（可选）", "English": "Manual resume input (optional)", "日本語": "履歴書を手動入力（任意）"},
    "empty_uses_db": {"中文": "留空则使用经验库...", "English": "Leave empty to use experience library...", "日本語": "空欄の場合は経験庫を使用..."},
    "job_description": {"中文": "职位描述", "English": "Job Description", "日本語": "職務記述書"},
    "jd_loaded": {"中文": "已从「简历优化」读取JD", "English": "JD loaded from 'Resume Optimization'", "日本語": "「履歴書最適化」からJDを読み込みました"},
    "view_jd": {"中文": "查看JD", "English": "View JD", "日本語": "JDを表示"},
    "change_jd": {"中文": "我要换一个JD", "English": "I want to use a different JD", "日本語": "別のJDを使いたい"},
    "paste_new_jd": {"中文": "粘贴新JD", "English": "Paste new JD", "日本語": "新しいJDを貼り付け"},
    "predict_questions": {"中文": "预测面试问题", "English": "Predict Interview Questions", "日本語": "面接質問を予測"},
    "show_answers_toggle": {"中文": "立刻显示推荐答案", "English": "Show recommended answers immediately", "日本語": "推奨回答を即時表示"},
    "generate_questions": {"中文": "生成面试问题", "English": "Generate questions", "日本語": "質問を生成"},
    "please_input_jd": {"中文": "请先输入JD", "English": "Please input JD first", "日本語": "先にJDを入力してください"},
    "predicting_questions": {"中文": "AI预测面试问题中...", "English": "AI predicting questions...", "日本語": "AIが質問を予測中..."},
    "assessment_point": {"中文": "考察点", "English": "Assessment Point", "日本語": "評価ポイント"},
    "recommended_answer": {"中文": "推荐回答思路", "English": "Recommended Answer Approach", "日本語": "推奨回答アプローチ"},
    "enable_to_see": {"中文": "开启「立刻显示推荐答案」查看回答思路", "English": "Enable 'Show recommended answers' to see", "日本語": "「推奨回答を即時表示」を有効にして確認"},
    "practice_answering": {"中文": "答题练习", "English": "Practice Answering", "日本語": "回答練習"},
    "practice_q_label": {"中文": "输入你想练习的问题", "English": "Enter the question to practice", "日本語": "練習したい質問を入力"},
    "practice_q_placeholder": {"中文": "复制上面的问题粘贴到这里...", "English": "Copy a question from above...", "日本語": "上記の質問をコピーして貼り付け..."},
    "practice_a_label": {"中文": "输入你的回答思路", "English": "Enter your answer approach", "日本語": "回答アプローチを入力"},
    "practice_a_placeholder": {"中文": "写下你会怎么回答这个问题...", "English": "Write how you would answer...", "日本語": "どのように答えるか書いてください..."},
    "ai_feedback": {"中文": "AI点评", "English": "AI Feedback", "日本語": "AIフィードバック"},
    "please_input_both": {"中文": "请输入问题和你的回答思路", "English": "Please input both question and answer", "日本語": "質問と回答を両方入力してください"},
    "ai_reviewing": {"中文": "AI点评中...", "English": "AI reviewing...", "日本語": "AIが評価中..."},
    # Tab 4
    "about_me_header": {"中文": "了解我", "English": "About Me", "日本語": "私について"},
    "about_me_desc": {"中文": "通过轻松的对话，让AI深入了解你的经历和优势，帮你发现简历中被忽视的亮点。", "English": "Through casual conversation, let AI understand your experience and strengths, helping you discover overlooked highlights.", "日本語": "カジュアルな会話を通じて、AIがあなたの経験と強みを理解し、見落とされたハイライトを発見します。"},
    "usage_tips": {"中文": "💡 使用提示", "English": "💡 Usage Tips", "日本語": "💡 使い方のヒント"},
    "usage_tips_content": {
        "中文": """
- **像聊天一样自然分享**，不需要整理格式
- AI会主动提问，引导你说出有价值的经历
- 左侧边栏会实时显示AI发现的亮点，鼠标悬停可查看详情
- ✅ 表示已确认的亮点，⏳ 表示正在深入挖掘的话题
- 分享3个经历后可以生成总结，一键加入经验库
        """,
        "English": """
- **Share naturally like chatting**, no formatting needed
- AI will ask questions to draw out valuable experiences
- Left sidebar shows highlights in real-time, hover for details
- ✅ means confirmed highlight, ⏳ means currently exploring
- After 3 experiences, generate summary and add to library
        """,
        "日本語": """
- **チャットのように自然に共有**、フォーマット不要
- AIが質問して価値ある経験を引き出します
- 左サイドバーにハイライトがリアルタイムで表示、ホバーで詳細
- ✅ は確認済みハイライト、⏳ は探索中のトピック
- 3つの経験を共有後、要約を生成して経験庫に追加できます
        """
    },
    "saved_conversation_info": {
        "中文": "你有一次未完成的对话",
        "English": "You have an unfinished conversation",
        "日本語": "未完了の会話があります"
    },
    "messages_count": {"中文": "条记录", "English": "messages", "日本語": "件のメッセージ"},
    "highlights_count": {"中文": "个亮点", "English": "highlights found", "日本語": "個のハイライト"},
    "continue_conversation": {"中文": "继续上次对话", "English": "Continue previous chat", "日本語": "前回の会話を続ける"},
    "start_new_conversation": {"中文": "开始新对话", "English": "Start new conversation", "日本語": "新しい会話を開始"},
    "start_conversation": {"中文": "开始对话", "English": "Start conversation", "日本語": "会話を開始"},
    "starting": {"中文": "启动中...", "English": "Starting...", "日本語": "起動中..."},
    "share_experience": {"中文": "分享你的经历...", "English": "Share your experience...", "日本語": "経験を共有..."},
    "thinking": {"中文": "思考中...", "English": "Thinking...", "日本語": "考え中..."},
    "end_and_summarize": {"中文": "结束并生成总结", "English": "End & Summarize", "日本語": "終了して要約"},
    "generating_summary": {"中文": "生成总结中...", "English": "Generating summary...", "日本語": "要約を生成中..."},
    "conversation_summary": {"中文": "对话总结", "English": "Conversation Summary", "日本語": "会話の要約"},
    "add_to_library": {"中文": "将总结加入经验库", "English": "Add summary to library", "日本語": "要約を経験庫に追加"},
    "added_to_library": {"中文": "已加入经验库！", "English": "Added to library!", "日本語": "経験庫に追加しました！"},
    "ai_dialogue_highlight": {"中文": "AI对话发现的亮点", "English": "AI Dialogue Highlights", "日本語": "AI対話のハイライト"},
    # Sidebar
    "found_highlights": {"中文": "已发现的亮点", "English": "Discovered Highlights", "日本語": "発見されたハイライト"},
    "highlights_placeholder": {"中文": "已确认的亮点将在这里显示", "English": "Confirmed highlights will appear here", "日本語": "確認されたハイライトがここに表示されます"},
    "exploring": {"中文": "正在挖掘...", "English": "Exploring...", "日本語": "探索中..."},
}

# 分类显示名称映射
CATEGORY_KEYS = ["基础信息", "技能", "经历片段", "性格与软实力"]
CATEGORY_I18N_KEYS = {"基础信息": "cat_basic", "技能": "cat_skills", "经历片段": "cat_episodes", "性格与软实力": "cat_personality"}

# ==================== 辅助函数 ====================
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

# ==================== 页面 ====================
st.title("JobFit")

# 默认界面语言（必须在t()使用前设置）
if "ui_lang" not in st.session_state:
    st.session_state.ui_lang = "中文"
ui_lang = st.session_state.ui_lang

def t(key):
    return TRANSLATIONS.get(key, {}).get(ui_lang, key)

def cat_display(cat_key):
    return t(CATEGORY_I18N_KEYS[cat_key])

st.caption(t("app_caption"))

# 侧边栏：只在了解我Tab激活时显示关键词
if "onboarding_started" in st.session_state and st.session_state.onboarding_started:
    with st.sidebar:
        st.subheader(t("found_highlights"))
        if st.session_state.get("onboarding_keywords"):
            for kw in st.session_state.onboarding_keywords:
                with st.popover(f"✅ {kw['keyword']}"):
                    st.write(kw["detail"])
        else:
            st.caption(t("highlights_placeholder"))
        pending = st.session_state.get("pending_topic")
        if pending:
            st.divider()
            st.caption(t("exploring"))
            st.info(f"⏳ {pending}")

# 语言设置
lang_output_map = {
    "中文": "用中文回答，包括翻译经验库内容。",
    "English": "Reply in English, including translating any Chinese content from the experience database.",
    "日本語": "日本語で回答し、経験データベースの中国語コンテンツも日本語に翻訳してください。"
}

col_ui_lang, col_out_lang = st.columns([1, 2])

with col_ui_lang:
    new_ui_lang = st.radio(t("ui_lang_label"), ["中文", "English", "日本語"], horizontal=True, index=["中文", "English", "日本語"].index(ui_lang))
    if new_ui_lang != ui_lang:
        st.session_state.ui_lang = new_ui_lang
        st.rerun()

with col_out_lang:
    custom_output = st.checkbox(t("custom_output_label"))
    if custom_output:
        custom_lang = st.text_input(t("output_lang_label"), placeholder=t("output_lang_placeholder"))
        if custom_lang:
            lang_instruction = f"Please reply in {custom_lang}, translating all content regardless of input language."
        else:
            lang_instruction = lang_output_map[ui_lang]
    else:
        lang_instruction = lang_output_map[ui_lang]

tab1, tab2, tab3, tab4 = st.tabs([t("tab_experience"), t("tab_resume"), t("tab_interview"), t("tab_aboutme")])

# ==================== Tab 1: 经验库 ====================
with tab1:
    st.header(t("my_experience"))
    category = st.selectbox(t("select_category"), CATEGORY_KEYS, format_func=cat_display)
    st.subheader(f"{t('existing_content')} - {cat_display(category)}")
    if data[category]:
        for i, item in enumerate(data[category]):
            col1, col2 = st.columns([5, 1])
            col1.write(f"**{item['title']}**：{item['content']}")
            if col2.button(t("delete"), key=f"del_{i}"):
                data[category].pop(i)
                save_data(data)
                st.rerun()
    else:
        st.write(t("no_content"))
    st.divider()
    st.subheader(t("add_new"))
    new_title = st.text_input(t("title_label"), placeholder=t("title_placeholder"))
    new_content = st.text_area(t("content_label"), placeholder=t("content_placeholder"))
    if st.button(t("add")):
        if new_title and new_content:
            data[category].append({"title": new_title, "content": new_content})
            save_data(data)
            st.success(t("added_success"))
            st.rerun()
        else:
            st.warning(t("fill_both"))

# ==================== Tab 2: 简历优化 ====================
with tab2:
    st.header(t("resume_optimize"))

    if "jd_input" not in st.session_state:
        st.session_state.jd_input = ""
    if "resume_input" not in st.session_state:
        st.session_state.resume_input = ""
    if "optimized_resume" not in st.session_state:
        st.session_state.optimized_resume = None
    if "generated_resume" not in st.session_state:
        st.session_state.generated_resume = None

    jd_input = st.text_area(t("paste_jd"), height=150,
                             placeholder=t("jd_placeholder"),
                             value=st.session_state.jd_input)
    if st.button(t("confirm_jd")):
        if jd_input:
            st.session_state.jd_input = jd_input
            st.success(t("jd_saved"))
        else:
            st.warning(t("please_paste_jd"))

    st.divider()
    st.subheader(t("your_resume"))
    resume_source = st.radio(t("resume_source"), [t("auto_generate"), t("manual_input")], horizontal=True)

    if resume_source == t("manual_input"):
        resume_input = st.text_area(t("paste_resume"), height=200,
                                     placeholder=t("resume_placeholder"),
                                     value=st.session_state.resume_input)
        if resume_input != st.session_state.resume_input:
            st.session_state.resume_input = resume_input

    if resume_source == t("auto_generate"):
        if st.button(t("preview_resume")):
            all_experience = json.dumps(data, ensure_ascii=False, indent=2)
            with st.spinner(t("generating_resume")):
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
            with st.expander(t("view_resume"), expanded=True):
                st.text(st.session_state.generated_resume)
            st.download_button(
                label=t("download_resume"),
                data=st.session_state.generated_resume,
                file_name="resume.txt",
                mime="text/plain"
            )

    if st.button(t("generate_optimization"), type="primary"):
        if not jd_input:
            st.warning(t("please_paste_jd"))
        else:
            all_experience = json.dumps(data, ensure_ascii=False, indent=2)
            if resume_source == t("auto_generate"):
                resume_text = st.session_state.generated_resume or f"经验库内容：\n{all_experience}"
            else:
                resume_text = st.session_state.resume_input or f"经验库内容：\n{all_experience}"

            with st.spinner(t("ai_analyzing")):
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
        full_text = st.session_state.optimized_resume
        if "## 优化后的简历" in full_text:
            parts = full_text.split("## 优化后的简历", 1)
            analysis_part = parts[0]
            resume_part = parts[1]
        else:
            analysis_part = full_text
            resume_part = None

        st.subheader(t("optimization_analysis"))
        st.write(analysis_part)

        if resume_part:
            st.divider()
            st.subheader(t("optimized_resume_header"))
            st.text(resume_part.strip())
            st.download_button(
                label=t("download_optimized"),
                data=resume_part.strip(),
                file_name="optimized_resume.txt",
                mime="text/plain"
            )

        st.info(t("resume_ready"))

# ==================== Tab 3: 面试准备 ====================
with tab3:
    st.header(t("interview_prep"))

    jd_for_interview = st.session_state.get("jd_input", "")
    optimized_resume = st.session_state.get("optimized_resume", None)

    if "interview_questions" not in st.session_state:
        st.session_state.interview_questions = None
    if "show_answers" not in st.session_state:
        st.session_state.show_answers = False
    if "practice_feedback" not in st.session_state:
        st.session_state.practice_feedback = None

    st.subheader(t("resume_used"))
    if optimized_resume:
        st.success(t("using_optimized"))
        if "## 优化后的简历" in optimized_resume:
            resume_only = optimized_resume.split("## 优化后的简历", 1)[1].strip()
        else:
            resume_only = optimized_resume
        with st.expander(t("view_resume_expander")):
            st.text(resume_only)
        if st.checkbox(t("change_resume")):
            interview_resume = st.text_area(t("paste_resume_short"), height=150, key="interview_resume_override")
        else:
            interview_resume = resume_only
    else:
        st.info(t("no_optimized"))
        manual_resume = st.text_area(t("manual_resume_optional"), height=150,
                                      placeholder=t("empty_uses_db"), key="manual_interview_resume")
        interview_resume = manual_resume if manual_resume else json.dumps(data, ensure_ascii=False)

    st.subheader(t("job_description"))
    if jd_for_interview:
        st.success(t("jd_loaded"))
        with st.expander(t("view_jd")):
            st.write(jd_for_interview)
        if st.checkbox(t("change_jd")):
            interview_jd = st.text_area(t("paste_new_jd"), height=150, key="interview_jd_override")
        else:
            interview_jd = jd_for_interview
    else:
        interview_jd = st.text_area(t("paste_jd"), height=150,
                                     placeholder=t("jd_placeholder"), key="interview_jd_input")

    st.divider()

    st.subheader(t("predict_questions"))
    show_answers = st.toggle(t("show_answers_toggle"))

    if st.button(t("generate_questions"), type="primary"):
        if not interview_jd:
            st.warning(t("please_input_jd"))
        else:
            with st.spinner(t("predicting_questions")):
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
            question_val = ""
            kaochadian_val = ""
            answer_val = ""

            current_field = None
            current_lines = []

            for line in q_block.split('\n'):
                line_stripped = line.strip()
                # 同时匹配中/英/日的字段前缀
                if line_stripped.startswith(("问题：", "Question:", "質問：")):
                    current_field = "question"
                    current_lines = [line_stripped.split("：", 1)[-1].split(":", 1)[-1].strip()]
                elif line_stripped.startswith(("考察点：", "Assessment Point:", "評価ポイント：")):
                    if current_field == "question":
                        question_val = " ".join(current_lines)
                    current_field = "kaochadian"
                    current_lines = [line_stripped.split("：", 1)[-1].split(":", 1)[-1].strip()]
                elif line_stripped.startswith(("推荐回答：", "Recommended Answer:", "推奨回答：")):
                    if current_field == "kaochadian":
                        kaochadian_val = " ".join(current_lines)
                    current_field = "answer"
                    current_lines = [line_stripped.split("：", 1)[-1].split(":", 1)[-1].strip()]
                elif line_stripped and current_field:
                    current_lines.append(line_stripped)

            if current_field == "answer":
                answer_val = " ".join(current_lines)
            elif current_field == "kaochadian":
                kaochadian_val = " ".join(current_lines)

            if not question_val:
                continue

            with st.expander(f"Q{i+1}：{question_val}", expanded=False):
                st.markdown(f"**{t('assessment_point')}：** {kaochadian_val}")
                if show_answers:
                    st.divider()
                    st.markdown(f"**{t('recommended_answer')}：**\n\n{answer_val}")
                else:
                    st.caption(t("enable_to_see"))

        st.divider()

        st.subheader(t("practice_answering"))
        practice_question = st.text_input(t("practice_q_label"), placeholder=t("practice_q_placeholder"))
        practice_answer = st.text_area(t("practice_a_label"), height=150, placeholder=t("practice_a_placeholder"))

        if st.button(t("ai_feedback")):
            if not practice_question or not practice_answer:
                st.warning(t("please_input_both"))
            else:
                with st.spinner(t("ai_reviewing")):
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
            st.subheader(t("ai_feedback"))
            st.write(st.session_state.practice_feedback)

# ==================== Tab 4: 了解我 ====================
with tab4:
    st.header(t("about_me_header"))
    st.write(t("about_me_desc"))

    with st.expander(t("usage_tips")):
        st.markdown(t("usage_tips_content"))

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
            st.info(f"{t('saved_conversation_info')} ({len(saved['messages'])} {t('messages_count')}, {len(saved['keywords'])} {t('highlights_count')})")
            col_a, col_b = st.columns(2)
            if col_a.button(t("continue_conversation"), type="primary"):
                st.session_state.onboarding_messages = saved["messages"]
                st.session_state.onboarding_keywords = saved["keywords"]
                st.session_state.onboarding_started = True
                st.rerun()
            if col_b.button(t("start_new_conversation")):
                clear_conversation()
                st.session_state.onboarding_started = True
                with st.spinner(t("starting")):
                    response = client.messages.create(
                        model="claude-haiku-4-5-20251001",
                        max_tokens=512,
                        system=ONBOARDING_SYSTEM + f"\n\n{lang_instruction}",
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
            if st.button(t("start_conversation"), type="primary"):
                st.session_state.onboarding_started = True
                with st.spinner(t("starting")):
                    response = client.messages.create(
                        model="claude-haiku-4-5-20251001",
                        max_tokens=512,
                        system=ONBOARDING_SYSTEM + f"\n\n{lang_instruction}",
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

        user_input = st.chat_input(t("share_experience"))

        if user_input:
            st.session_state.onboarding_messages.append({"role": "user", "content": user_input})
            with st.spinner(t("thinking")):
                response = client.messages.create(
                    model="claude-haiku-4-5-20251001",
                    max_tokens=1024,
                    system=ONBOARDING_SYSTEM + f"\n\n{lang_instruction}",
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

        if st.button(t("end_and_summarize")):
            with st.spinner(t("generating_summary")):
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
            st.subheader(t("conversation_summary"))
            st.write(st.session_state.onboarding_summary)
            if st.button(t("add_to_library")):
                data["经历片段"].append({
                    "title": t("ai_dialogue_highlight"),
                    "content": st.session_state.onboarding_summary
                })
                save_data(data)
                st.success(t("added_to_library"))
                st.session_state.onboarding_summary = None
                clear_conversation()
                st.rerun()
