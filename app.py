import streamlit as st
import pandas as pd
import sqlite3
import json
import datetime
import re
import streamlit.components.v1 as components

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="AMC Exam Portal Pro", layout="wide", page_icon="🎓")

# --- 2. LOCAL DB SETUP ---
# Initializes SQLite database for saving mappings offline
conn = sqlite3.connect('amc_exams_local.db', check_same_thread=False)
cursor = conn.cursor()

def init_db():
    cursor.execute('''CREATE TABLE IF NOT EXISTS exams 
                      (id TEXT PRIMARY KEY, course_code TEXT, exam_data TEXT, status TEXT, last_updated TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS syllabus 
                      (course_code TEXT, topic TEXT, mapped_co TEXT)''')
    conn.commit()

init_db()

# --- 3. LOAD BLOOM'S TAXONOMY ---
@st.cache_data
def load_blooms_taxonomy():
    try:
        # Assumes the CSV is in the same directory as app.py
        df = pd.read_csv('blooms taxonomy.xlsx - Sheet1.csv')
        return dict(zip(df['Verb'].astype(str).str.lower().str.strip(), df['Level'].astype(str).str.strip()))
    except Exception as e:
        return {} # Fallback to empty if missing

blooms_dict = load_blooms_taxonomy()

def suggest_bloom_level(text):
    if not text: return "L1"
    words = re.findall(r'\b\w+\b', text.lower())
    for word in words[:5]: # Scan the first few words for verbs
        if word in blooms_dict:
            return blooms_dict[word]
    return "L1"

# --- 4. STATE MANAGEMENT ---
if 'exam_details' not in st.session_state:
    st.session_state.exam_details = {'institution': 'AMC Engineering College', 'courseCode': 'CS501', 'courseName': 'Software Engineering', 'maxMarks': 50, 'duration': '3 Hours'}
if 'sections' not in st.session_state:
    st.session_state.sections = [{'id': 1, 'isNote': False, 'questions': [{'id': 101, 'qNo': '1.a', 'text': '', 'marks': 10, 'co': 'CO1', 'level': 'L1'}]}]

def add_section():
    new_id = int(datetime.datetime.now().timestamp() * 1000)
    st.session_state.sections.append({
        'id': new_id, 
        'isNote': False, 
        'questions': [{'id': new_id + 1, 'qNo': '', 'text': '', 'marks': 0, 'co': 'CO1', 'level': 'L1'}]
    })

# --- 5. DASHBOARD & HTML LOGIC ---
def calculate_metrics():
    total_marks = 0
    blooms_marks = {"L1": 0, "L2": 0, "L3": 0, "L4": 0, "L5": 0, "L6": 0}
    co_marks = {"CO1": 0, "CO2": 0, "CO3": 0, "CO4": 0, "CO5": 0, "CO6": 0}
    
    for section in st.session_state.sections:
        if not section.get('isNote'):
            for q in section['questions']:
                if q['text'].strip().upper() != 'OR':
                    m = float(q['marks']) if q['marks'] else 0
                    total_marks += m
                    level = q.get('level', 'L1')
                    co = q.get('co', 'CO1')
                    if level in blooms_marks: blooms_marks[level] += m
                    if co in co_marks: co_marks[co] += m
                    
    return total_marks, blooms_marks, co_marks

def generate_html():
    html = f"""
    <div style="font-family: Arial, sans-serif; padding: 20px; border: 1px solid #ccc; max-width: 800px; margin: auto; background-color: white;">
        <h3 style="text-align: center; margin-bottom: 5px;">{st.session_state.exam_details['institution']}</h3>
        <h4 style="text-align: center; margin-top: 0;">Course Code: {st.session_state.exam_details['courseCode']} - {st.session_state.exam_details['courseName']}</h4>
        <div style="display: flex; justify-content: space-between; border-bottom: 2px solid #000; padding-bottom: 10px; margin-bottom: 20px;">
            <span><b>Duration:</b> {st.session_state.exam_details['duration']}</span>
            <span><b>Max Marks:</b> {st.session_state.exam_details['maxMarks']}</span>
        </div>
        <table style="width: 100%; border-collapse: collapse;">
            <tr>
                <th style="border: 1px solid #000; padding: 5px; width: 10%;">Q.No</th>
                <th style="border: 1px solid #000; padding: 5px; width: 60%;">Question</th>
                <th style="border: 1px solid #000; padding: 5px; width: 10%;">Marks</th>
                <th style="border: 1px solid #000; padding: 5px; width: 10%;">CO</th>
                <th style="border: 1px solid #000; padding: 5px; width: 10%;">Bloom's</th>
            </tr>
    """
    for sec in st.session_state.sections:
        if not sec.get('isNote'):
            for q in sec['questions']:
                if q['text'].strip().upper() == 'OR':
                    # Syntax error fixed here: uses single quotes inside the style tags
                    html += f"<tr><td colspan='5' style='text-align: center; font-weight: bold; padding: 10px;'>--- OR ---</td></tr>"
                else:
                    html += f"""
                    <tr>
                        <td style="border: 1px solid #000; padding: 5px; text-align: center;">{q['qNo']}</td>
                        <td style="border: 1px solid #000; padding: 5px;">{q['text']}</td>
                        <td style="border: 1px solid #000; padding: 5px; text-align: center;">{q['marks']}</td>
                        <td style="border: 1px solid #000; padding: 5px; text-align: center;">{q['co']}</td>
                        <td style="border: 1px solid #000; padding: 5px; text-align: center;">{q['level']}</td>
                    </tr>
                    """
    html += "</table></div>"
    return html

