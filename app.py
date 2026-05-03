import streamlit as st
import json
import google.generativeai as genai

# Настройка страницы
st.set_page_config(page_title="IT English Duolingo", layout="centered")

# CSS для "кликабельного перевода" (tooltips)
st.markdown("""
<style>
    .word { border-bottom: 1px dotted #555; cursor: help; position: relative; display: inline-block; }
    .word:hover::after {
        content: attr(data-translation);
        position: absolute; bottom: 125%; left: 50%; transform: translateX(-50%);
        background: #333; color: #fff; padding: 5px; border-radius: 5px; font-size: 14px; white-space: nowrap; z-index: 10;
    }
</style>
""", unsafe_allow_html=True)

# Инициализация ИИ (Gemini)
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-1.5-flash')

# Контент Unit 1 из книги
CONTENT = {
    "Unit 1": {
        "title": "Working in the IT industry",
        "levels": [
            {
                "id": "jobs",
                "task": "Match the IT job to its description",
                "options": ["System Analyst", "Network Administrator", "Database Administrator"],
                "question": "Who solves computer problems and designs systems?",
                "answer": "System Analyst",
                "translation": "Кто решает компьютерные проблемы и проектирует системы?"
            },
            {
                "id": "acronyms",
                "task": "What does HTML stand for?",
                "options": ["HyperText Markup Language", "High Tech Modern Language"],
                "answer": "HyperText Markup Language",
                "translation": "Что означает аббревиатура HTML?"
            }
        ]
    }
}

# Функция для отображения кликабельного текста
def clickable_text(text, translation):
    return f'<span class="word" data-translation="{translation}">{text}</span>'

st.title("🚀 IT English Prep")

# Сайдбар для импорта/экспорта прогресса
with st.sidebar:
    st.header("Progress Sync")
    if st.button("Export Progress"):
        st.download_button("Download JSON", data=json.dumps({"xp": 100}), file_name="progress.json")
    st.file_uploader("Import Progress", type="json")

# Логика уровней
st.header(f"Topic: {CONTENT['Unit 1']['title']}")
level_idx = st.session_state.get("level", 0)
current_level = CONTENT["Unit 1"]["levels"][level_idx]

st.subheader(f"Level {level_idx + 1}")
st.markdown(clickable_text(current_level["task"], "Задание"), unsafe_allow_html=True)
st.write(current_level["question"])

user_choice = st.radio("Choose correct answer:", current_level["options"])

if st.button("Check!"):
    if user_choice == current_level["answer"]:
        st.success("Correct! +10 XP")
        # Здесь будет логика перехода к следующему уровню
    else:
        # Gemini объясняет ошибку
        response = model.generate_content(f"Объясни кратко на русском, почему в контексте ИТ ответ {user_choice} неверный для вопроса {current_level['question']}")
        st.error(f"Try again! Hint: {response.text}")
