import streamlit as st
import pandas as pd
import sqlite3
import datetime
import re
import json
import streamlit.components.v1 as components

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="AMC Exam Portal Pro", layout="wide", page_icon="🎓")

# --- 2. LOCAL DB SETUP & CRUD ---
conn = sqlite3.connect('amc_exams_local.db', check_same_thread=False)
cursor = conn.cursor()

def init_db():
    # Exams table (future use for saving full papers)
    cursor.execute('''CREATE TABLE IF NOT EXISTS exams (id TEXT PRIMARY KEY, course_code TEXT, exam_data TEXT, status TEXT, last_updated TEXT)''')
    # Custom Bloom's Dictionary
    cursor.execute('''CREATE TABLE IF NOT EXISTS custom_blooms (verb TEXT PRIMARY KEY, level TEXT)''')
    # Custom Syllabus to CO Mapping
    cursor.execute('''CREATE TABLE IF NOT EXISTS co_mappings (keyword TEXT PRIMARY KEY, rules TEXT)''')
    # Course Setup defaults
    cursor.execute('''CREATE TABLE IF NOT EXISTS course_setup (id INTEGER PRIMARY KEY, institution TEXT, course_code TEXT, course_name TEXT, max_marks INTEGER, duration TEXT)''')
    conn.commit()

init_db()

# --- 3. DYNAMIC DICTIONARIES (Merged Hardcoded + DB) ---
@st.cache_data(ttl=2) # Short TTL so DB updates reflect quickly
def load_blooms_taxonomy():
    # Base defaults (Included 'analyse' UK spelling!)
    verb_dict = {
        "define": "L1", "list": "L1", "state": "L1", "recall": "L1",
        "explain": "L2", "describe": "L2", "discuss": "L2", "compare": "L2",
        "calculate": "L3", "determine": "L3", "solve": "L3", "apply": "L3",
        "analyze": "L4", "analyse": "L4", "differentiate": "L4", "derive": "L4",
        "evaluate": "L5", "judge": "L5", "assess": "L5", "justify": "L5",
        "design": "L6", "develop": "L6", "create": "L6", "formulate": "L6"
    }
    # Merge with custom verbs from DB
    cursor.execute("SELECT verb, level FROM custom_blooms")
    for row in cursor.fetchall():
        verb_dict[row[0].lower()] = row[1]
    return verb_dict

@st.cache_data(ttl=2)
def load_syllabus_mapping():
    # Base defaults
    mapping = {
        "rectifier":  {"L1": "CO1", "L2": "CO1", "L3": "CO3", "L4": "CO3", "L5": "CO3", "L6": "CO3"},
        "op-amp":     {"L1": "CO1", "L2": "CO1", "L3": "CO3", "L4": "CO3", "L5": "CO3", "L6": "CO3"}
    }
    # Merge with DB mappings
    cursor.execute("SELECT keyword, rules FROM co_mappings")
    for row in cursor.fetchall():
        try:
            mapping[row[0].lower()] = json.loads(row[1])
        except:
            pass
    return mapping

blooms_dict = load_blooms_taxonomy()
advanced_syllabus_mapping = load_syllabus_mapping()

# --- 4. AUTO TAGGING ENGINE ---
def auto_tag_question(text):
    if not text: return "L1", "CO1"
    
    suggested_lvl = "L1"
    suggested_co = "CO1"
    text_lower = text.lower()
    
    # 1. FIND BLOOM'S
    words = re.findall(r'\b[a-zA-Z-]+\b', text_lower)
    for word in words[:7]: 
        if word in blooms_dict:
            suggested_lvl = blooms_dict[word]
            break
            
    # 2. FIND CO
    for keyword, level_rules in advanced_syllabus_mapping.items():
        if re.search(r'\b' + re.escape(keyword) + r'\b', text_lower):
            suggested_co = level_rules.get(suggested_lvl, "CO1")
            break 
            
    return suggested_lvl, suggested_co

# --- HTML GENERATOR ---
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
    last_printed_module = None
    for sec in st.session_state.sections:
        if not sec.get('isNote') and len(sec['questions']) > 0:
            current_module = sec.get('module', 'Module 1')
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

# --- STATE MANAGEMENT & CALLBACKS ---
def load_course_setup():
    cursor.execute("SELECT institution, course_code, course_name, max_marks, duration FROM course_setup WHERE id=1")
    row = cursor.fetchone()
    if row:
        return {'institution': row[0], 'courseCode': row[1], 'courseName': row[2], 'maxMarks': row[3], 'duration': row[4]}
    return {'institution': 'AMC Engineering College', 'courseCode': '1BESC104C', 'courseName': 'Intro to Electronics', 'maxMarks': 50, 'duration': '3 Hours'}

if 'exam_details' not in st.session_state:
    st.session_state.exam_details = load_course_setup()

if 'sections' not in st.session_state:
    st.session_state.sections = [
        {'id': 100, 'module': 'Module 1', 'isNote': False, 'questions': [
            {'id': 101, 'qNo': '', 'text': 'Define PN junction diode.', 'marks': 5, 'co': 'CO1', 'level': 'L1'}
        ]}
    ]

