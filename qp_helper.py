import streamlit as st
import pandas as pd
import sqlite3
import json
import datetime
import re
import streamlit.components.v1 as components

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="AMC Exam Portal Pro (Debug Mode)", layout="wide", page_icon="🎓")

# --- 2. LOCAL DB SETUP ---
conn = sqlite3.connect('amc_exams_local.db', check_same_thread=False)
cursor = conn.cursor()

def init_db():
    cursor.execute('''CREATE TABLE IF NOT EXISTS exams 
                      (id TEXT PRIMARY KEY, course_code TEXT, exam_data TEXT, status TEXT, last_updated TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS co_po_matrix 
                      (course_code TEXT, mapping_data TEXT)''')
    conn.commit()

init_db()

# --- 3. LOAD BLOOM'S TAXONOMY ---
@st.cache_data
def load_blooms_taxonomy():
    try:
        df = pd.read_csv('blooms taxonomy.xlsx - Sheet1.csv')
        return dict(zip(df['Verb'].astype(str).str.lower().str.strip(), df['Level'].astype(str).str.strip()))
    except Exception as e:
        # Fallback dictionary just in case the CSV fails to load during debugging
        return {"define": "L1", "explain": "L2", "determine": "L3", "derive": "L3", "calculate": "L3", "discuss": "L2", "construct": "L4", "demonstrate": "L3"}

blooms_dict = load_blooms_taxonomy()

# --- 4. MOCK SYLLABUS MAPPING (For 1BESC104C) ---
# This maps keywords from the syllabus topics to their official COs
syllabus_keywords_to_co = {
    "diode": "CO1", "rectifier": "CO1", "bjt": "CO1", "amplifier": "CO1", "oscillator": "CO1",
    "number system": "CO2", "logic circuits": "CO2", "gates": "CO2", "communication": "CO2", "modulation": "CO2",
    "op-amp": "CO3", "operational amplifier": "CO3", "ripple factor": "CO3", "zener": "CO3",
    "boolean": "CO4", "digital electronics": "CO4",
    "develop": "CO5", "sensors": "CO5", "embedded": "CO5"
}

def auto_tag_question(text):
    if not text: return "L1", "CO1"
    
    # 1. Guess Bloom's Level
    suggested_lvl = "L1"
    words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
    for word in words[:7]: 
        if word in blooms_dict:
            suggested_lvl = blooms_dict[word]
            break
            
    # 2. Guess CO based on Syllabus mapping
    suggested_co = "CO1" # Default
    text_lower = text.lower()
    for keyword, co in syllabus_keywords_to_co.items():
        if keyword in text_lower:
            suggested_co = co
            break # Takes the first major keyword found
            
    return suggested_lvl, suggested_co

# --- 5. STATE MANAGEMENT (Pre-loaded with 1BESC104C Data) ---
if 'exam_details' not in st.session_state:
    st.session_state.exam_details = {
        'institution': 'AMC Engineering College', 
        'courseCode': '1BESC104C', 
        'courseName': 'Intro to Electronics and Communication Engg', 
        'maxMarks': 50, 
        'duration': '3 Hours'
    }

if 'sections' not in st.session_state:
    # Pre-loading the first few questions from the provided HTML (Notice they are all incorrectly tagged CO1/L1 initially)
    st.session_state.sections = [
        {'id': 100, 'isNote': False, 'questions': [
            {'id': 101, 'qNo': '1.a', 'text': 'Define PN junction diode and its characteristics.', 'marks': 5, 'co': 'CO1', 'level': 'L1'},
            {'id': 102, 'qNo': '1.b', 'text': 'Explain the working of full wave rectifier.', 'marks': 5, 'co': 'CO1', 'level': 'L1'}
        ]},
        {'id': 200, 'isNote': False, 'questions': [
            {'id': 201, 'qNo': '2.a', 'text': 'Determine the ripple factor of a half wave rectifier.', 'marks': 5, 'co': 'CO1', 'level': 'L1'},
            {'id': 202, 'qNo': '2.b', 'text': 'Explain Switched Mode Power Supplies.', 'marks': 5, 'co': 'CO1', 'level': 'L1'}
        ]},
        {'id': 300, 'isNote': False, 'questions': [
            {'id': 301, 'qNo': '3.a', 'text': 'Derive expression for voltage regulation in Zener Diode.', 'marks': 5, 'co': 'CO1', 'level': 'L1'},
            {'id': 302, 'qNo': '3.b', 'text': 'Discuss operational amplifier parameters.', 'marks': 5, 'co': 'CO1', 'level': 'L1'}
        ]}
    ]

if 'co_po_df' not in st.session_state:
    # Pre-loaded with the corrected BOS Matrix
    cols = [f"PO{i}" for i in range(1, 13)]
    default_data = [
        ["2", "", "", "", "", "", "", "", "", "", "", ""], # CO1
        ["2", "", "", "", "", "", "", "", "", "", "", ""], # CO2
        ["3", "", "", "", "", "", "", "", "", "", "", ""], # CO3
        ["3", "", "", "", "", "", "", "", "", "", "", ""], # CO4
        ["3", "", "2", "", "1", "", "", "", "3", "1", "", ""]  # CO5
    ]
    df = pd.DataFrame(default_data, index=[f"CO{i}" for i in range(1, 6)], columns=cols)
    # Adding CO6 as blank just in case
    df.loc["CO6"] = [""] * 12
    st.session_state.co_po_df = df

