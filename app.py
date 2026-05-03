import streamlit as st
import json
import re
import io
import speech_recognition as sr
import google.generativeai as genai
from streamlit_mic_recorder import mic_recorder

# --- НАСТРОЙКА СТРАНИЦЫ ---
st.set_page_config(page_title="Vocational English for IT", layout="wide", page_icon="💻")

# --- ИНИЦИАЛИЗАЦИЯ СОСТОЯНИЯ ---
if "progress" not in st.session_state:
    st.session_state.progress = {
        "xp": 0,
        "unlocked_levels": ["Unit 1: Working in IT_Vocabulary"],
        "completed_tasks": []
    }

# --- ДАННЫЕ УЧЕБНИКА (ВЫЖИМКА ИЗ 8 ЮНИТОВ) ---
TRANSLATIONS = {
    "software": "программное обеспечение",
    "hardware": "аппаратное обеспечение",
    "developer": "разработчик",
    "network": "сеть",
    "database": "база данных",
    "troubleshoot": "устранять неполадки",
    "schedule": "расписание",
    "maintenance": "техническое обслуживание",
    "reliable": "надежный",
    "analytics": "аналитика",
    "purpose": "цель",
    "storage": "хранилище",
    "e-commerce": "электронная коммерция",
    "encryption": "шифрование",
    "bandwidth": "пропускная способность",
    "malware": "вредоносное ПО",
    "prohibition": "запрет",
    "firewall": "межсетевой экран",
    "headquarters": "штаб-квартира",
    "query": "запрос",
    "backup": "резервное копирование",
    "router": "маршрутизатор"
}

COURSE_DATA = {
    "Unit 1: Working in IT": {
        "Vocabulary": [
            {"type": "choice", "question": "What does a software developer do?", "options": ["Writes code", "Fixes hardware", "Sells computers"], "answer": "Writes code"},
            {"type": "choice", "question": "What is the job of a network administrator?", "options": ["Design databases", "Maintain the company network", "Create graphics"], "answer": "Maintain the company network"}
        ],
        "Grammar": [
            {"type": "choice", "question": "Where _____ you from?", "options": ["is", "are", "am"], "answer": "are"},
            {"type": "choice", "question": "She _____ for Microsoft.", "options": ["work", "working", "works"], "answer": "works"}
        ],
        "Reading": [
            {"type": "text", "question": "Complete the phrase: 'Pleased to ____ you.'", "answer": "meet"}
        ],
        "Challenge (Speaking & Mixed)": [
            {"type": "speaking", "question": "Introduce yourself. Say your name, your job (e.g. software developer), and your company.", "keywords": ["name", "am", "work", "developer", "company"]}
        ]
    },
    "Unit 2: Computer Systems": {
        "Vocabulary": [
            {"type": "choice", "question": "Which component is the 'brain' of the computer?", "options": ["RAM", "CPU", "Hard Drive"], "answer": "CPU"},
        ],
        "Grammar": [
            {"type": "choice", "question": "My new computer is _____ than the old one.", "options": ["fast", "faster", "fastest"], "answer": "faster"},
            {"type": "choice", "question": "You _____ update your antivirus regularly.", "options": ["must", "can't", "don't have to"], "answer": "must"}
        ],
        "Challenge (Speaking & Mixed)": [
            {"type": "text", "question": "Type the superlative form of 'reliable'.", "answer": "most reliable"}
        ]
    },
    "Unit 3: Websites": {
        "Vocabulary": [
            {"type": "choice", "question": "Which tool shows how many people visit a website?", "options": ["Website analytics", "Web development", "Database"], "answer": "Website analytics"}
        ],
        "Grammar": [
            {"type": "choice", "question": "_____ websites do you visit?", "options": ["Which", "Who", "Where"], "answer": "Which"}
        ],
        "Challenge (Speaking & Mixed)": [
            {"type": "speaking", "question": "Explain the purpose of an educational website in one sentence.", "keywords": ["educate", "learn", "information", "share", "knowledge"]}
        ]
    },
    "Unit 4: Databases": {
        "Vocabulary": [
            {"type": "choice", "question": "What do we use to store data in rows and columns?", "options": ["A router", "A database", "A firewall"], "answer": "A database"}
        ],
        "Grammar": [
            {"type": "choice", "question": "_____ you help me with this SQL query, please?", "options": ["Could", "Must", "Are"], "answer": "Could"}
        ],
        "Challenge (Speaking & Mixed)": [
            {"type": "text", "question": "Complete: Data processing step where data is checked for faults is called data ______.", "answer": "validation"}
        ]
    },
    "Unit 5: E-commerce": {
        "Vocabulary": [
            {"type": "choice", "question": "B2B stands for...", "options": ["Business to Buyer", "Business to Business", "Back to Basics"], "answer": "Business to Business"}
        ],
        "Grammar": [
            {"type": "choice", "question": "We use _____ to link sentences that describe similar actions.", "options": ["but", "so", "and"], "answer": "and"}
        ],
        "Challenge (Speaking & Mixed)": [
            {"type": "text", "question": "Hackers _____ be able to get into the network if we use strong encryption.", "answer": "won't"}
        ]
    },
    "Unit 6: Network Systems": {
        "Vocabulary": [
            {"type": "choice", "question": "A network that connects computers over a small area is a...", "options": ["WAN", "LAN", "VPN"], "answer": "LAN"}
        ],
        "Grammar": [
            {"type": "choice", "question": "When _____ they launch the new network?", "options": ["do", "did", "have"], "answer": "did"}
        ],
        "Challenge (Speaking & Mixed)": [
            {"type": "speaking", "question": "Suggest a solution for slow internet speed.", "keywords": ["router", "check", "restart", "provider", "cable"]}
        ]
    },
    "Unit 7: IT Support": {
        "Vocabulary": [
            {"type": "choice", "question": "If the screen is black, the monitor might be...", "options": ["unplugged", "running", "downloading"], "answer": "unplugged"}
        ],
        "Grammar": [
            {"type": "choice", "question": "_____ he switched off the computer?", "options": ["Has", "Have", "Did"], "answer": "Has"}
        ],
        "Challenge (Speaking & Mixed)": [
            {"type": "text", "question": "Complete the Present Perfect sentence: 'I have _____ (check) the cables.'", "answer": "checked"}
        ]
    },
    "Unit 8: IT Security and Safety": {
        "Vocabulary": [
            {"type": "choice", "question": "Malicious software that copies itself is a...", "options": ["Firewall", "Virus", "Patch"], "answer": "Virus"}
        ],
        "Grammar": [
            {"type": "choice", "question": "You _____ give your password to anyone.", "options": ["mustn't", "don't have to", "might"], "answer": "mustn't"}
        ],
        "Challenge (Speaking & Mixed)": [
            {"type": "speaking", "question": "Explain one important health and safety rule for computer users.", "keywords": ["back", "eyes", "screen", "break", "straight"]}
        ]
    }
}

