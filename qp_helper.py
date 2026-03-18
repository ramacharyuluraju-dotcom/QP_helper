import streamlit as st
import pandas as pd
import sqlite3
import datetime
import re
import streamlit.components.v1 as components

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="AMC Exam Portal Pro", layout="wide", page_icon="🎓")

# --- 2. LOCAL DB SETUP ---
conn = sqlite3.connect('amc_exams_local.db', check_same_thread=False)
cursor = conn.cursor()

def init_db():
    cursor.execute('''CREATE TABLE IF NOT EXISTS exams 
                      (id TEXT PRIMARY KEY, course_code TEXT, exam_data TEXT, status TEXT, last_updated TEXT)''')
    conn.commit()

init_db()

# --- 3. HARDCODED BLOOM'S TAXONOMY ENGINE (FIXED) ---
@st.cache_data
def load_blooms_taxonomy():
    blooms_data = {
        "L1": ["arrange", "cite", "define", "describe", "duplicate", "enumerate", "identify", "label", "list", "match", "memorize", "name", "order", "outline", "recall", "recognize", "record", "relate", "repeat", "reproduce", "select", "state", "tabulate", "tell"],
        "L2": ["approximate", "articulate", "categorize", "characterize", "clarify", "classify", "compare", "comprehend", "conclude", "contrast", "convert", "defend", "demonstrate", "discuss", "distinguish", "estimate", "explain", "express", "extend", "generalize", "illustrate", "indicate", "infer", "interpret", "locate", "paraphrase", "predict", "rephrase", "report", "restate", "review", "rewrite", "show", "summarize", "translate"],
        "L3": ["adapt", "allocate", "apply", "build", "calculate", "change", "choose", "compute", "conduct", "construct", "determine", "develop", "discover", "employ", "execute", "experiment", "function", "implement", "interview", "manipulate", "model", "modify", "operate", "practice", "produce", "schedule", "sketch", "solve", "use"],
        "L4": ["analyze", "appraise", "breakdown", "categorize", "classify", "compare", "conclude", "contrast", "criticize", "deduce", "derive", "differentiate", "discriminate", "distinguish", "examine", "experiment", "infer", "inspect", "inventory", "investigate", "model", "organize", "outline", "prioritize", "question", "relate", "separate", "simplify", "subdivide", "survey", "test"],
        "L5": ["agree", "appraise", "argue", "assess", "award", "choose", "compare", "conclude", "critique", "criticize", "decide", "deduct", "defend", "discriminate", "disprove", "estimate", "evaluate", "explain", "grade", "influence", "interpret", "judge", "justify", "mark", "measure", "perceive", "predict", "prioritize", "prove", "rate", "recommend", "score", "select", "support", "test", "validate", "value", "verify"],
        "L6": ["adapt", "arrange", "assemble", "build", "change", "combine", "compile", "compose", "construct", "create", "delete", "design", "develop", "devise", "elaborate", "estimate", "formulate", "generate", "imagine", "improve", "invent", "manage", "maximize", "minimize", "modify", "optimize", "organize", "originate", "plan", "predict", "prepare", "produce", "propose", "reconstruct", "revise", "rewrite", "synthesize"]
    }
    
    verb_dict = {}
    for level, verbs in blooms_data.items():
        for verb in verbs:
            if verb.lower() not in verb_dict:
                verb_dict[verb.lower()] = level
                
    return verb_dict

blooms_dict = load_blooms_taxonomy()

