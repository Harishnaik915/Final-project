import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import seaborn as sns
import matplotlib.pyplot as plt
from streamlit_autorefresh import st_autorefresh
import re
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ------------------------- PAGE SETUP -------------------------
st.set_page_config(page_title="Employee Performance Dashboard", layout="wide")
st.title("📊 Employee Performance Dashboard")
st_autorefresh(interval=60000, key="datarefresh")

# ------------------------- STYLING -------------------------
st.markdown("""
    <style>
        .kpi-container {
            display: flex;
            flex-wrap: wrap;
            gap: 16px;
            justify-content: space-between;
            margin-top: 15px;
        }
        .kpi-box {
            flex: 1;
            min-width: 200px;
            max-width: 220px;
            background: linear-gradient(to bottom right, #e3f2fd, #bbdefb);
            padding: 20px;
            border-radius: 10px;
            box-shadow: 2px 2px 10px rgba(0,0,0,0.05);
            text-align: center;
        }
        .kpi-box:hover {
            box-shadow: 4px 4px 12px rgba(0,0,0,0.1);
        }
        .kpi-title {
            font-size: 18px;
            font-weight: 600;
            color: #0d47a1;
            margin-bottom: 6px;
        }
        .kpi-value {
            font-size: 28px;
            font-weight: 800;
            color: #1a237e;
        }
    </style>
""", unsafe_allow_html=True)

# ------------------------- DATA LOAD -------------------------
@st.cache_data
def load_data():
    sheet_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSMjf8xi7YMKMXn2JSHbGK_ojiZjbcpPVf_7yLuTnhI0mgiFS5WKLlvnP7VGLsUwIkTDJq9pPqZqXp0/pub?output=csv"
    df = pd.read_csv(sheet_url)
    df.dropna(inplace=True)
    return df

def map_work_mode(freq):
    if freq == 0:
        return "Office"
    elif freq in [25, 50]:
        return "Hybrid"
    elif freq in [75, 100]:
        return "Work From Home"
    else:
        return "Unknown"

df = load_data()
df['Hire_Date'] = pd.to_datetime(df['Hire_Date'])
df["Remote_Work_Frequency_Label"] = df["Remote_Work_Frequency"].apply(map_work_mode)

# ------------------------- SIDEBAR FILTERS -------------------------
st.sidebar.header("🎛️ Filter Options")
department_filter = st.sidebar.selectbox("Select Department", options=["All"] + sorted(df["Department"].unique().tolist()))
job_title_filter = st.sidebar.selectbox("Select Job Title", options=["All"] + sorted(df["Job_Title"].unique().tolist()))
gender_filter = st.sidebar.selectbox("Select Gender", options=["All"] + sorted(df["Gender"].unique().tolist()))
work_mode_filter = st.sidebar.selectbox("Select Remote Work Frequency", options=["All"] + sorted(df["Remote_Work_Frequency_Label"].unique().tolist()))

# ------------------------- DATA FILTERING -------------------------
df_filtered = df.copy()
if department_filter != "All":
    df_filtered = df_filtered[df_filtered["Department"] == department_filter]
if job_title_filter != "All":
    df_filtered = df_filtered[df_filtered["Job_Title"] == job_title_filter]
if gender_filter != "All":
    df_filtered = df_filtered[df_filtered["Gender"] == gender_filter]
if work_mode_filter != "All":
    df_filtered = df_filtered[df_filtered["Remote_Work_Frequency_Label"] == work_mode_filter]

# ------------------------- DATE FILTER -------------------------
st.markdown("### 🗕️ Filter by Hire Date Range")
start_date, end_date = st.date_input("Select Hire Date Range:", value=(df['Hire_Date'].min(), df['Hire_Date'].max()))
df_filtered = df_filtered[(df_filtered['Hire_Date'] >= pd.to_datetime(start_date)) & (df_filtered['Hire_Date'] <= pd.to_datetime(end_date))]
st.write(f"📋 Showing employees hired between **{start_date}** and **{end_date}**")

df_filtered["Attrition"] = np.random.choice(["Yes", "No"], size=len(df_filtered), p=[0.2, 0.8])