# ADD Functions
def add_section():
    new_id = int(datetime.datetime.now().timestamp() * 1000)
    current_modules = len(st.session_state.sections)
    next_mod_num = current_modules + 1 if current_modules < 5 else 5
    st.session_state.sections.append({
        'id': new_id, 'module': f'Module {next_mod_num}', 'isNote': False, 
        'questions': [{'id': new_id + 1, 'qNo': '', 'text': '', 'marks': 0, 'co': 'CO1', 'level': 'L1'}]
    })

def add_sub_question(sec_idx):
    new_id = int(datetime.datetime.now().timestamp() * 1000)
    st.session_state.sections[sec_idx]['questions'].append({
        'id': new_id, 'qNo': '', 'text': '', 'marks': 0, 'co': 'CO1', 'level': 'L1'
    })

# DELETE Functions
def delete_section(sec_idx):
    st.session_state.sections.pop(sec_idx)

def delete_sub_question(sec_idx, q_idx):
    st.session_state.sections[sec_idx]['questions'].pop(q_idx)

def update_tags(q_id, sec_idx, q_idx):
    typed_text = st.session_state[f"qt_{q_id}"]
    new_level, new_co = auto_tag_question(typed_text)
    
    st.session_state[f"lv_{q_id}"] = new_level
    st.session_state[f"co_{q_id}"] = new_co
    
    st.session_state.sections[sec_idx]['questions'][q_idx]['text'] = typed_text
    st.session_state.sections[sec_idx]['questions'][q_idx]['level'] = new_level
    st.session_state.sections[sec_idx]['questions'][q_idx]['co'] = new_co


# --- UI LAYOUT ---
st.title("🎓 AMC Exam Portal Pro")

# TWO TABS: The Editor, and the Setup Database
tab_editor, tab_setup = st.tabs(["📝 Exam Paper Editor", "⚙️ Course & DB Setup"])

with tab_editor:
    col_edit, col_view = st.columns([1.2, 1], gap="large")

    with col_edit:
        for i, section in enumerate(st.session_state.sections):
            with st.container(border=True):
                mod_col, del_blk_col = st.columns([4, 1])
                mod_options = ["Module 1", "Module 2", "Module 3", "Module 4", "Module 5"]
                current_mod = section.get('module', 'Module 1')
                mod_idx = mod_options.index(current_mod) if current_mod in mod_options else 0
                
                section['module'] = mod_col.selectbox(f"Main Question {i+1} Assignment", mod_options, index=mod_idx, key=f"mod_sel_{section['id']}")
                
                # DELETE BLOCK BUTTON
                del_blk_col.button("🗑️ Delete Block", key=f"del_blk_{section['id']}", on_click=delete_section, args=(i,), type="secondary")
                
                if not section.get('isNote'):
                    for j, q in enumerate(section['questions']):
                        # Auto Numbering
                        computed_qno = f"{i+1}.{chr(97+j)}"
                        q['qNo'] = computed_qno 
                        
                        st.markdown(f"**Sub-Question {computed_qno}**")
                        c_no, c_txt, c_del = st.columns([1, 5, 1])
                        c_no.text_input("Q.No", value=computed_qno, disabled=True, key=f"qn_{q['id']}")
                        c_txt.text_area("Question Text (Ctrl+Enter to auto-tag)", q['text'], key=f"qt_{q['id']}", on_change=update_tags, args=(q['id'], i, j))
                        
                        # DELETE SUB-QUESTION BUTTON
                        c_del.button("❌", key=f"del_sq_{q['id']}", on_click=delete_sub_question, args=(i, j), help="Delete this sub-question")
                        
                        c_mk, c_co, c_lvl = st.columns([2, 2, 2])
                        q['marks'] = c_mk.number_input("Marks", value=float(q['marks']), step=1.0, key=f"mk_{q['id']}")
                        
                        if f"co_{q['id']}" not in st.session_state: st.session_state[f"co_{q['id']}"] = q.get('co', 'CO1')
                        q['co'] = c_co.selectbox("CO", ["CO1", "CO2", "CO3", "CO4", "CO5", "CO6"], key=f"co_{q['id']}")
                        
                        if f"lv_{q['id']}" not in st.session_state: st.session_state[f"lv_{q['id']}"] = q.get('level', 'L1')
                        q['level'] = c_lvl.selectbox("Bloom's", ["L1", "L2", "L3", "L4", "L5", "L6"], key=f"lv_{q['id']}")
                        st.divider()
                        
                    st.button("➕ Add Sub-Question", key=f"add_sub_{section['id']}", on_click=add_sub_question, args=(i,))

        st.button("➕ Add New Main Question", on_click=add_section, type="primary")

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
            
        st.header("👁️ Live Document Preview")
        html_content = generate_html()
        components.html(html_content, height=600, scrolling=True)
        st.download_button(label="📥 Download HTML Template", data=html_content, file_name=f"{st.session_state.exam_details['courseCode']}_QP.html", mime="text/html", type="primary")

