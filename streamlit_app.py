import streamlit as st
import pandas as pd
import re
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import gspread
from google.oauth2.service_account import Credentials


# ============================================================
# FINORA CONFIG
# ============================================================

st.set_page_config(
    page_title="FINORA | Your Finance AI",
    page_icon="💠",
    layout="wide",
    initial_sidebar_state="expanded",
)

ACTIVITY_SHEET = "Activity"
MASTER_SHEET = "Outlet Master"

ACTIVITY_HEADERS = [
    "Date",
    "Outlet",
    "Therapist",
    "Shift Timings",
    "Guests Interacted",
    "Conversions",
    "Appointment Value",
    "Saved At",
]


# ============================================================
# DESIGN
# ============================================================

st.markdown("""
<style>

/* ---------- GLOBAL ---------- */

html, body, [class*="css"] {
    font-family: "Segoe UI", Arial, sans-serif;
}

.stApp {
    background: #f6f8fc;
}

.block-container {
    max-width: 1500px;
    padding-top: 1.4rem;
    padding-left: 2.2rem;
    padding-right: 2.2rem;
    padding-bottom: 3rem;
}

#MainMenu {
    visibility: hidden;
}

footer {
    visibility: hidden;
}


/* ---------- SIDEBAR ---------- */

section[data-testid="stSidebar"] {
    background:
        linear-gradient(
            180deg,
            #071d38 0%,
            #0a2c4e 100%
        );

    border-right: 1px solid #163a5c;
}

section[data-testid="stSidebar"] > div {
    padding-top: 1.1rem;
}

.sidebar-brand {
    padding: 10px 8px 24px 8px;
}

.brand-row {
    display: flex;
    align-items: center;
    gap: 13px;
}

.brand-icon {
    width: 52px;
    height: 52px;
    border-radius: 15px;

    display: flex;
    align-items: center;
    justify-content: center;

    color: white;
    font-size: 29px;
    font-weight: 850;

    background:
        linear-gradient(
            135deg,
            #2dd6a6,
            #17a8c0
        );

    box-shadow:
        0 9px 22px
        rgba(0,0,0,.18);
}

.brand-name {
    color: white;
    font-size: 28px;
    font-weight: 850;
    letter-spacing: .8px;
    line-height: 1;
}

.brand-tagline {
    color: #9db4ca;
    font-size: 14px;
    margin-top: 6px;
}

.sidebar-label {
    color: #6f91af;
    font-size: 11px;
    font-weight: 800;
    letter-spacing: 1.5px;

    margin:
        8px 4px 8px 4px;
}


/* REAL STREAMLIT SIDEBAR BUTTONS */

section[data-testid="stSidebar"] div.stButton > button {

    width: 100%;
    min-height: 48px;

    justify-content: flex-start;

    text-align: left;

    padding:
        0 14px;

    margin-bottom:
        4px;

    border:
        1px solid transparent;

    border-radius:
        11px;

    background:
        transparent;

    color:
        #d7e5f1;

    font-size:
        15px !important;

    font-weight:
        650;

    box-shadow:
        none;
}

section[data-testid="stSidebar"] div.stButton > button:hover {

    background:
        rgba(255,255,255,.07);

    border-color:
        rgba(255,255,255,.06);

    color:
        white;
}

.sidebar-online {

    margin-top:
        26px;

    padding:
        14px 15px;

    border-radius:
        13px;

    background:
        rgba(255,255,255,.06);

    border:
        1px solid rgba(255,255,255,.08);

    color:
        #dce9f4;

    font-size:
        14px;
}

.online-dot {

    display:
        inline-block;

    width:
        9px;

    height:
        9px;

    border-radius:
        50%;

    margin-right:
        8px;

    background:
        #2cda9d;

    box-shadow:
        0 0 8px
        rgba(44,218,157,.8);
}


/* ---------- TOP BRAND ---------- */

.top-brand {

    display:
        flex;

    align-items:
        center;

    gap:
        14px;

    margin-bottom:
        18px;
}

.top-icon {

    width:
        55px;

    height:
        55px;

    display:
        flex;

    align-items:
        center;

    justify-content:
        center;

    border-radius:
        16px;

    color:
        white;

    font-size:
        29px;

    font-weight:
        850;

    background:
        linear-gradient(
            135deg,
            #29d4a4,
            #18a6c1
        );

    box-shadow:
        0 8px 20px
        rgba(22,167,185,.18);
}

.top-name {

    color:
        #082d5c;

    font-size:
        32px;

    font-weight:
        850;

    line-height:
        1;
}

.top-sub {

    color:
        #71849a;

    font-size:
        15px;

    margin-top:
        6px;
}


/* ---------- PROJECT HEADER ---------- */

.project-header {

    padding:
        24px 27px;

    margin-bottom:
        19px;

    border-radius:
        19px;

    color:
        white;

    background:
        linear-gradient(
            120deg,
            #092844 0%,
            #0e6073 55%,
            #159989 100%
        );

    box-shadow:
        0 10px 25px
        rgba(8,45,72,.12);
}

.project-small {

    color:
        #83ebd3;

    font-size:
        12px;

    font-weight:
        800;

    letter-spacing:
        1.3px;

    text-transform:
        uppercase;
}

.project-title {

    color:
        white;

    font-size:
        30px;

    font-weight:
        850;

    margin-top:
        5px;
}

.project-description {

    color:
        #d9eff1;

    font-size:
        16px;

    margin-top:
        5px;
}


/* ---------- BODY ---------- */

.page-title {

    color:
        #102a43;

    font-size:
        27px;

    font-weight:
        850;

    margin-top:
        16px;
}

.page-description {

    color:
        #718096;

    font-size:
        16px;

    margin:
        3px 0 18px 0;
}

.stApp p {
    font-size: 16px;
}

div[data-testid="stWidgetLabel"] p {

    color:
        #334e68 !important;

    font-size:
        15px !important;

    font-weight:
        700 !important;
}


/* ---------- TABS ---------- */

div[data-baseweb="tab-list"] {

    gap:
        6px;

    padding:
        6px;

    background:
        white;

    border:
        1px solid #e0e7ef;

    border-radius:
        13px;

    box-shadow:
        0 4px 14px
        rgba(16,42,67,.04);
}

button[data-baseweb="tab"] {

    height:
        49px;

    padding-left:
        20px !important;

    padding-right:
        20px !important;

    border-radius:
        9px !important;

    color:
        #52677c !important;

    font-size:
        15px !important;

    font-weight:
        700 !important;
}

button[data-baseweb="tab"][aria-selected="true"] {

    color:
        #4f5cf1 !important;

    background:
        linear-gradient(
            135deg,
            #eef0ff,
            #ecf8ff
        ) !important;
}


/* ---------- INPUTS ---------- */

textarea {

    min-height:
        225px !important;

    font-size:
        16px !important;

    line-height:
        1.6 !important;

    background:
        white !important;

    border-radius:
        12px !important;
}

input {
    font-size: 16px !important;
}

div[data-testid="stFileUploader"] section {

    padding:
        16px;

    border-radius:
        12px;

    background:
        linear-gradient(
            135deg,
            #f1f9ff,
            #effbf7
        );

    border:
        1px dashed #91b9c5;
}


/* ---------- MAIN BUTTON ---------- */

div.stButton > button[kind="primary"] {

    min-height:
        54px;

    border:
        none;

    border-radius:
        11px;

    color:
        white;

    font-size:
        16px !important;

    font-weight:
        800 !important;

    background:
        linear-gradient(
            90deg,
            #5d5cf6,
            #4e7bea,
            #16aa96
        );

    box-shadow:
        0 8px 18px
        rgba(78,91,220,.17);
}


/* ---------- METRICS ---------- */

div[data-testid="stMetric"] {

    min-height:
        108px;

    padding:
        15px;

    border-radius:
        15px;

    background:
        white;

    border:
        1px solid #e0e7ef;

    box-shadow:
        0 5px 16px
        rgba(16,42,67,.05);
}

div[data-testid="stMetricLabel"] p {

    color:
        #66788b !important;

    font-size:
        13px !important;

    font-weight:
        750 !important;
}

div[data-testid="stMetricValue"] {

    color:
        #102a43 !important;

    font-size:
        27px !important;

    font-weight:
        850 !important;
}


/* ---------- CARDS ---------- */

.card {

    padding:
        19px;

    margin-bottom:
        14px;

    border-radius:
        16px;

    background:
        white;

    border:
        1px solid #e0e7ef;

    box-shadow:
        0 5px 16px
        rgba(16,42,67,.05);
}

.card-title {

    color:
        #173b5e;

    font-size:
        18px;

    font-weight:
        800;

    margin-bottom:
        12px;
}


/* ---------- PILLS ---------- */

.pill {

    display:
        inline-block;

    margin:
        4px;

    padding:
        7px 11px;

    border-radius:
        20px;

    font-size:
        13px;

    font-weight:
        700;
}

.pending {

    color:
        #aa3c3c;

    background:
        #fff0ee;

    border:
        1px solid #ffc9c3;
}

.received {

    color:
        #087052;

    background:
        #e5f9f1;

    border:
        1px solid #bce8d7;
}


/* ---------- MODULE PLACEHOLDER ---------- */

.module-box {

    max-width:
        850px;

    padding:
        35px;

    margin-top:
        25px;

    border-radius:
        20px;

    text-align:
        center;

    background:
        white;

    border:
        1px solid #e1e8ef;

    box-shadow:
        0 8px 25px
        rgba(16,42,67,.06);
}

.module-icon {

    font-size:
        45px;
}

.module-name {

    color:
        #102a43;

    font-size:
        27px;

    font-weight:
        850;

    margin-top:
        8px;
}

.module-text {

    color:
        #718096;

    font-size:
        16px;

    margin-top:
        7px;
}


/* ---------- DATAFRAME ---------- */

div[data-testid="stDataFrame"] {

    border:
        1px solid #e0e7ef;

    border-radius:
        13px;

    overflow:
        hidden;
}


/* ---------- MOBILE ---------- */

@media (max-width: 900px) {

    .block-container {

        padding-left:
            14px;

        padding-right:
            14px;
    }

}

</style>
""", unsafe_allow_html=True)