# ------------------------- KPI -------------------------
df_filtered["Workload_Index"] = df_filtered["Projects_Handled"] / df_filtered["Team_Size"]
df_filtered["Monthly_Salary"] = pd.to_numeric(df_filtered["Monthly_Salary"], errors="coerce")
df_filtered["Employee_Satisfaction_Score"] = pd.to_numeric(df_filtered["Employee_Satisfaction_Score"], errors="coerce")

avg_perf = round(df_filtered["Performance_Score"].mean(), 2)
avg_workload = round(df_filtered["Workload_Index"].mean(), 2)
avg_tenure = df_filtered["Years_At_Company"].mean()
avg_salary = df_filtered["Monthly_Salary"].mean()

st.markdown("### 🔑 Key Performance Indicators")
st.markdown(f"""
<div class="kpi-container">
    <div class="kpi-box">
        <div class="kpi-title">📊 Avg. Performance Score</div>
        <div class="kpi-value">{avg_perf}</div>
    </div>
    <div class="kpi-box">
        <div class="kpi-title">⚙️ Workload Index</div>
        <div class="kpi-value">{avg_workload}</div>
    </div>
    <div class="kpi-box">
        <div class="kpi-title">🗓️ Years at Company</div>
        <div class="kpi-value">{avg_tenure:.1f} years</div>
    </div>
    <div class="kpi-box">
        <div class="kpi-title">💰 Monthly Salary</div>
        <div class="kpi-value">${avg_salary:,.0f}</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ------------------------- UNIFIED CHATBOT -------------------------
def map_keyword_to_column(keyword):
    keyword_map = {
        'department': 'Department',
        'dept': 'Department',
        'departments': 'Department',
        'job title': 'Job_Title',
        'job titles': 'Job_Title',
        'jobtitle': 'Job_Title',
        'jobtitles': 'Job_Title',
        'gender': 'Gender',
        'work mode': 'Remote_Work_Frequency_Label',
        'salary': 'Monthly_Salary',
        'performance': 'Performance_Score',
        'satisfaction': 'Employee_Satisfaction_Score',
        'productivity': 'Productivity score',
        'workload': 'Workload_Index',
        'age': 'Age',
        'hire date': 'Hire_Date',
        'years at company': 'Years_At_Company',
        'projects handled': 'Projects_Handled',
        'team size': 'Team_Size',
        'attrition': 'Attrition',
        'male': 'Gender',
        'males': 'Gender',
        'female': 'Gender',
        'females': 'Gender',
        'other': 'Gender',
        'others': 'Gender',
        'department': 'Department',
        'departments': 'Department',
        'job title': 'Job_Title',
        'job titles': 'Job_Title',
        'gender': 'Gender',
        'genders': 'Gender',
        'work mode': 'Remote_Work_Frequency_Label',
        'work modes': 'Remote_Work_Frequency_Labe'
    }
    for key, value in keyword_map.items():
        if key in keyword.lower():
            return value
    return None
def parse_query(query):
    query = query.lower().strip()
    result = {
        'operation': 'filter',
        'conditions': [],
        'columns': None,
        'sort': None,
        'limit': None,
        'agg_func': None,
        'agg_column': None,
        'list_column': None,
        'group_by': None,
        'count_value': None,
        'sort_column': None
    }

    # List unique values
    list_patterns = [
        (r'(?:list|show|get|what are|all)\s+(?:all\s+|unique\s+|distinct\s+)?(departments?|job\s+titles?|work\s+modes?|genders?)', None)
    ]
    for pat, _ in list_patterns:
        match = re.search(pat, query)
        if match:
            col_keyword = match.group(1)
            col = map_keyword_to_column(col_keyword)
            if col:
                result['operation'] = 'list_unique'
                result['list_column'] = col
                return result
            
            

    # Specific count queries (e.g., count of males/females)
    count_value_patterns = [
        (r'count\s+of\s+(males?|females?|others?)', 'Gender'),
        (r'how\s+many\s+(males?|females?|others?)', 'Gender'),
        (r'number\s+of\s+(males?|females?|others?)', 'Gender')
    ]
    for pat, col in count_value_patterns:
        match = re.search(pat, query)
        if match:
            count_val = match.group(1).rstrip('s').title()
            if count_val in df[col].unique():
                result['operation'] = 'count_value'
                result['agg_column'] = col
                result['count_value'] = count_val
                return result

    # Grouped aggregation
    if any(re.search(fr"{word}\s+(by|per|.*wise)", query) for word in ['count', 'how many', 'number of']):
        result['operation'] = 'group_aggregate'
        result['agg_func'] = 'count'
        for col in ['Department', 'Gender', 'Job_Title', 'Remote_Work_Frequency_Label']:
            if col.lower() in query:
                result['group_by'] = col
                return result
        for keyword in ['department', 'gender', 'job title', 'work mode']:
            matched = map_keyword_to_column(keyword)
            if matched:
                result['group_by'] = matched
                return result

    # General aggregation
    if any(word in query for word in ['average', 'mean', 'count', 'sum', 'max', 'maximum', 'min', 'minimum', 'how many', 'number of']):
        result['operation'] = 'aggregate'
        if 'average' in query or 'mean' in query:
            result['agg_func'] = 'mean'
        elif 'count' in query or 'how many' in query or 'number of' in query:
            result['agg_func'] = 'count'
        elif 'sum' in query:
            result['agg_func'] = 'sum'
        elif 'max' in query or 'maximum' in query:
            result['agg_func'] = 'max'
        elif 'min' in query or 'minimum' in query:
            result['agg_func'] = 'min'

        agg_keywords = [
            ('salary', 'Monthly_Salary'),
            ('age', 'Age'),
            ('performance', 'Performance_Score'),
            ('satisfaction', 'Employee_Satisfaction_Score'),
            ('productivity', 'Productivity score'),
            ('workload', 'Workload_Index'),
            ('years at company', 'Years_At_Company'),
            ('projects handled', 'Projects_Handled'),
            ('team size', 'Team_Size'),
            ('retention risk', 'Retention_Risk')
        ]
        for keyword, col in agg_keywords:
            if keyword in query:
                result['agg_column'] = col
                return result
        for col in df.columns:
            if col.lower() in query:
                result['agg_column'] = col
                return result

    # Department-wise top N employees
    if any(phrase in query for phrase in ['each department', 'by department', 'department wise', 'per department', 'in each department']):
        result['operation'] = 'group_top'
        result['group_by'] = 'Department'
        limit_match = re.search(r'(top|highest)\s+(\d+)', query)
        result['limit'] = int(limit_match.group(2)) if limit_match else 5
        result['sort_column'] = 'Performance_Score'
        for col in ['Performance_Score', 'Monthly_Salary', 'Employee_Satisfaction_Score', 'Productivity score', 'Workload_Index']:
            if col.lower() in query:
                result['sort_column'] = col
                break
        result['sort'] = 'desc'
        return result

    # Filter conditions
    patterns = [
        (r'in\s+([\w\s&]+)\s*(department|dept)', 'Department', '=='),
        (r'gender\s+(\w+)', 'Gender', '=='),
        (r'job title\s+([\w\s]+)', 'Job_Title', '=='),
        (r'age\s*>\s*(\d+)', 'Age', '>'),
        (r'age\s*<\s*(\d+)', 'Age', '<'),
        (r'age\s+(\d+)', 'Age', '=='),
        (r'performance score\s*>\s*(\d+)', 'Performance_Score', '>'),
        (r'performance score\s*<\s*(\d+)', 'Performance_Score', '<'),
        (r'performance score\s+(\d+)', 'Performance_Score', '=='),
        (r'hired after\s+(\d{4})', 'Hire_Date', '>'),
        (r'hired before\s+(\d{4})', 'Hire_Date', '<'),
        (r'hired between\s+(\d{4}-\d{2}-\d{2})\s+and\s+(\d{4}-\d{2}-\d{2})', 'Hire_Date', 'between')
    ]
    for pat, col, op in patterns:
        match = re.search(pat, query)
        if match:
            if op == 'between':
                start_date = pd.to_datetime(match.group(1))
                end_date = pd.to_datetime(match.group(2))
                result['conditions'].append((col, 'between', (start_date, end_date)))
            else:
                val = match.group(1).strip().title() if op == '==' and col not in ['Age', 'Performance_Score', 'Hire_Date'] else pd.to_datetime(f"{match.group(1)}-01-01") if col == 'Hire_Date' else int(match.group(1))
                result['conditions'].append((col, op, val))

    # Sorting
    if 'top' in query or 'highest' in query:
        result['operation'] = 'sort'
        result['sort'] = 'desc'
        limit_match = re.search(r'(top|highest)\s+(\d+)', query)
        result['limit'] = int(limit_match.group(2)) if limit_match else 5
        for col in df.columns:
            if col.lower() in query:
                result['sort_column'] = col
                break
        if not result['sort_column']:
            for keyword in ['performance', 'salary', 'satisfaction', 'workload', 'productivity']:
                matched = map_keyword_to_column(keyword)
                if matched:
                    result['sort_column'] = matched
                    break
        return result

    elif 'bottom' in query or 'lowest' in query:
        result['operation'] = 'sort'
        result['sort'] = 'asc'
        limit_match = re.search(r'(bottom|lowest)\s+(\d+)', query)
        result['limit'] = int(limit_match.group(2)) if limit_match else 5
        for col in df.columns:
            if col.lower() in query:
                result['sort_column'] = col
                break
        if not result['sort_column']:
            for keyword in ['performance', 'salary', 'satisfaction', 'workload', 'productivity']:
                matched = map_keyword_to_column(keyword)
                if matched:
                    result['sort_column'] = matched
                    break
        return result

    # Ensure essential columns are always included
    default_cols = ['Employee_ID', 'Department', 'Age', 'Job_Title', 'Performance_Score', 'Monthly_Salary']
    result['columns'] = [col for col in df.columns if col.lower() in query] or default_cols

    return result


def process_query(df, query_info):
    filtered_df = df.copy()

    for col, op, val in query_info['conditions']:
        if op == '==':
            filtered_df = filtered_df[filtered_df[col] == val]
        elif op == '>':
            filtered_df = filtered_df[filtered_df[col] > val]
        elif op == '<':
            filtered_df = filtered_df[filtered_df[col] < val]
        elif op == 'between':
            start_date, end_date = val
            filtered_df = filtered_df[(filtered_df[col] >= start_date) & (filtered_df[col] <= end_date)]

    if query_info['operation'] == 'count_value':
        agg_col = query_info.get('agg_column')
        count_val = query_info.get('count_value')
        if agg_col and count_val:
            count = len(filtered_df[filtered_df[agg_col] == count_val])
            return pd.DataFrame({f"count({count_val})": [count]})
        return pd.DataFrame({"Error": ["No valid column or value for counting"]})

    if query_info['operation'] == 'aggregate':
        agg_col = query_info.get('agg_column')
        agg_func = query_info.get('agg_func')
        if agg_col and agg_func:
            if agg_func == 'count':
                result = len(filtered_df)
                return pd.DataFrame({f"count(employees)": [result]})
            filtered_df[agg_col] = pd.to_numeric(filtered_df[agg_col], errors='coerce')
            result = filtered_df[agg_col].agg(agg_func)
            return pd.DataFrame({f"{agg_func}({agg_col})": [result]})
        return pd.DataFrame({"Error": ["No valid column for aggregation"]})

    if query_info['operation'] == 'group_aggregate':
        group_col = query_info.get('group_by')
        agg_func = query_info.get('agg_func')
        if group_col and agg_func:
            result = filtered_df[group_col].value_counts().reset_index()
            result.columns = [group_col, 'Count']
            return result
        return pd.DataFrame({"Error": ["No valid column for grouping"]})

    if query_info['operation'] == 'list_unique':
        list_col = query_info.get('list_column')
        if list_col:
            values = filtered_df[list_col].dropna().astype(str).apply(lambda x: x.strip().title())
            values = sorted(set(values))
            return pd.DataFrame({list_col: values})
        return pd.DataFrame({"Error": ["No valid column for listing"]})

    if query_info['operation'] == 'group_top':
        group_col = query_info.get('group_by')
        sort_col = query_info.get('sort_column')
        limit = query_info.get('limit', 5)
        if group_col and sort_col:
            filtered_df[sort_col] = pd.to_numeric(filtered_df[sort_col], errors='coerce')
            result = filtered_df.groupby(group_col).apply(lambda x: x.nlargest(limit, sort_col, keep='all')).reset_index(drop=True)
            return result[query_info['columns'] or ['Employee_ID', 'Department', 'Job_Title', sort_col]]
        return pd.DataFrame({"Error": ["No valid column for grouping or sorting"]})

    if query_info['operation'] == 'sort' and query_info.get('sort_column'):
        filtered_df[query_info['sort_column']] = pd.to_numeric(filtered_df[query_info['sort_column']], errors='coerce')
        filtered_df = filtered_df.sort_values(by=query_info['sort_column'], ascending=(query_info['sort'] == 'asc'))
        if query_info['limit']:
            filtered_df = filtered_df.head(query_info['limit'])
        return filtered_df[query_info['columns']].reset_index(drop=True)

    if query_info['operation'] == 'filter':
        if query_info['columns']:
            filtered_df = filtered_df[query_info['columns']]
        return filtered_df.reset_index(drop=True) if not filtered_df.empty else pd.DataFrame({"Message": ["No results found."]})

    return pd.DataFrame({"Error": ["Unable to understand your query. Try again."]})


# ------------------------- CHARTS & VISUAL INSIGHTS -------------------------
st.markdown("### 📈 Visual Insights")
tab1, tab2, tab3 = st.tabs(["📊 Charts", "📋 Table", "📎 Correlations"])

with tab1:
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(px.bar(
            df_filtered.groupby("Department")["Performance_Score"].mean().reset_index(),
            x="Department", y="Performance_Score", color="Department",
            title="Avg. Performance by Department"
        ), use_container_width=True)

    with col2:
        st.plotly_chart(px.pie(
            df_filtered, names="Remote_Work_Frequency_Label",
            title="Work Mode Distribution"
        ), use_container_width=True)

    col3, col4 = st.columns(2)
    with col3:
        st.plotly_chart(px.box(
            df_filtered, x="Gender", y="Performance_Score", color="Gender",
            title="Performance by Gender"
        ), use_container_width=True)

    with col4:
        st.plotly_chart(px.line(
            df_filtered.groupby("Years_At_Company")["Performance_Score"].mean().reset_index(),
            x="Years_At_Company", y="Performance_Score",
            title="Performance Score by Tenure"
        ), use_container_width=True)

    col5, col6 = st.columns(2)
    with col5:
        satisfaction_data = df_filtered.groupby("Job_Title")["Employee_Satisfaction_Score"].mean().reset_index()
        st.plotly_chart(px.treemap(
            satisfaction_data, path=["Job_Title"], values="Employee_Satisfaction_Score",
            color="Employee_Satisfaction_Score", color_continuous_scale="Blues",
            title="Average Satisfaction Score by Job Title"
        ), use_container_width=True)

    with col6:
        prod_job = df_filtered.groupby("Job_Title")["Productivity score"].mean().reset_index()
        st.plotly_chart(px.scatter(
            prod_job, x="Job_Title", y="Productivity score", size="Productivity score",
            color="Productivity score", color_continuous_scale="Viridis",
            title="Productivity Score by Job Title (Bubble Chart)"
        ).update_layout(xaxis_tickangle=-45), use_container_width=True)

    st.plotly_chart(px.bar(
        df_filtered.groupby("Remote_Work_Frequency_Label")["Attrition"]
        .apply(lambda x: (x == "Yes").mean())
        .reset_index(name="Retention_Risk")
        .sort_values("Retention_Risk", ascending=False),
        x="Remote_Work_Frequency_Label", y="Retention_Risk",
        color="Retention_Risk", color_continuous_scale="Oranges",
        title="Retention Risk by Remote Work Frequency"
    ), use_container_width=True)

    # Alerts Section
    if st.sidebar.checkbox("⚠ Show Performance Alerts", value=True):
        st.subheader("🚨 Alerts")
        dept_avg_perf = df_filtered.groupby("Department")["Performance_Score"].mean().reset_index()
        low_perf_depts = dept_avg_perf[dept_avg_perf["Performance_Score"] <= 2]

        if not low_perf_depts.empty:
            for _, row in low_perf_depts.iterrows():
                st.error(f"⚠ Department {row['Department']} has low average Performance Score: {row['Performance_Score']:.2f}")

        low_perf_emps = df_filtered[df_filtered["Performance_Score"] <= 2]
        if not low_perf_emps.empty:
            st.warning(f"⚠ {len(low_perf_emps)} employee(s) have Performance Score ≤ 2")
            with st.expander("View Low Performing Employees"):
                st.dataframe(low_perf_emps[["Employee_ID", "Department", "Job_Title", "Performance_Score"]])

with tab2:
    st.dataframe(df_filtered.sort_values(by="Performance_Score", ascending=False).head(10)[
        ["Employee_ID", "Department", "Job_Title", "Monthly_Salary", "Performance_Score"]
    ])

# ------------------------- EMAIL ALERT -------------------------
st.markdown("### 📤 Send Email Alert to Admin")
sender_email = "tejaerugurala5@gmail.com"
receiver_email = "tejaerugurala5@gmail.com"
sender_password = "hceegfzdebslbdqp"  # App password, keep safe

if st.button("📧 Email Low Performers List to Admin"):
    low_perf_emps = df_filtered[df_filtered["Performance_Score"] <= 2]
    if not low_perf_emps.empty:
        subject = "⚠ Low Performing Employees Alert"
        table_html = low_perf_emps[["Employee_ID", "Department", "Job_Title", "Performance_Score"]].to_html(index=False)
        body = f"""
        <html>
        <body>
            <p>Dear Admin,</p>
            <p>The following employees have a Performance Score of 2 or less:</p>
            {table_html}
            <p>Regards,<br>Performance Monitoring System</p>
        </body>
        </html>
        """

        msg = MIMEMultipart("alternative")
        msg['Subject'] = subject
        msg['From'] = sender_email
        msg['To'] = receiver_email
        msg.attach(MIMEText(body, "html"))

        try:
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(sender_email, sender_password)
                server.send_message(msg)
            st.success("✅ Email sent successfully to Admin.")
        except Exception as e:
            st.error(f"❌ Failed to send email: {e}")
    else:
        st.info("No employees found with Performance Score ≤ 2.")

# ------------------------- CHATBOT SECTION -------------------------
# # ------------------------- CHATBOT SECTION -------------------------
st.markdown("### 💬 Ask the Employee Chatbot")
chat_input = st.text_input("Type your question (e.g., 'List departments', 'List job titles', 'Count of males', 'Average salary', etc.')")

if chat_input:
    query_lower = chat_input.lower()

    # Handle unique departments
    if "unique department" in query_lower or "list departments" in query_lower or "show departments" in query_lower:
        unique_departments = (
            df_filtered["Department"]
            .dropna()
            .astype(str)
            .apply(lambda x: x.strip().title())
            .unique()
        )
        st.success("Here are the unique departments:")
        st.dataframe(pd.DataFrame({"Departments": sorted(unique_departments)}))

        # Handle unique job titles with counts
    elif "unique job" in query_lower or "list job titles" in query_lower or "show job titles" in query_lower:
        job_counts = (
            df_filtered["Job_Title"]
            .dropna()
            .astype(str)
            .apply(lambda x: x.strip().title())
            .value_counts()
            .sort_index()
        )
        job_titles_with_counts = [f"{job} ({count})" for job, count in job_counts.items()]
        st.success("Here are the unique job titles with their counts:")
        st.dataframe(pd.DataFrame({"Job Titles": job_titles_with_counts}))



    # Handle general chatbot query
    else:
        try:
            query_info = parse_query(chat_input)
            chatbot_result = process_query(df_filtered, query_info)

            if chatbot_result.empty or 'Error' in chatbot_result.columns or 'Message' in chatbot_result.columns:
                st.warning("No results found or invalid question. Try something like 'List departments', 'List job titles', 'Count of males', or 'Average salary'.")
            else:
                st.success("Here's what I found:")
                st.dataframe(chatbot_result)

        except Exception as e:
            st.error(f"Error processing question: {e}")
