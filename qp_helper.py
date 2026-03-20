import streamlit as st
import pandas as pd
import datetime
import re
import io
import json
import streamlit.components.v1 as components

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="AMC Exam Portal Pro", layout="wide", page_icon="🎓")

# --- 2. UNIVERSAL BLOOM'S TAXONOMY (HARDCODED) ---
@st.cache_data
def load_blooms_taxonomy():
    blooms_data = {
        "L1": ["arrange", "cite", "define", "describe", "duplicate", "enumerate", "identify", "label", "list", "match", "memorize", "name", "order", "outline", "recall", "recognize", "record", "relate", "repeat", "reproduce", "select", "state", "tabulate", "tell"],
        "L2": ["approximate", "articulate", "categorize", "characterize", "clarify", "classify", "compare", "comprehend", "conclude", "contrast", "convert", "defend", "demonstrate", "discuss", "distinguish", "estimate", "explain", "express", "extend", "generalize", "illustrate", "indicate", "infer", "interpret", "locate", "paraphrase", "predict", "rephrase", "report", "restate", "review", "rewrite", "show", "summarize", "translate"],
        "L3": ["adapt", "allocate", "apply", "build", "calculate", "change", "choose", "compute", "conduct", "construct", "determine", "develop", "discover", "employ", "execute", "experiment", "function", "implement", "interview", "manipulate", "model", "modify", "operate", "practice", "produce", "schedule", "sketch", "solve", "use"],
        "L4": ["analyze", "analyse", "appraise", "breakdown", "categorize", "classify", "compare", "conclude", "contrast", "criticize", "deduce", "derive", "differentiate", "discriminate", "distinguish", "examine", "experiment", "infer", "inspect", "inventory", "investigate", "model", "organize", "outline", "prioritize", "question", "relate", "separate", "simplify", "subdivide", "survey", "test"],
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

# --- 3. DYNAMIC EXCEL TEMPLATE GENERATOR ---
def generate_excel_template():
    output = io.BytesIO()
    df_course = pd.DataFrame({
        'Institution': ['AMC Engineering College'], 'CourseCode': ['Enter Code Here'], 
        'CourseName': ['Enter Subject Name Here'], 'MaxMarks': [50], 'Duration': ['3 Hours']
    })
    # Notice: Bloom's is gone. Only Course Details and Syllabus Mapping are here!
    df_syllabus = pd.DataFrame({
        'Keyword': ['example_topic_1', 'example_topic_2'], 
        'L1': ['CO1', 'CO2'], 'L2': ['CO1', 'CO2'], 'L3': ['CO3', 'CO4'], 
        'L4': ['CO3', 'CO4'], 'L5': ['CO3', 'CO4'], 'L6': ['CO3', 'CO4']
    })
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_course.to_excel(writer, sheet_name='CourseSetup', index=False)
        df_syllabus.to_excel(writer, sheet_name='SyllabusMapping', index=False)
    return output.getvalue()

# --- 4. STATE MANAGEMENT & DATA LOADERS ---
if 'exam_details' not in st.session_state:
    st.session_state.exam_details = {
        'institution': 'AMC Engineering College', 'courseCode': 'SUBJECT_CODE', 
        'courseName': 'SUBJECT_NAME', 'maxMarks': 50, 'duration': '3 Hours'
    }

if 'syllabus_mapping' not in st.session_state:
    st.session_state.syllabus_mapping = {}

if 'sections' not in st.session_state:
    st.session_state.sections = [
        {'id': 100, 'module': 'Module 1', 'isNote': False, 'questions': [
            {'id': 101, 'qNo': '', 'text': '', 'marks': 5, 'co': 'CO1', 'level': 'L1'}
        ]}
    ]

def load_excel_database(uploaded_file):
    try:
        new_syllabus = {}
        df_course = pd.read_excel(uploaded_file, sheet_name='CourseSetup').dropna(how="all")
        if not df_course.empty:
            st.session_state.exam_details = {
                'institution': str(df_course['Institution'].iloc[0]), 'courseCode': str(df_course['CourseCode'].iloc[0]),
                'courseName': str(df_course['CourseName'].iloc[0]), 'maxMarks': int(df_course['MaxMarks'].iloc[0]),
                'duration': str(df_course['Duration'].iloc[0])
            }
            
        df_syl = pd.read_excel(uploaded_file, sheet_name='SyllabusMapping').dropna(how="all")
        for index, row in df_syl.iterrows():
            if pd.notna(row['Keyword']):
                kw = str(row['Keyword']).lower().strip()
                new_syllabus[kw] = {
                    "L1": str(row.get('L1', 'CO1')).strip(), "L2": str(row.get('L2', 'CO1')).strip(),
                    "L3": str(row.get('L3', 'CO1')).strip(), "L4": str(row.get('L4', 'CO1')).strip(),
                    "L5": str(row.get('L5', 'CO1')).strip(), "L6": str(row.get('L6', 'CO1')).strip()
                }
        st.session_state.syllabus_mapping = new_syllabus
        return True
    except Exception as e:
        st.error(f"Error reading Excel file. Ensure you are using the official template. Error: {e}")
        return False

# --- 5. AUTO TAGGING ENGINE ---
def auto_tag_question(text):
    if not text: return "L1", "CO1"
    suggested_lvl, suggested_co = "L1", "CO1"
    text_lower = text.lower()
    
    # Check universal Bloom's Dictionary
    words = re.findall(r'\b[a-zA-Z-]+\b', text_lower)
    for word in words[:7]: 
        if word in blooms_dict:
            suggested_lvl = blooms_dict[word]
            break
            
    # Check Subject-Specific Syllabus mapping
    for keyword, level_rules in st.session_state.syllabus_mapping.items():
        if re.search(r'\b' + re.escape(keyword) + r'\b', text_lower):
            suggested_co = level_rules.get(suggested_lvl, "CO1")
            break 
            
    return suggested_lvl, suggested_co

# --- 6. HTML GENERATOR ---
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

# --- 7. HELPER FUNCTIONS ---
def add_section():
    new_id = int(datetime.datetime.now().timestamp() * 1000)
    current_modules = len(st.session_state.sections)
    next_mod_num = current_modules + 1 if current_modules < 5 else 5
    st.session_state.sections.append({'id': new_id, 'module': f'Module {next_mod_num}', 'isNote': False, 'questions': [{'id': new_id + 1, 'qNo': '', 'text': '', 'marks': 0, 'co': 'CO1', 'level': 'L1'}]})

def add_sub_question(sec_idx):
    new_id = int(datetime.datetime.now().timestamp() * 1000)
    st.session_state.sections[sec_idx]['questions'].append({'id': new_id, 'qNo': '', 'text': '', 'marks': 0, 'co': 'CO1', 'level': 'L1'})

def delete_section(sec_idx): st.session_state.sections.pop(sec_idx)
def delete_sub_question(sec_idx, q_idx): st.session_state.sections[sec_idx]['questions'].pop(q_idx)

def update_tags(q_id, sec_idx, q_idx):
    typed_text = st.session_state[f"qt_{q_id}"]
    new_level, new_co = auto_tag_question(typed_text)
    st.session_state[f"lv_{q_id}"] = new_level
    st.session_state[f"co_{q_id}"] = new_co
    st.session_state.sections[sec_idx]['questions'][q_idx]['text'] = typed_text
    st.session_state.sections[sec_idx]['questions'][q_idx]['level'] = new_level
    st.session_state.sections[sec_idx]['questions'][q_idx]['co'] = new_co

def export_draft_json():
    draft_data = {
        'exam_details': st.session_state.exam_details, 
        'sections': st.session_state.sections,
        'syllabus_mapping': st.session_state.syllabus_mapping # Save the brain with the draft!
    }
    return json.dumps(draft_data, indent=4)

def load_draft_json(uploaded_draft):
    try:
        draft_data = json.load(uploaded_draft)
        st.session_state.exam_details = draft_data['exam_details']
        st.session_state.sections = draft_data['sections']
        if 'syllabus_mapping' in draft_data:
            st.session_state.syllabus_mapping = draft_data['syllabus_mapping']
        return True
    except Exception as e:
        st.error("Invalid draft file.")
        return False

# --- 8. UI LAYOUT ---
st.title("🎓 AMC Exam Portal Pro")

tab_editor, tab_setup = st.tabs(["📝 Exam Paper Editor", "⚙️ Subject Configuration (Excel)"])

with tab_setup:
    st.header("⚙️ Configure Subject Specifics")
    st.write("Since Bloom's Taxonomy is universally programmed into this app, you only need to upload the Course Details and Syllabus CO mappings for the specific subject you are teaching.")
    col_dl, col_ul = st.columns(2)
    with col_dl:
        st.subheader("Step 1: Download Subject Template")
        excel_data = generate_excel_template()
        st.download_button(label="📥 Download Excel Template", data=excel_data, file_name="Subject_Syllabus_Template.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", type="primary")
    with col_ul:
        st.subheader("Step 2: Upload Subject Rules")
        uploaded_file = st.file_uploader("Upload Configured Excel", type=['xlsx'])
        if uploaded_file is not None:
            if load_excel_database(uploaded_file):
                st.success("✅ Subject Database Loaded Successfully!")
    st.divider()
    if len(st.session_state.syllabus_mapping) > 0:
        st.success(f"🧠 Currently running with {len(st.session_state.syllabus_mapping)} Subject-Specific Mapping Rules.")
    else:
        st.warning("⚠️ No Subject Mappings loaded. The app will only predict Bloom's Taxonomy, not COs.")

with tab_editor:
    # --- SAVE / RESUME PROGRESS BAR ---
    with st.expander("💾 Save or Resume a Draft", expanded=False):
        c_save, c_load = st.columns(2)
        with c_save:
            st.download_button(label="📥 Download Current Draft (.json)", data=export_draft_json(), file_name=f"Draft_{st.session_state.exam_details['courseCode']}_Exam.json", mime="application/json", type="primary")
        with c_load:
            draft_upload = st.file_uploader("📂 Upload Previous Draft (.json)", type=['json'], key="draft_up")
            if draft_upload is not None:
                if st.button("🔄 Resume Draft", type="primary"):
                    if load_draft_json(draft_upload):
                        st.success("Draft Loaded Successfully!")
                        st.rerun()

    st.divider()

    # --- EDITOR UI ---
    col_edit, col_view = st.columns([1.2, 1], gap="large")

    with col_edit:
        for i, section in enumerate(st.session_state.sections):
            with st.container(border=True):
                mod_col, del_blk_col = st.columns([4, 1])
                mod_options = ["Module 1", "Module 2", "Module 3", "Module 4", "Module 5"]
                current_mod = section.get('module', 'Module 1')
                mod_idx = mod_options.index(current_mod) if current_mod in mod_options else 0
                
                section['module'] = mod_col.selectbox(f"Main Question {i+1} Assignment", mod_options, index=mod_idx, key=f"mod_sel_{section['id']}")
                del_blk_col.button("🗑️ Delete Block", key=f"del_blk_{section['id']}", on_click=delete_section, args=(i,), type="secondary")
                
                if not section.get('isNote'):
                    for j, q in enumerate(section['questions']):
                        computed_qno = f"{i+1}.{chr(97+j)}"
                        q['qNo'] = computed_qno 
                        
                        st.markdown(f"**Sub-Question {computed_qno}**")
                        c_no, c_txt, c_del = st.columns([1, 5, 1])
                        c_no.text_input("Q.No", value=computed_qno, disabled=True, key=f"qn_{q['id']}")
                        c_txt.text_area("Question Text (Ctrl+Enter to auto-tag)", q['text'], key=f"qt_{q['id']}", on_change=update_tags, args=(q['id'], i, j))
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
        st.download_button(label="📥 Finalize & Download HTML QP", data=html_content, file_name=f"{st.session_state.exam_details['courseCode']}_QP.html", mime="text/html", type="primary")