# --- TAB 2: SETUP & DATABASE MANAGEMENT ---
with tab_setup:
    st.header("⚙️ System Database & Course Setup")
    st.write("Save your local configurations here. Data is written to the local SQLite database.")
    
    # 1. Course Details Setup
    with st.expander("📚 1. Course Profile Setup", expanded=True):
        st.info("Update the exam header details here.")
        with st.form("course_setup_form"):
            i_inst = st.text_input("Institution", st.session_state.exam_details['institution'])
            c1, c2 = st.columns(2)
            i_code = c1.text_input("Course Code", st.session_state.exam_details['courseCode'])
            i_name = c2.text_input("Course Name", st.session_state.exam_details['courseName'])
            i_marks = c1.number_input("Max Marks", value=int(st.session_state.exam_details['maxMarks']))
            i_dur = c2.text_input("Duration", st.session_state.exam_details['duration'])
            
            if st.form_submit_button("💾 Save Course Details to DB"):
                cursor.execute("DELETE FROM course_setup")
                cursor.execute("INSERT INTO course_setup (id, institution, course_code, course_name, max_marks, duration) VALUES (1, ?, ?, ?, ?, ?)", 
                               (i_inst, i_code, i_name, i_marks, i_dur))
                conn.commit()
                # Update Session State
                st.session_state.exam_details = {'institution': i_inst, 'courseCode': i_code, 'courseName': i_name, 'maxMarks': i_marks, 'duration': i_dur}
                st.success("Course details saved to DB!")
                st.rerun()

    # 2. Bloom's Dictionary Editor
    with st.expander("🧠 2. Bloom's Taxonomy Dictionary", expanded=False):
        st.write("Add missing action verbs (e.g., UK spellings like 'analyse') to force the system to recognize them.")
        with st.form("add_verb_form", clear_on_submit=True):
            vc1, vc2, vc3 = st.columns([2, 1, 1])
            new_verb = vc1.text_input("Action Verb (e.g. analyse)")
            new_level = vc2.selectbox("Bloom's Level", ["L1", "L2", "L3", "L4", "L5", "L6"])
            if vc3.form_submit_button("➕ Add to DB"):
                if new_verb:
                    cursor.execute("INSERT OR REPLACE INTO custom_blooms (verb, level) VALUES (?, ?)", (new_verb.lower().strip(), new_level))
                    conn.commit()
                    load_blooms_taxonomy.clear() # Clear cache to reload new DB values
                    st.success(f"Added '{new_verb}' as {new_level}")
        
        # Show Current Custom Verbs
        st.write("**Your Custom DB Verbs:**")
        custom_verbs_df = pd.read_sql_query("SELECT * FROM custom_blooms", conn)
        if not custom_verbs_df.empty:
            st.dataframe(custom_verbs_df, use_container_width=True)
        else:
            st.caption("No custom verbs added yet.")

    # 3. Keyword to CO Mapping Setup
    with st.expander("🔗 3. Smart Syllabus (Keyword to CO) Mapping", expanded=False):
        st.write("Map a syllabus phrase to specific COs based on the cognitive level. ")
        with st.form("add_mapping_form", clear_on_submit=True):
            new_phrase = st.text_input("Syllabus Phrase (e.g., 'number system', 'flip-flop')")
            st.write("Assign the CO if this phrase is tested at the following levels:")
            cc1, cc2, cc3, cc4, cc5, cc6 = st.columns(6)
            co_options = ["CO1", "CO2", "CO3", "CO4", "CO5", "CO6"]
            co_l1 = cc1.selectbox("If L1", co_options, key="cl1")
            co_l2 = cc2.selectbox("If L2", co_options, key="cl2")
            co_l3 = cc3.selectbox("If L3", co_options, key="cl3")
            co_l4 = cc4.selectbox("If L4", co_options, key="cl4")
            co_l5 = cc5.selectbox("If L5", co_options, key="cl5")
            co_l6 = cc6.selectbox("If L6", co_options, key="cl6")
            
            if st.form_submit_button("➕ Map Phrase to DB"):
                if new_phrase:
                    rules = json.dumps({"L1": co_l1, "L2": co_l2, "L3": co_l3, "L4": co_l4, "L5": co_l5, "L6": co_l6})
                    cursor.execute("INSERT OR REPLACE INTO co_mappings (keyword, rules) VALUES (?, ?)", (new_phrase.lower().strip(), rules))
                    conn.commit()
                    load_syllabus_mapping.clear() # Clear cache
                    st.success(f"Mapped '{new_phrase}' successfully!")
                    
        # Show Current Mappings
        st.write("**Your Custom DB Mappings:**")
        custom_mappings_df = pd.read_sql_query("SELECT * FROM co_mappings", conn)
        if not custom_mappings_df.empty:
            st.dataframe(custom_mappings_df, use_container_width=True)
        else:
            st.caption("No custom mappings added yet.")