# --- 4. ADVANCED 2D SYLLABUS MAPPING ENGINE ---
advanced_syllabus_mapping = {
    "rectifier":  {"L1": "CO1", "L2": "CO1", "L3": "CO3", "L4": "CO3", "L5": "CO3", "L6": "CO3"},
    "diode":      {"L1": "CO1", "L2": "CO1", "L3": "CO3", "L4": "CO3", "L5": "CO3", "L6": "CO3"},
    "amplifier":  {"L1": "CO1", "L2": "CO1", "L3": "CO3", "L4": "CO3", "L5": "CO3", "L6": "CO3"},
    "op-amp":     {"L1": "CO1", "L2": "CO1", "L3": "CO3", "L4": "CO3", "L5": "CO3", "L6": "CO3"},
    "oscillator": {"L1": "CO1", "L2": "CO1", "L3": "CO3", "L4": "CO3", "L5": "CO3", "L6": "CO3"},
    "filter":     {"L1": "CO1", "L2": "CO1", "L3": "CO3", "L4": "CO3", "L5": "CO3", "L6": "CO3"},
    "number system": {"L1": "CO2", "L2": "CO2", "L3": "CO4", "L4": "CO4", "L5": "CO4", "L6": "CO4"},
    "logic circuit": {"L1": "CO2", "L2": "CO2", "L3": "CO4", "L4": "CO4", "L5": "CO4", "L6": "CO4"},
    "boolean":       {"L1": "CO2", "L2": "CO2", "L3": "CO4", "L4": "CO4", "L5": "CO4", "L6": "CO4"},
    "gates":         {"L1": "CO2", "L2": "CO2", "L3": "CO4", "L4": "CO4", "L5": "CO4", "L6": "CO4"},
    "communication": {"L1": "CO2", "L2": "CO2", "L3": "CO4", "L4": "CO4", "L5": "CO4", "L6": "CO4"},
    "develop":  {"L1": "CO5", "L2": "CO5", "L3": "CO5", "L4": "CO5", "L5": "CO5", "L6": "CO5"},
    "sensors":  {"L1": "CO5", "L2": "CO5", "L3": "CO5", "L4": "CO5", "L5": "CO5", "L6": "CO5"},
    "embedded": {"L1": "CO5", "L2": "CO5", "L3": "CO5", "L4": "CO5", "L5": "CO5", "L6": "CO5"}
}

def auto_tag_question(text):
    if not text: return "L1", "CO1"
    
    suggested_lvl = "L1"
    suggested_co = "CO1"
    text_lower = text.lower()
    
    words = re.findall(r'\b[a-zA-Z-]+\b', text_lower)
    for word in words[:7]: 
        if word in blooms_dict:
            suggested_lvl = blooms_dict[word]
            break
            
    for keyword, level_rules in advanced_syllabus_mapping.items():
        if re.search(r'\b' + re.escape(keyword) + r'\b', text_lower):
            suggested_co = level_rules.get(suggested_lvl, "CO1")
            break 
            
    return suggested_lvl, suggested_co

# --- HTML GENERATOR (FIXED MODULE GROUPING) ---
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
    
    # We keep track of the last module printed so we don't repeat the header
    last_printed_module = None
    
    for sec in st.session_state.sections:
        if not sec.get('isNote'):
            current_module = sec.get('module', 'Module 1')
            
            # ONLY print the header if the module has changed!
            if current_module != last_printed_module:
                html += f"<tr><td colspan='5' style='text-align: center; font-weight: bold; padding: 8px; background-color: #f0f2f6; border: 1px solid #000;'>--- {current_module.upper()} ---</td></tr>"
                last_printed_module = current_module
            
            for q in sec['questions']:
                if q['text'].strip().upper() == 'OR':
                    html += f"<tr><td colspan='5' style='text-align: center; font-weight: bold; padding: 10px; background:#fff;'>--- OR ---</td></tr>"
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

# --- 5. STATE MANAGEMENT ---
if 'exam_details' not in st.session_state:
    st.session_state.exam_details = {
        'institution': 'AMC Engineering College', 'courseCode': '1BESC104C', 
        'courseName': 'Intro to Electronics and Communication Engg', 'maxMarks': 50, 'duration': '3 Hours'
    }

if 'sections' not in st.session_state:
    st.session_state.sections = [
        {'id': 100, 'module': 'Module 1', 'isNote': False, 'questions': [
            {'id': 101, 'qNo': '1.a', 'text': 'Define PN junction diode and its characteristics.', 'marks': 5, 'co': 'CO1', 'level': 'L1'},
            {'id': 102, 'qNo': '1.b', 'text': 'Explain the working of full wave rectifier.', 'marks': 5, 'co': 'CO1', 'level': 'L1'}
        ]},
        {'id': 200, 'module': 'Module 2', 'isNote': False, 'questions': [
            {'id': 201, 'qNo': '2.a', 'text': 'Determine the ripple factor of a half wave rectifier.', 'marks': 5, 'co': 'CO1', 'level': 'L1'}
        ]}
    ]

def add_section():
    new_id = int(datetime.datetime.now().timestamp() * 1000)
    current_modules = len(st.session_state.sections)
    next_mod_num = current_modules + 1 if current_modules < 5 else 5
    
    st.session_state.sections.append({
        'id': new_id, 'module': f'Module {next_mod_num}', 'isNote': False, 
        'questions': [{'id': new_id + 1, 'qNo': '', 'text': '', 'marks': 0, 'co': 'CO1', 'level': 'L1'}]
    })