# --- 6. MAIN UI: SIDE-BY-SIDE LAYOUT ---
st.title("📋 Exam Dashboard Workspace")

col_edit, col_view = st.columns([1.2, 1], gap="large")

# === LEFT COLUMN: EDITOR ===
with col_edit:
    st.header("📝 Question Editor")
    
    with st.expander("Header Details", expanded=False):
        st.session_state.exam_details['institution'] = st.text_input("Institution", st.session_state.exam_details['institution'])
        col1, col2 = st.columns(2)
        st.session_state.exam_details['courseCode'] = col1.text_input("Course Code", st.session_state.exam_details['courseCode'])
        st.session_state.exam_details['courseName'] = col2.text_input("Course Name", st.session_state.exam_details['courseName'])
        st.session_state.exam_details['maxMarks'] = col1.number_input("Max Marks", value=int(st.session_state.exam_details['maxMarks']))
        st.session_state.exam_details['duration'] = col2.text_input("Duration", st.session_state.exam_details['duration'])

    st.divider()

    # Dynamic Question Blocks
    for i, section in enumerate(st.session_state.sections):
        st.markdown(f"**Question Block {i+1}**")
        if not section.get('isNote'):
            for j, q in enumerate(section['questions']):
                with st.container(border=True):
                    c_no, c_txt = st.columns([1, 5])
                    q['qNo'] = c_no.text_input("Q No.", q['qNo'], key=f"qn_{q['id']}")
                    q['text'] = c_txt.text_area("Question Text", q['text'], key=f"qt_{q['id']}")
                    
                    # Smart Tagging Execution
                    suggested_lvl = suggest_bloom_level(q['text'])
                    
                    c_mk, c_co, c_lvl = st.columns([2, 2, 2])
                    q['marks'] = c_mk.number_input("Marks", value=float(q['marks']), step=1.0, key=f"mk_{q['id']}")
                    q['co'] = c_co.selectbox("CO", ["CO1", "CO2", "CO3", "CO4", "CO5", "CO6"], index=int(q['co'][-1])-1 if q['co'] and q['co'][-1].isdigit() else 0, key=f"co_{q['id']}")
                    
                    # Set Selectbox default to the suggested level
                    b_opts = ["L1", "L2", "L3", "L4", "L5", "L6"]
                    b_index = b_opts.index(suggested_lvl) if suggested_lvl in b_opts else 0
                    q['level'] = c_lvl.selectbox("Bloom's", b_opts, index=b_index, key=f"lv_{q['id']}")

    st.button("➕ Add Question Block", on_click=add_section)

# === RIGHT COLUMN: LIVE DASHBOARD & PREVIEW ===
with col_view:
    st.header("📊 Live Dashboard")
    
    total_marks, blooms_marks, co_marks = calculate_metrics()
    max_m = st.session_state.exam_details['maxMarks']
    
    # Progress Bar / Mark Check
    if total_marks > max_m: st.error(f"Marks Exceeded: {total_marks}/{max_m}")
    elif total_marks < max_m: st.warning(f"Marks Shortfall: {total_marks}/{max_m}")
    else: st.success(f"Marks Balanced: {total_marks}/{max_m}")
    
    # Metrics
    if total_marks > 0:
        p_l12 = ((blooms_marks["L1"] + blooms_marks["L2"]) / total_marks) * 100
        p_l3 = (blooms_marks["L3"] / total_marks) * 100
        p_l456 = ((blooms_marks["L4"] + blooms_marks["L5"] + blooms_marks["L6"]) / total_marks) * 100
        
        c1, c2, c3 = st.columns(3)
        c1.metric("L1-L2 (Target 20-30%)", f"{p_l12:.1f}%", delta=f"{p_l12 - 25:.1f}%" if not (20<=p_l12<=30) else "On Target", delta_color="inverse" if not (20<=p_l12<=30) else "normal")
        c2.metric("L3 (Target 30-40%)", f"{p_l3:.1f}%", delta=f"{p_l3 - 35:.1f}%" if not (30<=p_l3<=40) else "On Target", delta_color="inverse" if not (30<=p_l3<=40) else "normal")
        c3.metric("L4-L6 (Target 30-50%)", f"{p_l456:.1f}%", delta=f"{p_l456 - 40:.1f}%" if not (30<=p_l456<=50) else "On Target", delta_color="inverse" if not (30<=p_l456<=50) else "normal")
    else:
        st.info("Assign marks to questions to see the distribution metrics.")
        
    st.divider()
    st.header("👁️ Live Preview")
    
    # Render HTML dynamically
    html_content = generate_html()
    components.html(html_content, height=600, scrolling=True)
    
    st.download_button(
        label="📥 Download HTML Template",
        data=html_content,
        file_name=f"{st.session_state.exam_details['courseCode']}_QP.html",
        mime="text/html",
        type="primary"
    )