def add_section():
    new_id = int(datetime.datetime.now().timestamp() * 1000)
    st.session_state.sections.append({
        'id': new_id, 
        'isNote': False, 
        'questions': [{'id': new_id + 1, 'qNo': '', 'text': '', 'marks': 0, 'co': 'CO1', 'level': 'L1'}]
    })

# --- CALLBACK TO FORCE SMART TAGGING ---
def update_tags(q_id, sec_idx, q_idx):
    typed_text = st.session_state[f"qt_{q_id}"]
    new_level, new_co = auto_tag_question(typed_text)
    
    # Update widgets
    st.session_state[f"lv_{q_id}"] = new_level
    st.session_state[f"co_{q_id}"] = new_co
    
    # Update data store
    st.session_state.sections[sec_idx]['questions'][q_idx]['text'] = typed_text
    st.session_state.sections[sec_idx]['questions'][q_idx]['level'] = new_level
    st.session_state.sections[sec_idx]['questions'][q_idx]['co'] = new_co

# --- 6. MAIN UI ---
st.title("📋 Exam Dashboard (1BESC104C Debug Mode)")

col_edit, col_view = st.columns([1.2, 1], gap="large")

with col_edit:
    st.header("📝 Question Editor")
    
    with st.expander("📝 1. Header Details", expanded=False):
        st.session_state.exam_details['institution'] = st.text_input("Institution", st.session_state.exam_details['institution'])
        col1, col2 = st.columns(2)
        st.session_state.exam_details['courseCode'] = col1.text_input("Course Code", st.session_state.exam_details['courseCode'])
        st.session_state.exam_details['courseName'] = col2.text_input("Course Name", st.session_state.exam_details['courseName'])
        st.session_state.exam_details['maxMarks'] = col1.number_input("Max Marks", value=int(st.session_state.exam_details['maxMarks']))
        st.session_state.exam_details['duration'] = col2.text_input("Duration", st.session_state.exam_details['duration'])

    with st.expander("🔗 2. Corrected CO-PO Matrix", expanded=True):
        st.write("This matrix is pre-loaded with the defensible mappings for 1BESC104C.")
        st.data_editor(st.session_state.co_po_df, use_container_width=True)

    st.divider()
    st.info("💡 **Debug Test:** Click inside the text box for Question 3.a or 3.b, add a space, and press Ctrl+Enter. Watch the Bloom's and CO auto-correct based on the syllabus!")

    for i, section in enumerate(st.session_state.sections):
        st.markdown(f"**Block {i+1}**")
        if not section.get('isNote'):
            for j, q in enumerate(section['questions']):
                with st.container(border=True):
                    c_no, c_txt = st.columns([1, 5])
                    q['qNo'] = c_no.text_input("Q No.", q['qNo'], key=f"qn_{q['id']}")
                    
                    # Triggers auto-tagging on change
                    c_txt.text_area("Question Text", q['text'], key=f"qt_{q['id']}", 
                                    on_change=update_tags, args=(q['id'], i, j))
                    
                    c_mk, c_co, c_lvl = st.columns([2, 2, 2])
                    q['marks'] = c_mk.number_input("Marks", value=float(q['marks']), step=1.0, key=f"mk_{q['id']}")
                    
                    # CO Selectbox (FIXED)
                    if f"co_{q['id']}" not in st.session_state: 
                        st.session_state[f"co_{q['id']}"] = q.get('co', 'CO1')
                    q['co'] = c_co.selectbox("CO", ["CO1", "CO2", "CO3", "CO4", "CO5", "CO6"], key=f"co_{q['id']}")
                    
                    # Bloom's Selectbox (FIXED)
                    if f"lv_{q['id']}" not in st.session_state: 
                        st.session_state[f"lv_{q['id']}"] = q.get('level', 'L1')
                    q['level'] = c_lvl.selectbox("Bloom's", ["L1", "L2", "L3", "L4", "L5", "L6"], key=f"lv_{q['id']}")

    st.button("➕ Add Question", on_click=add_section)

with col_view:
    st.header("📊 Live Dashboard")
    
    total_marks = sum([float(q['marks']) for s in st.session_state.sections for q in s['questions'] if not s.get('isNote')])
    blooms_marks = {"L1": 0, "L2": 0, "L3": 0, "L4": 0, "L5": 0, "L6": 0}
    for s in st.session_state.sections:
        for q in s['questions']: blooms_marks[q.get('level', 'L1')] += float(q['marks'])
    
    st.write(f"**Total Marks Assigned: {total_marks} / {st.session_state.exam_details['maxMarks']}**")
    
    if total_marks > 0:
        p_l12 = ((blooms_marks["L1"] + blooms_marks["L2"]) / total_marks) * 100
        p_l3 = (blooms_marks["L3"] / total_marks) * 100
        p_l456 = ((blooms_marks["L4"] + blooms_marks["L5"] + blooms_marks["L6"]) / total_marks) * 100
        
        c1, c2, c3 = st.columns(3)
        c1.metric("L1-L2 (Target 20-30%)", f"{p_l12:.1f}%")
        c2.metric("L3 (Target 30-40%)", f"{p_l3:.1f}%")
        c3.metric("L4-L6 (Target 30-50%)", f"{p_l456:.1f}%")