def update_tags(q_id, sec_idx, q_idx):
    typed_text = st.session_state[f"qt_{q_id}"]
    new_level, new_co = auto_tag_question(typed_text)
    
    st.session_state[f"lv_{q_id}"] = new_level
    st.session_state[f"co_{q_id}"] = new_co
    
    st.session_state.sections[sec_idx]['questions'][q_idx]['text'] = typed_text
    st.session_state.sections[sec_idx]['questions'][q_idx]['level'] = new_level
    st.session_state.sections[sec_idx]['questions'][q_idx]['co'] = new_co

def add_sub_question(sec_idx):
    new_id = int(datetime.datetime.now().timestamp() * 1000)
    st.session_state.sections[sec_idx]['questions'].append({
        'id': new_id, 'qNo': '', 'text': '', 'marks': 0, 'co': 'CO1', 'level': 'L1'
    })

# --- 6. MAIN UI ---
st.title("📋 Exam Dashboard Workspace")

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

    st.divider()

    for i, section in enumerate(st.session_state.sections):
        with st.container(border=True):
            mod_col, title_col = st.columns([1, 3])
            mod_options = ["Module 1", "Module 2", "Module 3", "Module 4", "Module 5"]
            current_mod = section.get('module', 'Module 1')
            mod_idx = mod_options.index(current_mod) if current_mod in mod_options else 0
            
            # Allow user to change the module for this block
            section['module'] = mod_col.selectbox(f"Block {i+1} Assignment", mod_options, index=mod_idx, key=f"mod_sel_{section['id']}")
            
            if not section.get('isNote'):
                for j, q in enumerate(section['questions']):
                    c_no, c_txt = st.columns([1, 5])
                    q['qNo'] = c_no.text_input("Q No.", q['qNo'], key=f"qn_{q['id']}")
                    
                    c_txt.text_area("Question Text (Ctrl+Enter to auto-tag)", q['text'], key=f"qt_{q['id']}", 
                                    on_change=update_tags, args=(q['id'], i, j))
                    
                    c_mk, c_co, c_lvl = st.columns([2, 2, 2])
                    q['marks'] = c_mk.number_input("Marks", value=float(q['marks']), step=1.0, key=f"mk_{q['id']}")
                    
                    if f"co_{q['id']}" not in st.session_state: 
                        st.session_state[f"co_{q['id']}"] = q.get('co', 'CO1')
                    q['co'] = c_co.selectbox("CO", ["CO1", "CO2", "CO3", "CO4", "CO5", "CO6"], key=f"co_{q['id']}")
                    
                    if f"lv_{q['id']}" not in st.session_state: 
                        st.session_state[f"lv_{q['id']}"] = q.get('level', 'L1')
                    q['level'] = c_lvl.selectbox("Bloom's", ["L1", "L2", "L3", "L4", "L5", "L6"], key=f"lv_{q['id']}")
                    
                st.button("➕ Add Sub-Question", key=f"add_sub_{section['id']}", on_click=add_sub_question, args=(i,))

    st.button("➕ Add New Block", on_click=add_section)

with col_view:
    st.header("📊 Live Dashboard")
    
    total_marks = sum([float(q['marks']) for s in st.session_state.sections for q in s['questions'] if not s.get('isNote')])
    blooms_marks = {"L1": 0, "L2": 0, "L3": 0, "L4": 0, "L5": 0, "L6": 0}
    for s in st.session_state.sections:
        for q in s['questions']: blooms_marks[q.get('level', 'L1')] += float(q['marks'])
    
    if total_marks > 0:
        p_l12 = ((blooms_marks["L1"] + blooms_marks["L2"]) / total_marks) * 100
        p_l3 = (blooms_marks["L3"] / total_marks) * 100
        p_l456 = ((blooms_marks["L4"] + blooms_marks["L5"] + blooms_marks["L6"]) / total_marks) * 100
        
        c1, c2, c3 = st.columns(3)
        c1.metric("L1-L2 (Target 20-30%)", f"{p_l12:.1f}%")
        c2.metric("L3 (Target 30-40%)", f"{p_l3:.1f}%")
        c3.metric("L4-L6 (Target 30-50%)", f"{p_l456:.1f}%")
        
    st.divider()
    st.header("👁️ Live Document Preview")
    
    html_content = generate_html()
    components.html(html_content, height=600, scrolling=True)
    
    st.download_button(
        label="📥 Download HTML Template",
        data=html_content,
        file_name=f"{st.session_state.exam_details['courseCode']}_QP.html",
        mime="text/html",
        type="primary"
    )