# --- ФУНКЦИИ ---
def render_smart_text(text):
    """Оборачивает слова в HTML для показа перевода по наведению"""
    processed_text = text
    for eng, rus in TRANSLATIONS.items():
        # Регулярка для замены с сохранением регистра
        pattern = re.compile(rf'\b({eng})\b', re.IGNORECASE)
        replacement = f'<span title="{rus}" style="border-bottom: 1px dashed #4CAF50; cursor: help; color: #4CAF50;">\\1</span>'
        processed_text = pattern.sub(replacement, processed_text)
    return processed_text

def get_gemini_explanation(question, user_ans, correct_ans, api_key):
    """Отправка запроса в Gemini API (с контекстом EPAM/IT)"""
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    prompt = f"""
    Пользователь изучает IT-английский и допустил ошибку в упражнении.
    Задание: '{question}'
    Ответ пользователя: '{user_ans}'
    Правильный ответ: '{correct_ans}'
    
    Твоя задача как Senior IT Mentor:
    1. Вежливо объясни на русском языке, почему ответ пользователя неверный, а правильный именно '{correct_ans}'.
    2. Объясни грамматическое правило или лексику.
    3. Приведи реалистичный пример (1-2 предложения) того, как это слово/фраза используется в повседневной работе разработчика или DevOps инженера (например, в EPAM, на митинге, в Jira, при общении с заказчиком).
    Форматируй ответ красиво с помощью Markdown.
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Ошибка при обращении к Gemini API: {e}"

def process_audio(audio_bytes):
    """Распознавание речи через SpeechRecognition"""
    r = sr.Recognizer()
    audio_file = io.BytesIO(audio_bytes)
    try:
        with sr.AudioFile(audio_file) as source:
            audio_data = r.record(source)
            text = r.recognize_google(audio_data, language="en-US")
            return text
    except Exception as e:
        return f"Error: Could not recognize speech. {str(e)}"

# --- ИНТЕРФЕЙС ---
st.sidebar.title("👨‍💻 IT English Platform")

# Настройки API
api_key = st.sidebar.text_input("Gemini API Key (Для разбора ошибок)", type="password")
st.sidebar.markdown("[Get API key here](https://aistudio.google.com/app/apikey)")

# Профиль и Прогресс
st.sidebar.divider()
st.sidebar.subheader("Твой Прогресс")
st.sidebar.metric("Опыт (XP)", st.session_state.progress['xp'])

# Синхронизация прогресса
st.sidebar.divider()
st.sidebar.subheader("Синхронизация")
export_data = json.dumps(st.session_state.progress)
st.sidebar.download_button("💾 Экспорт прогресса", export_data, file_name="it_english_progress.json", mime="application/json")

uploaded_file = st.sidebar.file_uploader("📂 Импорт прогресса", type="json")
if uploaded_file is not None:
    try:
        st.session_state.progress = json.load(uploaded_file)
        st.sidebar.success("Прогресс успешно загружен!")
    except Exception:
        st.sidebar.error("Ошибка чтения файла.")

# --- ГЛАВНЫЙ ЭКРАН ---
st.title("English for Information Technology 🚀")
st.markdown("Наведите курсор на выделенные зеленым слова для перевода!")

# Навигация
unit_names = list(COURSE_DATA.keys())
selected_unit = st.selectbox("📚 Выберите модуль (Unit)", unit_names)

levels = list(COURSE_DATA[selected_unit].keys())
selected_level = st.radio("Уровень", levels, horizontal=True)

level_id = f"{selected_unit}_{selected_level}"

# Блокировка уровней (Разблокирован ли уровень?)
if level_id not in st.session_state.progress["unlocked_levels"] and level_id != f"{selected_unit}_{levels[0]}":
    st.warning(f"🔒 Этот уровень закрыт. Пройдите предыдущие уровни в {selected_unit}, чтобы открыть его.")
else:
    st.markdown(f"### {selected_unit} — {selected_level}")
    tasks = COURSE_DATA[selected_unit][selected_level]
    
    all_passed = True
    
    for i, task in enumerate(tasks):
        task_id = f"{level_id}_task_{i}"
        
        st.markdown(f"**Question {i+1}:** " + render_smart_text(task["question"]), unsafe_allow_html=True)
        
        if task["type"] == "choice":
            user_ans = st.radio("Select answer:", task["options"], key=f"radio_{task_id}")
            if st.button("Check", key=f"btn_{task_id}"):
                if user_ans == task["answer"]:
                    st.success("Correct! +10 XP")
                    if task_id not in st.session_state.progress["completed_tasks"]:
                        st.session_state.progress["xp"] += 10
                        st.session_state.progress["completed_tasks"].append(task_id)
                else:
                    st.error("Incorrect.")
                    all_passed = False
                    if api_key:
                        with st.spinner("Спрашиваем Senior-разработчика (Gemini)..."):
                            explanation = get_gemini_explanation(task["question"], user_ans, task["answer"], api_key)
                            st.info(explanation)
                    else:
                        st.warning("Введите Gemini API ключ в боковой панели, чтобы получить подробный разбор ошибки.")
                        
        elif task["type"] == "text":
            user_ans = st.text_input("Type your answer:", key=f"text_{task_id}")
            if st.button("Check", key=f"btn_{task_id}"):
                if user_ans.strip().lower() == task["answer"].lower():
                    st.success("Correct! +15 XP")
                    if task_id not in st.session_state.progress["completed_tasks"]:
                        st.session_state.progress["xp"] += 15
                        st.session_state.progress["completed_tasks"].append(task_id)
                else:
                    st.error("Incorrect.")
                    all_passed = False
                    if api_key:
                        with st.spinner("Анализируем через Gemini..."):
                            explanation = get_gemini_explanation(task["question"], user_ans, task["answer"], api_key)
                            st.info(explanation)
                            
        elif task["type"] == "speaking":
            st.info("🎤 Нажмите кнопку ниже, чтобы записать ваш голос.")
            audio = mic_recorder(start_prompt="🔴 Record", stop_prompt="⏹️ Stop", key=f"mic_{task_id}")
            
            if audio:
                st.audio(audio['bytes'])
                with st.spinner("Распознаем речь..."):
                    spoken_text = process_audio(audio['bytes'])
                    st.write(f"**Ваш ответ:** {spoken_text}")
                    
                    if "Error" in spoken_text:
                        st.error(spoken_text)
                        all_passed = False
                    else:
                        # Простая проверка по ключевым словам
                        matches = sum(1 for kw in task["keywords"] if kw.lower() in spoken_text.lower())
                        if matches >= len(task["keywords"]) / 2: # Хотя бы половина ключей
                            st.success("Great job! Speech recognized and context matches. +20 XP")
                            if task_id not in st.session_state.progress["completed_tasks"]:
                                st.session_state.progress["xp"] += 20
                                st.session_state.progress["completed_tasks"].append(task_id)
                        else:
                            st.warning("Не все ключевые конструкции использованы. Попробуйте сформулировать ответ иначе.")
                            all_passed = False
                            
        st.divider()

    # Логика разблокировки следующего уровня
    if all_passed and st.session_state.progress["completed_tasks"]:
        current_lvl_idx = levels.index(selected_level)
        if current_lvl_idx < len(levels) - 1:
            next_level = f"{selected_unit}_{levels[current_lvl_idx + 1]}"
            if next_level not in st.session_state.progress["unlocked_levels"]:
                st.session_state.progress["unlocked_levels"].append(next_level)
                st.balloons()
                st.success(f"🎉 Вы открыли следующий уровень: {levels[current_lvl_idx + 1]}!")