# ============================================================
# SESSION STATE / PROJECT NAVIGATION
# ============================================================

if "project" not in st.session_state:
    st.session_state.project = "Home"


def open_project(name):
    st.session_state.project = name


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown(
        """
        <div class="sidebar-brand">
            <div class="brand-row">
                <div class="brand-icon">F</div>
                <div>
                    <div class="brand-name">FINORA</div>
                    <div class="brand-tagline">Your Finance AI</div>
                </div>
            </div>
        </div>

        <div class="sidebar-label">
            WORKSPACE
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button(
        "🏠  Home",
        use_container_width=True,
    ):
        open_project("Home")
        st.rerun()

    if st.button(
        "📊  Lobby Activity",
        use_container_width=True,
    ):
        open_project("Lobby Activity")
        st.rerun()

    if st.button(
        "🧾  GST Returns",
        use_container_width=True,
    ):
        open_project("GST Returns")
        st.rerun()

    if st.button(
        "📈  Zenoti Reports",
        use_container_width=True,
    ):
        open_project("Zenoti Reports")
        st.rerun()

    if st.button(
        "💰  Cash Reconciliation",
        use_container_width=True,
    ):
        open_project("Cash Reconciliation")
        st.rerun()

    if st.button(
        "📁  Files",
        use_container_width=True,
    ):
        open_project("Files")
        st.rerun()

    if st.button(
        "⚙️  Settings",
        use_container_width=True,
    ):
        open_project("Settings")
        st.rerun()

    st.markdown(
        """
        <div class="sidebar-online">
            <span class="online-dot"></span>
            FINORA Online
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# TOP BRAND
# ============================================================

st.markdown(
    """
    <div class="top-brand">
        <div class="top-icon">F</div>
        <div>
            <div class="top-name">Finora</div>
            <div class="top-sub">Your Finance AI</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# GOOGLE SHEETS
# ============================================================

@st.cache_resource
def connect_to_sheet():

    service_account_info = dict(
        st.secrets["google_service_account"]
    )

    credentials = Credentials.from_service_account_info(
        service_account_info,
        scopes=[
            "https://www.googleapis.com/auth/spreadsheets"
        ],
    )

    client = gspread.authorize(
        credentials
    )

    spreadsheet = client.open_by_key(
        st.secrets["spreadsheet_id"]
    )

    return spreadsheet


def activity_ws():
    return connect_to_sheet().worksheet(
        ACTIVITY_SHEET
    )


def master_ws():
    return connect_to_sheet().worksheet(
        MASTER_SHEET
    )


# ============================================================
# HELPERS
# ============================================================

def number(value):

    if value is None:
        return 0

    text = (
        str(value)
        .replace(",", "")
        .replace("₹", "")
        .strip()
    )

    match = re.search(
        r"-?\d+(?:\.\d+)?",
        text,
    )

    if not match:
        return 0

    result = float(match.group())

    if result.is_integer():
        return int(result)

    return result


def rupees(value):

    try:
        return f"₹{float(value):,.0f}"

    except Exception:
        return "₹0"


def normalize_date(value):

    value = str(value).strip()

    if not value:
        return ""

    formats = [
        "%Y-%m-%d",
        "%d/%m/%Y",
        "%d-%m-%Y",
        "%m/%d/%Y",
        "%Y/%m/%d",
        "%d %b %Y",
        "%d %B %Y",
    ]

    for fmt in formats:

        try:
            return datetime.strptime(
                value,
                fmt,
            ).date().isoformat()

        except ValueError:
            pass

    try:

        return pd.to_datetime(
            value,
            dayfirst=True,
        ).date().isoformat()

    except Exception:

        return value


def current_time():

    return datetime.now(
        ZoneInfo("Asia/Kolkata")
    ).strftime(
        "%Y-%m-%d %H:%M:%S"
    )


# ============================================================
# OUTLET MASTER
# ============================================================

def get_outlets():

    values = master_ws().get("A:C")

    outlets = {}

    if len(values) < 2:
        return outlets

    for row in values[1:]:

        row = row + [""] * (3 - len(row))

        code = str(row[0]).strip().upper()
        name = str(row[1]).strip()
        active = str(row[2]).strip().lower()

        if (
            code
            and name
            and active
            in {
                "yes",
                "y",
                "true",
                "1",
                "active",
            }
        ):
            outlets[code] = name

    return outlets


# ============================================================
# FLEXIBLE WHATSAPP PARSER
# ============================================================

def clean_line(line):

    # Removes:
    # 1.
    # 2)
    # -
    # *
    # bullets
    return re.sub(
        r"^\s*(?:\d+\s*[\.\)]\s*|[-•*]\s*)",
        "",
        line,
    ).strip()


def get_message_value(
    text,
    labels,
):

    lines = text.splitlines()

    for raw_line in lines:

        line = clean_line(raw_line)

        for label in labels:

            # Supports:
            # Therapist: Gayatri
            # Therapist - Gayatri
            # Therapist Gayatri

            pattern = (
                rf"(?i)^\s*"
                rf"{re.escape(label)}"
                rf"\s*(?::|-)\s*"
                rf"(.+?)\s*$"
            )

            match = re.match(
                pattern,
                line,
            )

            if match:
                return match.group(1).strip()

    return ""


def identify_outlet(
    text,
    outlets,
):

    upper_text = text.upper()

    for code, name in outlets.items():

        if re.search(
            rf"(?<![A-Z0-9])"
            rf"{re.escape(code)}"
            rf"(?![A-Z0-9])",
            upper_text,
        ):

            return code, name

    for code, name in outlets.items():

        if name.upper() in upper_text:
            return code, name

    return None, None


def parse_whatsapp(
    text,
    outlets,
):

    code, outlet_name = identify_outlet(
        text,
        outlets,
    )

    therapist = get_message_value(
        text,
        [
            "Therapist",
            "Therapist Name",
            "Name of Therapist",
        ],
    )

    shift = get_message_value(
        text,
        [
            "Shift timings",
            "Shift timing",
            "Shift",
            "Timings",
            "Timing",
        ],
    )

    guests_text = get_message_value(
        text,
        [
            "Number of guests interacted",
            "No of guests interacted",
            "No. of guests interacted",
            "Guests interacted",
            "Guest interacted",
            "Number of guests",
            "Guests",
        ],
    )

    conversions_text = get_message_value(
        text,
        [
            "Number of conversions",
            "No of conversions",
            "No. of conversions",
            "Conversions",
            "Conversion",
        ],
    )

    appointment_text = get_message_value(
        text,
        [
            "Appointment value",
            "Appointment amount",
            "Appointment Value",
            "Value",
        ],
    )

    return {
        "Outlet Code": code,
        "Outlet Name": outlet_name,
        "Therapist": therapist,
        "Shift Timings": shift,
        "Guests Interacted": number(guests_text),
        "Conversions": number(conversions_text),
        "Appointment Value": number(appointment_text),
    }


# ============================================================
# READ ACTIVITY
# ============================================================

def get_activity_records():

    ws = activity_ws()

    values = ws.get("A:H")

    if not values:

        ws.append_row(
            ACTIVITY_HEADERS
        )

        return []

    records = []

    # IMPORTANT:
    # We do NOT use get_all_records().
    # This avoids your previous duplicate-header error.

    for sheet_row, row in enumerate(
        values[1:],
        start=2,
    ):

        if not any(
            str(x).strip()
            for x in row
        ):
            continue

        row = row + [""] * (8 - len(row))

        record = {
            "Date": row[0],
            "Outlet": row[1],
            "Therapist": row[2],
            "Shift Timings": row[3],
            "Guests Interacted": row[4],
            "Conversions": row[5],
            "Appointment Value": row[6],
            "Saved At": row[7],
            "_row": sheet_row,
        }

        records.append(record)

    return records


def code_from_sheet(
    outlet_value,
    outlets,
):

    value = str(
        outlet_value
    ).strip().upper()

    for code in outlets:

        if re.search(
            rf"(?<![A-Z0-9])"
            rf"{re.escape(code)}"
            rf"(?![A-Z0-9])",
            value,
        ):
            return code

    for code, name in outlets.items():

        if name.upper() == value:
            return code

    return None


# ============================================================
# SAVE OR UPDATE
# ============================================================

def save_or_update(
    activity_date,
    parsed,
    outlets,
):

    ws = activity_ws()

    records = get_activity_records()

    target_date = activity_date.isoformat()

    target_code = parsed["Outlet Code"]

    matching_rows = []

    for record in records:

        old_date = normalize_date(
            record["Date"]
        )

        old_code = code_from_sheet(
            record["Outlet"],
            outlets,
        )

        if (
            old_date == target_date
            and old_code == target_code
        ):
            matching_rows.append(
                record["_row"]
            )

    new_row = [
        target_date,
        f"{target_code}-Lobby",
        parsed["Therapist"],
        parsed["Shift Timings"],
        parsed["Guests Interacted"],
        parsed["Conversions"],
        parsed["Appointment Value"],
        current_time(),
    ]

    if matching_rows:

        # Update the first existing record.
        row_to_update = matching_rows[0]

        ws.update(
            values=[new_row],
            range_name=(
                f"A{row_to_update}:"
                f"H{row_to_update}"
            ),
        )

        # Delete any duplicate rows for the
        # same outlet/date from bottom upward.
        duplicate_rows = matching_rows[1:]

        for duplicate_row in sorted(
            duplicate_rows,
            reverse=True,
        ):
            ws.delete_rows(
                duplicate_row
            )

        return (
            "updated",
            len(duplicate_rows),
        )

    ws.append_row(
        new_row,
        value_input_option="USER_ENTERED",
    )

    return (
        "saved",
        0,
    )


# ============================================================
# DEDUPLICATED DATA
# ============================================================

def unique_activity(outlets):

    records = get_activity_records()

    unique = {}

    duplicates = 0

    for record in records:

        record_date = normalize_date(
            record["Date"]
        )

        code = code_from_sheet(
            record["Outlet"],
            outlets,
        )

        if not record_date or not code:
            continue

        key = (
            record_date,
            code,
        )

        if key in unique:
            duplicates += 1

        # latest sheet row wins
        unique[key] = record

    return unique, duplicates


def get_daily(
    selected_date,
    outlets,
):

    unique, duplicates = unique_activity(
        outlets
    )

    target_date = selected_date.isoformat()

    result = {}

    for (record_date, code), record in unique.items():

        if record_date == target_date:
            result[code] = record

    return result, duplicates


# ============================================================
# COMMON PROJECT HEADER
# ============================================================

def project_header(
    title,
    description,
):

    st.markdown(
        f"""
        <div class="project-header">
            <div class="project-small">
                FINORA WORKSPACE
            </div>

            <div class="project-title">
                {title}
            </div>

            <div class="project-description">
                {description}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# PLACEHOLDER MODULE
# ============================================================

def module_placeholder(
    icon,
    title,
    text,
):

    project_header(
        title,
        text,
    )

    st.markdown(
        f"""
        <div class="module-box">

            <div class="module-icon">
                {icon}
            </div>

            <div class="module-name">
                {title}
            </div>

            <div class="module-text">
                This FINORA project has its own
                workspace. We will build and
                connect this module separately.
            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# HOME
# ============================================================

if st.session_state.project == "Home":

    project_header(
        "Welcome to Finora 👋",
        "Your Finance AI workspace for daily finance and operations automation.",
    )

    st.markdown(
        """
        <div class="page-title">
            What should Finora do?
        </div>

        <div class="page-description">
            Select a project from the left side.
            Each project opens in its own workspace.
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2, c3 = st.columns(3)

    with c1:

        st.markdown(
            """
            <div class="card">
                <div class="card-title">
                    📊 Lobby Activity
                </div>
                Daily activity collection,
                pending outlet monitoring and
                performance dashboards.
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c2:

        st.markdown(
            """
            <div class="card">
                <div class="card-title">
                    🧾 GST Returns
                </div>
                FINORA's GST return automation
                project.
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c3:

        st.markdown(
            """
            <div class="card">
                <div class="card-title">
                    📈 Zenoti Reports
                </div>
                FINORA's Zenoti reporting
                automation project.
            </div>
            """,
            unsafe_allow_html=True,
        )


# ============================================================
# LOBBY ACTIVITY PROJECT
# ============================================================

elif st.session_state.project == "Lobby Activity":

    try:

        outlets = get_outlets()

        if not outlets:

            st.error(
                "No active outlets found "
                "in Outlet Master."
            )

            st.stop()

    except Exception as error:

        st.error(
            "FINORA cannot connect "
            "to Google Sheets."
        )

        with st.expander(
            "Technical details"
        ):
            st.code(str(error))

        st.stop()

    project_header(
        "Lobby Activity",
        "Capture daily outlet activity, monitor performance and follow up pending submissions.",
    )

    enter_tab, daily_tab, period_tab = st.tabs(
        [
            "✍️ Enter Activity",
            "📊 Daily Dashboard",
            "📅 Period Dashboard",
        ]
    )


    # ========================================================
    # ENTER ACTIVITY
    # ========================================================

    with enter_tab:

        st.markdown(
            """
            <div class="page-title">
                Enter Lobby Activity
            </div>

            <div class="page-description">
                Copy the activity message from
                WhatsApp and paste it below.
            </div>
            """,
            unsafe_allow_html=True,
        )

        left, right = st.columns(
            [1, 2],
            gap="large",
        )

        with left:

            activity_date = st.date_input(
                "Activity Date",
                value=date.today(),
                format="DD/MM/YYYY",
            )

            photo = st.file_uploader(
                "Optional Photo",
                type=[
                    "jpg",
                    "jpeg",
                    "png",
                ],
            )

            st.caption(
                "Photos are not stored by FINORA."
            )

        with right:

            activity_text = st.text_area(
                "Paste WhatsApp Activity",
                height=240,
                placeholder=(
                    "JIAL-Lobby Activity\n"
                    "1. Therapist: Gayatri\n"
                    "2. Shift timings: 7AM to 4PM\n"
                    "3. Number of guests interacted- 5\n"
                    "4. Number of conversions: 2\n"
                    "5. Appointment value:7064"
                ),
            )

        save_clicked = st.button(
            "✨ Read & Save Activity",
            type="primary",
            use_container_width=True,
        )

        if save_clicked:

            if not activity_text.strip():

                st.error(
                    "Please paste the WhatsApp "
                    "activity first."
                )

            else:

                parsed = parse_whatsapp(
                    activity_text,
                    outlets,
                )

                if not parsed["Outlet Code"]:

                    st.error(
                        "FINORA could not recognise "
                        "the outlet code."
                    )

                else:

                    # Show exactly what FINORA read.
                    st.markdown(
                        "#### FINORA read:"
                    )

                    preview = pd.DataFrame(
                        [
                            {
                                "Outlet":
                                    parsed["Outlet Code"],

                                "Therapist":
                                    parsed["Therapist"],

                                "Shift":
                                    parsed["Shift Timings"],

                                "Guests":
                                    parsed["Guests Interacted"],

                                "Conversions":
                                    parsed["Conversions"],

                                "Appointment Value":
                                    parsed["Appointment Value"],
                            }
                        ]
                    )

                    st.dataframe(
                        preview,
                        use_container_width=True,
                        hide_index=True,
                    )

                    missing = []

                    if not parsed["Therapist"]:
                        missing.append("Therapist")

                    if not parsed["Shift Timings"]:
                        missing.append("Shift Timings")

                    if missing:

                        st.error(
                            "FINORA could not read: "
                            + ", ".join(missing)
                            + ". Please check the message."
                        )

                    else:

                        try:

                            action, duplicates_removed = (
                                save_or_update(
                                    activity_date,
                                    parsed,
                                    outlets,
                                )
                            )

                            if action == "updated":

                                st.success(
                                    "🔄 Activity UPDATED successfully — "
                                    f"{parsed['Outlet Code']} • "
                                    f"{parsed['Outlet Name']}"
                                )

                            else:

                                st.success(
                                    "✅ New activity SAVED successfully — "
                                    f"{parsed['Outlet Code']} • "
                                    f"{parsed['Outlet Name']}"
                                )

                            if duplicates_removed:

                                st.info(
                                    f"{duplicates_removed} duplicate "
                                    "record(s) were removed."
                                )

                            # Re-read Google Sheet immediately
                            # and confirm what is actually saved.
                            fresh_records = get_activity_records()

                            saved_record = None

                            for record in reversed(
                                fresh_records
                            ):

                                if (
                                    normalize_date(
                                        record["Date"]
                                    )
                                    == activity_date.isoformat()
                                    and
                                    code_from_sheet(
                                        record["Outlet"],
                                        outlets,
                                    )
                                    == parsed["Outlet Code"]
                                ):

                                    saved_record = record
                                    break

                            if saved_record:

                                st.markdown(
                                    "#### Confirmed in Google Sheet"
                                )

                                st.dataframe(
                                    pd.DataFrame(
                                        [
                                            {
                                                "Date":
                                                    saved_record["Date"],

                                                "Outlet":
                                                    saved_record["Outlet"],

                                                "Therapist":
                                                    saved_record["Therapist"],

                                                "Shift":
                                                    saved_record["Shift Timings"],

                                                "Guests":
                                                    saved_record["Guests Interacted"],

                                                "Conversions":
                                                    saved_record["Conversions"],

                                                "Appointment Value":
                                                    saved_record["Appointment Value"],
                                            }
                                        ]
                                    ),
                                    use_container_width=True,
                                    hide_index=True,
                                )

                        except Exception as error:

                            st.error(
                                "FINORA recognised the activity, "
                                "but Google Sheets could not be updated."
                            )

                            with st.expander(
                                "Technical details"
                            ):
                                st.code(str(error))


    # ========================================================
    # DAILY DASHBOARD
    # ========================================================

    with daily_tab:

        st.markdown(
            """
            <div class="page-title">
                Daily Dashboard
            </div>

            <div class="page-description">
                Check received activity,
                performance and pending outlets
                for any selected date.
            </div>
            """,
            unsafe_allow_html=True,
        )

        date_col, blank = st.columns(
            [1, 3]
        )

        with date_col:

            selected_date = st.date_input(
                "Dashboard Date",
                value=date.today(),
                format="DD/MM/YYYY",
                key="daily_dashboard_date",
            )

        daily, duplicate_count = get_daily(
            selected_date,
            outlets,
        )

        received_codes = list(
            daily.keys()
        )

        pending_codes = [
            code
            for code in outlets
            if code not in daily
        ]

        guests = sum(
            number(
                r["Guests Interacted"]
            )
            for r in daily.values()
        )

        conversions = sum(
            number(
                r["Conversions"]
            )
            for r in daily.values()
        )

        appointment_value = sum(
            number(
                r["Appointment Value"]
            )
            for r in daily.values()
        )

        conversion_rate = (
            conversions / guests * 100
            if guests
            else 0
        )

        m1, m2, m3, m4, m5, m6 = st.columns(6)

        m1.metric(
            "Total Outlets",
            len(outlets),
        )

        m2.metric(
            "Received",
            len(received_codes),
        )

        m3.metric(
            "Pending",
            len(pending_codes),
        )

        m4.metric(
            "Guests",
            int(guests),
        )

        m5.metric(
            "Conversions",
            int(conversions),
        )

        m6.metric(
            "Appointment Value",
            rupees(appointment_value),
        )

        st.write("")

        left, right = st.columns(
            [1, 1],
            gap="large",
        )

        with left:

            st.markdown(
                """
                <div class="card">
                    <div class="card-title">
                        🟢 Received Outlets
                    </div>
                """,
                unsafe_allow_html=True,
            )

            if received_codes:

                html = "".join(
                    f'<span class="pill received">'
                    f'{code} • {outlets[code]}'
                    f'</span>'
                    for code in received_codes
                )

                st.markdown(
                    html,
                    unsafe_allow_html=True,
                )

            else:

                st.info(
                    "No submissions received yet."
                )

            st.markdown(
                "</div>",
                unsafe_allow_html=True,
            )

        with right:

            st.markdown(
                """
                <div class="card">
                    <div class="card-title">
                        🔴 Pending Follow-up
                    </div>
                """,
                unsafe_allow_html=True,
            )

            if pending_codes:

                html = "".join(
                    f'<span class="pill pending">'
                    f'{code} • {outlets[code]}'
                    f'</span>'
                    for code in pending_codes
                )

                st.markdown(
                    html,
                    unsafe_allow_html=True,
                )

            else:

                st.success(
                    "All outlets submitted 🎉"
                )

            st.markdown(
                "</div>",
                unsafe_allow_html=True,
            )

        if daily:

            chart_rows = []

            for code, record in daily.items():

                chart_rows.append(
                    {
                        "Outlet": code,
                        "Guests":
                            number(
                                record["Guests Interacted"]
                            ),
                        "Conversions":
                            number(
                                record["Conversions"]
                            ),
                        "Appointment Value":
                            number(
                                record["Appointment Value"]
                            ),
                    }
                )

            chart_df = pd.DataFrame(
                chart_rows
            )

            c1, c2 = st.columns(
                2,
                gap="large",
            )

            with c1:

                st.markdown(
                    "### 👥 Guests vs Conversions"
                )

                st.bar_chart(
                    chart_df.set_index(
                        "Outlet"
                    )[
                        [
                            "Guests",
                            "Conversions",
                        ]
                    ],
                    height=300,
                )

            with c2:

                st.markdown(
                    "### 💰 Appointment Value"
                )

                st.bar_chart(
                    chart_df.set_index(
                        "Outlet"
                    )[
                        ["Appointment Value"]
                    ],
                    height=300,
                )

        st.markdown(
            "### 💬 WhatsApp Follow-up Summary"
        )

        pending_text = (
            ", ".join(pending_codes)
            if pending_codes
            else "None"
        )

        st.code(
            f"""FINORA Lobby Activity | {selected_date.strftime('%d %b %Y')}
Received: {len(received_codes)}/{len(outlets)}
Pending: {len(pending_codes)}
Guests: {int(guests)}
Conversions: {int(conversions)}
Conversion Rate: {conversion_rate:.1f}%
Appointment Value: {rupees(appointment_value)}
Pending Outlets: {pending_text}"""
        )

        details = []

        for code, name in outlets.items():

            record = daily.get(code)

            if record:

                details.append(
                    {
                        "Code": code,
                        "Outlet": name,
                        "Status": "Received",
                        "Therapist":
                            record["Therapist"],
                        "Shift":
                            record["Shift Timings"],
                        "Guests":
                            number(
                                record["Guests Interacted"]
                            ),
                        "Conversions":
                            number(
                                record["Conversions"]
                            ),
                        "Appointment Value":
                            number(
                                record["Appointment Value"]
                            ),
                    }
                )

            else:

                details.append(
                    {
                        "Code": code,
                        "Outlet": name,
                        "Status": "Pending",
                        "Therapist": "",
                        "Shift": "",
                        "Guests": "",
                        "Conversions": "",
                        "Appointment Value": "",
                    }
                )

        with st.expander(
            "📋 Complete outlet-wise details"
        ):

            st.dataframe(
                pd.DataFrame(details),
                use_container_width=True,
                hide_index=True,
                height=500,
            )


    # ========================================================
    # PERIOD DASHBOARD
    # ========================================================

    with period_tab:

        st.markdown(
            """
            <div class="page-title">
                Period Dashboard
            </div>

            <div class="page-description">
                Select a date range to see
                submissions and exact pending dates
                outlet by outlet.
            </div>
            """,
            unsafe_allow_html=True,
        )

        c1, c2, blank = st.columns(
            [1, 1, 2]
        )

        with c1:

            start_date = st.date_input(
                "From Date",
                value=date.today(),
                format="DD/MM/YYYY",
                key="period_start",
            )

        with c2:

            end_date = st.date_input(
                "To Date",
                value=date.today(),
                format="DD/MM/YYYY",
                key="period_end",
            )

        if end_date < start_date:

            st.error(
                "To Date cannot be before From Date."
            )

        else:

            unique, duplicates = unique_activity(
                outlets
            )

            days = []

            d = start_date

            while d <= end_date:

                days.append(d)

                d += timedelta(days=1)

            rows = []

            for code, name in outlets.items():

                received_days = []
                missing_days = []

                total_guests = 0
                total_conversions = 0
                total_value = 0

                for day in days:

                    record = unique.get(
                        (
                            day.isoformat(),
                            code,
                        )
                    )

                    if record:

                        received_days.append(day)

                        total_guests += number(
                            record["Guests Interacted"]
                        )

                        total_conversions += number(
                            record["Conversions"]
                        )

                        total_value += number(
                            record["Appointment Value"]
                        )

                    else:

                        missing_days.append(day)

                rows.append(
                    {
                        "Code": code,
                        "Outlet": name,
                        "Received Days":
                            len(received_days),
                        "Pending Days":
                            len(missing_days),
                        "Guests":
                            total_guests,
                        "Conversions":
                            total_conversions,
                        "Appointment Value":
                            total_value,
                        "Missing Dates":
                            ", ".join(
                                x.strftime("%d-%b")
                                for x in missing_days
                            )
                            if missing_days
                            else "Complete",
                    }
                )

            period_df = pd.DataFrame(rows)

            expected = (
                len(days)
                * len(outlets)
            )

            received = int(
                period_df[
                    "Received Days"
                ].sum()
            )

            pending = (
                expected - received
            )

            total_guests = int(
                period_df[
                    "Guests"
                ].sum()
            )

            total_conversions = int(
                period_df[
                    "Conversions"
                ].sum()
            )

            total_value = period_df[
                "Appointment Value"
            ].sum()

            p1, p2, p3, p4, p5, p6 = st.columns(6)

            p1.metric(
                "Days",
                len(days),
            )

            p2.metric(
                "Expected",
                expected,
            )

            p3.metric(
                "Received",
                received,
            )

            p4.metric(
                "Pending",
                pending,
            )

            p5.metric(
                "Guests",
                total_guests,
            )

            p6.metric(
                "Appointment Value",
                rupees(total_value),
            )

            st.markdown(
                "### 🔴 Pending Outlet / Date Follow-up"
            )

            pending_df = period_df[
                period_df["Pending Days"] > 0
            ]

            if pending_df.empty:

                st.success(
                    "All outlets are complete "
                    "for this period 🎉"
                )

            else:

                st.dataframe(
                    pending_df[
                        [
                            "Code",
                            "Outlet",
                            "Received Days",
                            "Pending Days",
                            "Missing Dates",
                        ]
                    ],
                    use_container_width=True,
                    hide_index=True,
                    height=420,
                )

            st.markdown(
                "### 📊 Outlet Performance"
            )

            st.bar_chart(
                period_df.set_index(
                    "Code"
                )[
                    [
                        "Guests",
                        "Conversions",
                    ]
                ],
                height=320,
            )

            with st.expander(
                "📋 Complete period report"
            ):

                st.dataframe(
                    period_df,
                    use_container_width=True,
                    hide_index=True,
                    height=500,
                )


# ============================================================
# OTHER FINORA PROJECTS
# ============================================================

elif st.session_state.project == "GST Returns":

    module_placeholder(
        "🧾",
        "GST Returns",
        "GST return download and processing automation.",
    )


elif st.session_state.project == "Zenoti Reports":

    module_placeholder(
        "📈",
        "Zenoti Reports",
        "Automated Zenoti organisation report downloads.",
    )


elif st.session_state.project == "Cash Reconciliation":

    module_placeholder(
        "💰",
        "Cash Reconciliation",
        "Cash sales versus cash deposit reconciliation.",
    )


elif st.session_state.project == "Files":

    module_placeholder(
        "📁",
        "Files",
        "FINORA file and report centre.",
    )


elif st.session_state.project == "Settings":

    module_placeholder(
        "⚙️",
        "Settings",
        "FINORA administration and configuration.",
    )
