import streamlit as st
import pandas as pd
import re
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import gspread
from google.oauth2.service_account import Credentials


# ============================================================
# FINORA - PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="FINORA | Your Finance AI",
    page_icon="💠",
    layout="wide",
    initial_sidebar_state="expanded",
)

ACTIVITY_SHEET = "Activity"
OUTLET_MASTER_SHEET = "Outlet Master"

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
# PREMIUM FINORA DESIGN
# ============================================================

st.markdown(
    """
<style>

/* ----------------------------------------------------------
   GLOBAL
---------------------------------------------------------- */

html, body, [class*="css"] {
    font-family: "Segoe UI", Arial, sans-serif;
}

.stApp {
    background:
        radial-gradient(circle at 95% 5%,
            rgba(93, 91, 255, 0.06),
            transparent 24%),
        #f7f9fc;
}

.block-container {
    max-width: 1500px;
    padding-top: 1.1rem;
    padding-left: 2.2rem;
    padding-right: 2.2rem;
    padding-bottom: 3rem;
}


/* ----------------------------------------------------------
   SIDEBAR
---------------------------------------------------------- */

section[data-testid="stSidebar"] {
    background:
        linear-gradient(
            180deg,
            #081d38 0%,
            #0b2948 100%
        );
    border-right: 1px solid #173b5d;
}

section[data-testid="stSidebar"] > div {
    padding-top: 18px;
}

section[data-testid="stSidebar"] * {
    color: #ffffff;
}

.sidebar-brand {
    padding: 14px 8px 24px 8px;
    text-align: left;
}

.sidebar-logo-row {
    display: flex;
    align-items: center;
    gap: 13px;
}

.sidebar-logo-icon {
    width: 52px;
    height: 52px;
    border-radius: 15px;

    display: flex;
    align-items: center;
    justify-content: center;

    font-size: 30px;

    background:
        linear-gradient(
            135deg,
            #26d3a5,
            #16a7bc
        );

    box-shadow:
        0 8px 20px
        rgba(0, 0, 0, 0.18);
}

.sidebar-finora {
    color: white !important;
    font-size: 29px !important;
    font-weight: 800 !important;
    letter-spacing: 1px;
    line-height: 1;
}

.sidebar-tagline {
    color: #9db5ca !important;
    font-size: 14px !important;
    margin-top: 6px;
}

.sidebar-section {
    color: #6f8aa4 !important;
    font-size: 12px !important;
    font-weight: 700;
    letter-spacing: 1.4px;
    margin: 20px 5px 10px 5px;
}

.sidebar-menu {
    padding: 12px 14px;
    margin: 6px 0;

    border-radius: 11px;

    font-size: 16px;
    font-weight: 600;

    color: #cbd9e6 !important;
}

.sidebar-menu-active {
    padding: 12px 14px;
    margin: 6px 0;

    border-radius: 11px;

    font-size: 16px;
    font-weight: 700;

    color: white !important;

    background:
        linear-gradient(
            90deg,
            rgba(39, 211, 170, 0.22),
            rgba(62, 129, 232, 0.18)
        );

    border-left:
        4px solid #2ad4a6;
}

.sidebar-status {
    margin-top: 28px;

    padding: 15px;

    background:
        rgba(255,255,255,0.06);

    border:
        1px solid rgba(255,255,255,0.08);

    border-radius:
        13px;
}

.status-dot {
    display: inline-block;

    width: 10px;
    height: 10px;

    border-radius: 50%;

    background: #2dd79b;

    margin-right: 7px;

    box-shadow:
        0 0 8px
        rgba(45, 215, 155, 0.8);
}


/* ----------------------------------------------------------
   TOP BRAND
---------------------------------------------------------- */

.top-brand {
    display: flex;
    align-items: center;
    gap: 15px;

    margin-bottom: 17px;
}

.top-logo {
    width: 58px;
    height: 58px;

    border-radius: 17px;

    display: flex;
    align-items: center;
    justify-content: center;

    font-size: 32px;

    background:
        linear-gradient(
            135deg,
            #27d3a8,
            #18a7c4
        );

    box-shadow:
        0 8px 20px
        rgba(19, 167, 175, 0.20);
}

.top-finora {
    font-size: 34px !important;
    font-weight: 800 !important;
    line-height: 1 !important;

    color: #092a55 !important;

    margin: 0 !important;
}

.top-tagline {
    color: #73859a !important;
    font-size: 16px !important;
    margin-top: 6px;
}


/* ----------------------------------------------------------
   PAGE HERO
---------------------------------------------------------- */

.page-hero {
    position: relative;
    overflow: hidden;

    padding: 25px 28px;

    margin-top: 10px;
    margin-bottom: 20px;

    border-radius: 20px;

    background:
        linear-gradient(
            120deg,
            #092747 0%,
            #105b73 60%,
            #119486 100%
        );

    box-shadow:
        0 12px 28px
        rgba(8, 39, 72, 0.13);
}

.page-hero::after {
    content: "";

    position: absolute;

    width: 180px;
    height: 180px;

    right: -60px;
    top: -100px;

    border-radius: 50%;

    background:
        rgba(255,255,255,0.08);
}

.hero-eyebrow {
    color: #7debd1 !important;
    font-size: 13px !important;
    font-weight: 750;
    letter-spacing: 1.2px;
    text-transform: uppercase;
}

.hero-title {
    color: white !important;

    font-size: 31px !important;
    font-weight: 800 !important;

    margin-top: 5px;
}

.hero-text {
    color: #d9eef1 !important;

    font-size: 16px !important;

    margin-top: 5px;
}


/* ----------------------------------------------------------
   TABS
---------------------------------------------------------- */

div[data-baseweb="tab-list"] {

    gap: 8px;

    background: white;

    padding: 7px;

    border-radius: 14px;

    border: 1px solid #e1e8ef;

    box-shadow:
        0 5px 16px
        rgba(17, 44, 74, 0.045);
}

button[data-baseweb="tab"] {

    height: 51px;

    padding-left: 22px !important;
    padding-right: 22px !important;

    border-radius: 10px !important;

    font-size: 16px !important;
    font-weight: 650 !important;

    color: #52677d !important;
}

button[data-baseweb="tab"][aria-selected="true"] {

    color: #5b57f6 !important;

    background:
        linear-gradient(
            135deg,
            #efefff,
            #eef8ff
        ) !important;
}


/* ----------------------------------------------------------
   NORMAL BODY TEXT
---------------------------------------------------------- */

.stApp p {
    font-size: 16px;
}

div[data-testid="stWidgetLabel"] p {

    font-size: 16px !important;
    font-weight: 650 !important;

    color: #334e68 !important;
}

div[data-testid="stCaptionContainer"] p {

    font-size: 14px !important;

    color: #718096 !important;
}


/* ----------------------------------------------------------
   SECTION TITLE
---------------------------------------------------------- */

.section-title {

    font-size: 26px !important;

    font-weight: 800 !important;

    color: #102a43 !important;

    margin-top: 18px;
    margin-bottom: 3px;
}

.section-subtitle {

    font-size: 16px !important;

    color: #718096 !important;

    margin-bottom: 20px;
}


/* ----------------------------------------------------------
   INPUTS
---------------------------------------------------------- */

div[data-baseweb="input"] {

    min-height: 48px;

    border-radius: 11px !important;

    background: white !important;

    border: 1px solid #dce5ec !important;
}

input {

    font-size: 16px !important;
}

textarea {

    font-size: 16px !important;

    line-height: 1.55 !important;

    min-height: 210px !important;

    border-radius: 13px !important;

    background: white !important;

    border: 1px solid #dce5ec !important;
}

div[data-testid="stFileUploader"] section {

    background:
        linear-gradient(
            135deg,
            #f1f8ff,
            #effbf8
        );

    border:
        1px dashed #9bbdca;

    border-radius:
        13px;

    padding: 17px;
}


/* ----------------------------------------------------------
   PRIMARY BUTTON
---------------------------------------------------------- */

div.stButton > button[kind="primary"] {

    min-height: 55px;

    border: none;

    border-radius: 12px;

    color: white;

    font-size: 17px !important;
    font-weight: 750 !important;

    background:
        linear-gradient(
            90deg,
            #5d5cf6 0%,
            #5575ef 45%,
            #19a997 100%
        );

    box-shadow:
        0 8px 20px
        rgba(78, 93, 230, 0.20);
}

div.stButton > button[kind="primary"]:hover {

    color: white;

    border: none;

    transform:
        translateY(-1px);
}


/* ----------------------------------------------------------
   KPI CARDS
---------------------------------------------------------- */

div[data-testid="stMetric"] {

    position: relative;

    overflow: hidden;

    min-height: 112px;

    padding: 16px 17px;

    background: white;

    border: 1px solid #e0e7ee;

    border-radius: 16px;

    box-shadow:
        0 6px 18px
        rgba(15, 42, 72, 0.055);
}

div[data-testid="stMetricLabel"] p {

    font-size: 14px !important;

    font-weight: 700 !important;

    color: #66788b !important;
}

div[data-testid="stMetricValue"] {

    font-size: 27px !important;

    font-weight: 800 !important;

    color: #102a43 !important;
}


/* ----------------------------------------------------------
   CUSTOM CARDS
---------------------------------------------------------- */

.fin-card {

    background: white;

    border:
        1px solid #e1e8ef;

    border-radius:
        17px;

    padding:
        20px;

    box-shadow:
        0 6px 18px
        rgba(15, 42, 72, 0.055);

    margin-bottom:
        14px;
}

.fin-card-title {

    font-size:
        19px !important;

    font-weight:
        800;

    color:
        #173b5e !important;

    margin-bottom:
        12px;
}


/* ----------------------------------------------------------
   RECEIVED / PENDING
---------------------------------------------------------- */

.status-wrap {

    display: grid;

    grid-template-columns:
        1fr 1fr;

    gap: 13px;
}

.received-card {

    padding: 18px;

    border-radius: 14px;

    text-align: center;

    background:
        linear-gradient(
            135deg,
            #dff9ee,
            #effcf7
        );

    border:
        1px solid #b9ead7;
}

.pending-card {

    padding: 18px;

    border-radius: 14px;

    text-align: center;

    background:
        linear-gradient(
            135deg,
            #ffeded,
            #fff7f3
        );

    border:
        1px solid #ffd0c9;
}

.status-big {

    font-size:
        35px !important;

    font-weight:
        850;
}

.status-small {

    font-size:
        13px !important;

    font-weight:
        750;

    letter-spacing:
        0.6px;
}


/* ----------------------------------------------------------
   OUTLET PILLS
---------------------------------------------------------- */

.outlet-pill {

    display: inline-block;

    padding:
        7px 11px;

    margin:
        5px 4px;

    border-radius:
        20px;

    font-size:
        14px !important;

    font-weight:
        650;
}

.pending-pill {

    color:
        #a23a3a;

    background:
        #fff0ef;

    border:
        1px solid #ffc9c4;
}

.received-pill {

    color:
        #087052;

    background:
        #e4f9f0;

    border:
        1px solid #bce9d7;
}


/* ----------------------------------------------------------
   TABLES / EXPANDERS
---------------------------------------------------------- */

div[data-testid="stDataFrame"] {

    background:
        white;

    border:
        1px solid #e0e7ee;

    border-radius:
        14px;

    overflow:
        hidden;

    box-shadow:
        0 5px 16px
        rgba(15, 42, 72, 0.045);
}

div[data-testid="stExpander"] {

    background:
        white;

    border:
        1px solid #e0e7ee;

    border-radius:
        14px;
}

div[data-testid="stExpander"] summary p {

    font-size:
        16px !important;

    font-weight:
        650 !important;
}


/* ----------------------------------------------------------
   ALERTS
---------------------------------------------------------- */

div[data-testid="stAlert"] {

    border-radius:
        13px;
}

div[data-testid="stAlert"] p {

    font-size:
        16px !important;
}


/* ----------------------------------------------------------
   WHATSAPP BOX
---------------------------------------------------------- */

.whatsapp-box {

    padding:
        18px 20px;

    border-radius:
        15px;

    background:
        linear-gradient(
            135deg,
            #eafaf3,
            #eef8ff
        );

    border:
        1px solid #cbe7db;

    color:
        #173b4f;

    font-size:
        16px !important;

    line-height:
        1.65;

    white-space:
        pre-line;
}


/* ----------------------------------------------------------
   FOOTER
---------------------------------------------------------- */

.finora-footer {

    text-align:
        center;

    color:
        #94a3b8 !important;

    font-size:
        13px !important;

    margin-top:
        35px;

    padding:
        15px;
}


/* ----------------------------------------------------------
   HIDE STREAMLIT DEFAULTS
---------------------------------------------------------- */

#MainMenu {
    visibility: hidden;
}

footer {
    visibility: hidden;
}


/* ----------------------------------------------------------
   MOBILE
---------------------------------------------------------- */

@media (max-width: 900px) {

    .block-container {

        padding-left:
            14px;

        padding-right:
            14px;
    }

    .top-finora {

        font-size:
            28px !important;
    }

    .status-wrap {

        grid-template-columns:
            1fr;
    }
}

</style>
""",
    unsafe_allow_html=True,
)


# ============================================================
# SIDEBAR - FINORA PLATFORM
# ============================================================

with st.sidebar:

    st.markdown(
        """
<div class="sidebar-brand">

    <div class="sidebar-logo-row">

        <div class="sidebar-logo-icon">
            F
        </div>

        <div>

            <div class="sidebar-finora">
                FINORA
            </div>

            <div class="sidebar-tagline">
                Your Finance AI
            </div>

        </div>

    </div>

</div>

<div class="sidebar-section">
    WORKSPACE
</div>

<div class="sidebar-menu">
    🏠 &nbsp; Home
</div>

<div class="sidebar-menu-active">
    📊 &nbsp; Lobby Activity
</div>

<div class="sidebar-menu">
    🧾 &nbsp; GST Returns
</div>

<div class="sidebar-menu">
    📈 &nbsp; Zenoti Reports
</div>

<div class="sidebar-menu">
    💰 &nbsp; Cash Reconciliation
</div>

<div class="sidebar-menu">
    📁 &nbsp; Files
</div>

<div class="sidebar-menu">
    ⚙️ &nbsp; Settings
</div>

<div class="sidebar-status">

    <div style="
        color:#8da8bf;
        font-size:12px;
        font-weight:700;
        margin-bottom:8px;
    ">
        SYSTEM STATUS
    </div>

    <div style="
        color:white;
        font-size:15px;
    ">
        <span class="status-dot"></span>
        FINORA Online
    </div>

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

    <div class="top-logo">
        F
    </div>

    <div>

        <div class="top-finora">
            Finora
        </div>

        <div class="top-tagline">
            Your Finance AI
        </div>

    </div>

</div>
""",
    unsafe_allow_html=True,
)


# ============================================================
# GOOGLE SHEETS
# ============================================================

@st.cache_resource
def get_spreadsheet():

    info = dict(
        st.secrets[
            "google_service_account"
        ]
    )

    credentials = (
        Credentials.from_service_account_info(
            info,
            scopes=[
                "https://www.googleapis.com/auth/spreadsheets"
            ],
        )
    )

    client = gspread.authorize(
        credentials
    )

    return client.open_by_key(
        st.secrets[
            "spreadsheet_id"
        ]
    )


def get_activity_sheet():

    return (
        get_spreadsheet()
        .worksheet(
            ACTIVITY_SHEET
        )
    )


def get_master_sheet():

    return (
        get_spreadsheet()
        .worksheet(
            OUTLET_MASTER_SHEET
        )
    )


# ============================================================
# HELPERS
# ============================================================

def clean_number(value):

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

    number = float(
        match.group()
    )

    if number.is_integer():
        return int(number)

    return number


def money(value):

    try:

        return (
            f"₹{float(value):,.0f}"
        )

    except Exception:

        return "₹0"


def normalize_date(value):

    text = str(
        value
    ).strip()

    if not text:
        return ""

    formats = [
        "%Y-%m-%d",
        "%d-%m-%Y",
        "%d/%m/%Y",
        "%m/%d/%Y",
        "%Y/%m/%d",
        "%d %b %Y",
        "%d %B %Y",
    ]

    for fmt in formats:

        try:

            return (
                datetime.strptime(
                    text,
                    fmt,
                )
                .date()
                .isoformat()
            )

        except ValueError:

            pass

    try:

        return (
            pd.to_datetime(
                text,
                dayfirst=True,
            )
            .date()
            .isoformat()
        )

    except Exception:

        return text


def now_ist():

    return datetime.now(
        ZoneInfo(
            "Asia/Kolkata"
        )
    ).strftime(
        "%Y-%m-%d %H:%M:%S"
    )


# ============================================================
# OUTLET MASTER
# ============================================================

def load_outlet_master():

    worksheet = (
        get_master_sheet()
    )

    values = worksheet.get(
        "A:C"
    )

    outlets = {}

    if len(values) < 2:

        return outlets

    for row in values[1:]:

        row = (
            row
            + [""] * (
                3 - len(row)
            )
        )

        code = str(
            row[0]
        ).strip().upper()

        name = str(
            row[1]
        ).strip()

        active = str(
            row[2]
        ).strip().lower()

        if (
            code
            and name
            and active in {
                "yes",
                "y",
                "true",
                "1",
                "active",
            }
        ):

            outlets[
                code
            ] = name

    return outlets


# ============================================================
# WHATSAPP MESSAGE PARSER
# ============================================================

def extract_field(
    text,
    labels,
):

    for label in labels:

        pattern = (
            rf"(?im)^\s*"
            rf"{re.escape(label)}"
            rf"\s*[:\-]\s*"
            rf"(.*?)\s*$"
        )

        match = re.search(
            pattern,
            text,
        )

        if match:

            return (
                match.group(1)
                .strip()
            )

    return ""


def detect_outlet(
    text,
    outlets,
):

    upper = text.upper()

    # Search outlet code first.
    for code, name in (
        outlets.items()
    ):

        if re.search(
            rf"(?<![A-Z0-9])"
            rf"{re.escape(code)}"
            rf"(?![A-Z0-9])",
            upper,
        ):

            return (
                code,
                name,
            )

    # Search full outlet name.
    for code, name in (
        outlets.items()
    ):

        if (
            name.upper()
            in upper
        ):

            return (
                code,
                name,
            )

    return (
        None,
        None,
    )


def parse_activity(
    text,
    outlets,
):

    code, name = (
        detect_outlet(
            text,
            outlets,
        )
    )

    return {

        "Outlet Code":
            code,

        "Outlet Name":
            name,

        "Therapist":
            extract_field(
                text,
                [
                    "Therapist",
                    "Therapist Name",
                    "Name of Therapist",
                    "Staff",
                ],
            ),

        "Shift Timings":
            extract_field(
                text,
                [
                    "Shift",
                    "Shift Timing",
                    "Shift Timings",
                    "Timing",
                    "Timings",
                ],
            ),

        "Guests Interacted":
            clean_number(
                extract_field(
                    text,
                    [
                        "Guests Interacted",
                        "Guest Interacted",
                        "Guests",
                        "Guest",
                        "No of Guests",
                        "No. of Guests",
                    ],
                )
            ),

        "Conversions":
            clean_number(
                extract_field(
                    text,
                    [
                        "Conversions",
                        "Conversion",
                        "Converted",
                    ],
                )
            ),

        "Appointment Value":
            clean_number(
                extract_field(
                    text,
                    [
                        "Appointment Value",
                        "Appointment Amount",
                        "Appointment",
                        "Value",
                    ],
                )
            ),
    }


# ============================================================
# READ ACTIVITY SHEET
# ============================================================

def read_activity():

    worksheet = (
        get_activity_sheet()
    )

    values = worksheet.get(
        "A:H"
    )

    if not values:

        worksheet.append_row(
            ACTIVITY_HEADERS
        )

        return []

    records = []

    for row_number, row in (
        enumerate(
            values[1:],
            start=2,
        )
    ):

        if not any(row):

            continue

        row = (
            row
            + [""] * (
                8 - len(row)
            )
        )

        record = {
            ACTIVITY_HEADERS[i]:
                row[i]
            for i in range(8)
        }

        record[
            "_row"
        ] = row_number

        records.append(
            record
        )

    return records


def sheet_outlet_code(
    value,
    outlets,
):

    upper = str(
        value
    ).strip().upper()

    for code in outlets:

        if re.search(
            rf"(?<![A-Z0-9])"
            rf"{re.escape(code)}"
            rf"(?![A-Z0-9])",
            upper,
        ):

            return code

    for code, name in (
        outlets.items()
    ):

        if (
            name.upper()
            == upper
        ):

            return code

    return None


# ============================================================
# SAVE / UPDATE / DUPLICATE CONTROL
# ============================================================

def save_activity(
    activity_date,
    parsed,
    outlets,
):

    worksheet = (
        get_activity_sheet()
    )

    records = (
        read_activity()
    )

    target_date = (
        activity_date
        .isoformat()
    )

    target_code = (
        parsed[
            "Outlet Code"
        ]
    )

    matches = []

    for record in records:

        record_date = (
            normalize_date(
                record.get(
                    "Date",
                    "",
                )
            )
        )

        record_code = (
            sheet_outlet_code(
                record.get(
                    "Outlet",
                    "",
                ),
                outlets,
            )
        )

        if (
            record_date
            == target_date
            and record_code
            == target_code
        ):

            matches.append(
                record[
                    "_row"
                ]
            )

    values = [

        target_date,

        f"{target_code}-Lobby",

        parsed[
            "Therapist"
        ],

        parsed[
            "Shift Timings"
        ],

        parsed[
            "Guests Interacted"
        ],

        parsed[
            "Conversions"
        ],

        parsed[
            "Appointment Value"
        ],

        now_ist(),
    ]

    if matches:

        main_row = (
            matches[0]
        )

        worksheet.update(
            range_name=(
                f"A{main_row}:"
                f"H{main_row}"
            ),
            values=[
                values
            ],
        )

        duplicates = (
            matches[1:]
        )

        for row_number in sorted(
            duplicates,
            reverse=True,
        ):

            worksheet.delete_rows(
                row_number
            )

        return (
            "updated",
            len(
                duplicates
            ),
        )

    worksheet.append_row(
        values,
        value_input_option=(
            "USER_ENTERED"
        ),
    )

    return (
        "saved",
        0,
    )


# ============================================================
# UNIQUE DATA
# ============================================================

def build_unique_activity(
    outlets,
):

    records = (
        read_activity()
    )

    unique = {}

    duplicate_count = 0

    for record in records:

        day = (
            normalize_date(
                record.get(
                    "Date",
                    "",
                )
            )
        )

        code = (
            sheet_outlet_code(
                record.get(
                    "Outlet",
                    "",
                ),
                outlets,
            )
        )

        if (
            not day
            or not code
        ):

            continue

        key = (
            day,
            code,
        )

        if key in unique:

            duplicate_count += 1

        # Latest row wins.
        unique[
            key
        ] = record

    return (
        unique,
        duplicate_count,
    )


def daily_activity(
    selected_date,
    outlets,
):

    unique, duplicates = (
        build_unique_activity(
            outlets
        )
    )

    target = (
        selected_date
        .isoformat()
    )

    daily = {}

    for (
        record_date,
        code,
    ), record in (
        unique.items()
    ):

        if (
            record_date
            == target
        ):

            daily[
                code
            ] = record

    return (
        daily,
        duplicates,
    )


# ============================================================
# PERIOD DATA
# ============================================================

def period_activity(
    start_date,
    end_date,
    outlets,
):

    unique, duplicate_count = (
        build_unique_activity(
            outlets
        )
    )

    all_dates = []

    current = start_date

    while (
        current
        <= end_date
    ):

        all_dates.append(
            current
        )

        current += timedelta(
            days=1
        )

    outlet_rows = []

    daily_rows = []

    for day in all_dates:

        day_records = []

        for code in outlets:

            record = (
                unique.get(
                    (
                        day.isoformat(),
                        code,
                    )
                )
            )

            if record:

                day_records.append(
                    record
                )

        guests = sum(
            clean_number(
                r.get(
                    "Guests Interacted",
                    0,
                )
            )
            for r in day_records
        )

        conversions = sum(
            clean_number(
                r.get(
                    "Conversions",
                    0,
                )
            )
            for r in day_records
        )

        value = sum(
            clean_number(
                r.get(
                    "Appointment Value",
                    0,
                )
            )
            for r in day_records
        )

        daily_rows.append(
            {
                "Date":
                    day.strftime(
                        "%d %b"
                    ),

                "Received":
                    len(
                        day_records
                    ),

                "Pending":
                    len(outlets)
                    - len(
                        day_records
                    ),

                "Guests":
                    guests,

                "Conversions":
                    conversions,

                "Appointment Value":
                    value,
            }
        )

    for code, name in (
        outlets.items()
    ):

        received_dates = []

        missing_dates = []

        guests = 0

        conversions = 0

        value = 0

        for day in all_dates:

            record = (
                unique.get(
                    (
                        day.isoformat(),
                        code,
                    )
                )
            )

            if record:

                received_dates.append(
                    day
                )

                guests += (
                    clean_number(
                        record.get(
                            "Guests Interacted",
                            0,
                        )
                    )
                )

                conversions += (
                    clean_number(
                        record.get(
                            "Conversions",
                            0,
                        )
                    )
                )

                value += (
                    clean_number(
                        record.get(
                            "Appointment Value",
                            0,
                        )
                    )
                )

            else:

                missing_dates.append(
                    day
                )

        outlet_rows.append(
            {
                "Code":
                    code,

                "Outlet":
                    name,

                "Received":
                    len(
                        received_dates
                    ),

                "Pending":
                    len(
                        missing_dates
                    ),

                "Guests":
                    guests,

                "Conversions":
                    conversions,

                "Appointment Value":
                    value,

                "Missing Dates":
                    ", ".join(
                        d.strftime(
                            "%d-%b"
                        )
                        for d
                        in missing_dates
                    )
                    if missing_dates
                    else "Complete",
            }
        )

    return (
        pd.DataFrame(
            outlet_rows
        ),

        pd.DataFrame(
            daily_rows
        ),

        duplicate_count,
    )


# ============================================================
# CONNECT TO FINORA DATA
# ============================================================

try:

    outlets = (
        load_outlet_master()
    )

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

        st.code(
            str(error)
        )

    st.stop()


# ============================================================
# LOBBY ACTIVITY HERO
# ============================================================

st.markdown(
    """
<div class="page-hero">

    <div class="hero-eyebrow">
        FINORA WORKSPACE
    </div>

    <div class="hero-title">
        Lobby Activity
    </div>

    <div class="hero-text">
        Capture daily outlet activity,
        monitor performance and follow up
        pending submissions from one place.
    </div>

</div>
""",
    unsafe_allow_html=True,
)


# ============================================================
# LOBBY NAVIGATION
# ============================================================

entry_tab, daily_tab, period_tab = (
    st.tabs(
        [
            "✍️  Enter Activity",
            "📊  Daily Dashboard",
            "📅  Period Dashboard",
        ]
    )
)


# ============================================================
# ENTER ACTIVITY
# ============================================================

with entry_tab:

    st.markdown(
        """
<div class="section-title">
    Enter Lobby Activity
</div>

<div class="section-subtitle">
    Paste the activity received from WhatsApp.
    FINORA will identify the outlet and save
    the information to the dashboard.
</div>
""",
        unsafe_allow_html=True,
    )

    left, right = (
        st.columns(
            [1, 2],
            gap="large",
        )
    )

    with left:

        activity_date = (
            st.date_input(
                "Activity Date",
                value=date.today(),
                format="DD/MM/YYYY",
            )
        )

        uploaded_photo = (
            st.file_uploader(
                "Optional Photo",
                type=[
                    "jpg",
                    "jpeg",
                    "png",
                ],
            )
        )

        if uploaded_photo:

            st.info(
                "Photo received temporarily. "
                "FINORA does not save the photo "
                "or a photo link."
            )

        else:

            st.caption(
                "Photos are not stored by FINORA."
            )

    with right:

        whatsapp_text = (
            st.text_area(
                "Paste WhatsApp Activity",
                height=230,
                placeholder=(
                    "JIAL-Lobby Activity\n\n"
                    "Therapist: Neha\n"
                    "Shift Timings: 1 PM to 10 PM\n"
                    "Guests Interacted: 5\n"
                    "Conversions: 2\n"
                    "Appointment Value: 7918"
                ),
            )
        )

    if st.button(
        "✨  Read & Save Activity",
        type="primary",
        use_container_width=True,
    ):

        if not (
            whatsapp_text.strip()
        ):

            st.error(
                "Please paste the WhatsApp "
                "activity first."
            )

        else:

            parsed = (
                parse_activity(
                    whatsapp_text,
                    outlets,
                )
            )

            if not (
                parsed[
                    "Outlet Code"
                ]
            ):

                st.error(
                    "FINORA could not recognise "
                    "the outlet. Please make sure "
                    "the outlet code is included "
                    "in the message."
                )

            else:

                action, removed = (
                    save_activity(
                        activity_date,
                        parsed,
                        outlets,
                    )
                )

                if (
                    action
                    == "saved"
                ):

                    st.success(
                        "✅ Activity saved successfully — "
                        f"{parsed['Outlet Code']} • "
                        f"{parsed['Outlet Name']}"
                    )

                else:

                    st.success(
                        "🔄 Existing activity updated — "
                        f"{parsed['Outlet Code']} • "
                        f"{parsed['Outlet Name']}"
                    )

                if removed:

                    st.info(
                        f"{removed} duplicate "
                        f"record(s) were removed."
                    )

                a, b, c, d = (
                    st.columns(4)
                )

                a.metric(
                    "Outlet",
                    parsed[
                        "Outlet Code"
                    ],
                )

                b.metric(
                    "Guests",
                    parsed[
                        "Guests Interacted"
                    ],
                )

                c.metric(
                    "Conversions",
                    parsed[
                        "Conversions"
                    ],
                )

                d.metric(
                    "Appointment Value",
                    money(
                        parsed[
                            "Appointment Value"
                        ]
                    ),
                )


# ============================================================
# DAILY DASHBOARD
# ============================================================

with daily_tab:

    st.markdown(
        """
<div class="section-title">
    Daily Dashboard
</div>

<div class="section-subtitle">
    See today's submissions, performance
    and the outlets requiring follow-up.
</div>
""",
        unsafe_allow_html=True,
    )

    date_col, spacer = (
        st.columns(
            [1, 3]
        )
    )

    with date_col:

        selected_date = (
            st.date_input(
                "Select Date",
                value=date.today(),
                format="DD/MM/YYYY",
                key="daily_date",
            )
        )

    daily, duplicate_count = (
        daily_activity(
            selected_date,
            outlets,
        )
    )

    received_codes = list(
        daily.keys()
    )

    pending_codes = [
        code
        for code in outlets
        if code not in daily
    ]

    total_guests = sum(
        clean_number(
            record.get(
                "Guests Interacted",
                0,
            )
        )
        for record
        in daily.values()
    )

    total_conversions = sum(
        clean_number(
            record.get(
                "Conversions",
                0,
            )
        )
        for record
        in daily.values()
    )

    total_value = sum(
        clean_number(
            record.get(
                "Appointment Value",
                0,
            )
        )
        for record
        in daily.values()
    )

    conversion_rate = (
        (
            total_conversions
            / total_guests
        )
        * 100
        if total_guests
        else 0
    )

    st.markdown(
        f"""
<div style="
    font-size:19px;
    font-weight:750;
    color:#27445e;
    margin:10px 0 14px 0;
">
    {selected_date.strftime('%d %B %Y')}
</div>
""",
        unsafe_allow_html=True,
    )

    k1, k2, k3, k4, k5, k6, k7 = (
        st.columns(7)
    )

    k1.metric(
        "Total Outlets",
        len(outlets),
    )

    k2.metric(
        "Received",
        len(received_codes),
    )

    k3.metric(
        "Pending",
        len(pending_codes),
    )

    k4.metric(
        "Guests",
        int(total_guests),
    )

    k5.metric(
        "Conversions",
        int(total_conversions),
    )

    k6.metric(
        "Conversion %",
        f"{conversion_rate:.1f}%",
    )

    k7.metric(
        "Appointment Value",
        money(
            total_value
        ),
    )

    st.write("")

    # --------------------------------------------------------
    # STATUS + PENDING
    # --------------------------------------------------------

    status_column, pending_column = (
        st.columns(
            [0.85, 2.15],
            gap="large",
        )
    )

    with status_column:

        st.markdown(
            f"""
<div class="fin-card">

    <div class="fin-card-title">
        Submission Status
    </div>

    <div class="status-wrap">

        <div class="received-card">

            <div class="status-big"
                 style="color:#087052;">
                {len(received_codes)}
            </div>

            <div class="status-small"
                 style="color:#087052;">
                RECEIVED
            </div>

        </div>

        <div class="pending-card">

            <div class="status-big"
                 style="color:#b23e3e;">
                {len(pending_codes)}
            </div>

            <div class="status-small"
                 style="color:#b23e3e;">
                PENDING
            </div>

        </div>

    </div>

</div>
""",
            unsafe_allow_html=True,
        )

    with pending_column:

        st.markdown(
            """
<div class="fin-card">

    <div class="fin-card-title">
        🔴 Pending Follow-up
    </div>
""",
            unsafe_allow_html=True,
        )

        if pending_codes:

            pending_html = "".join(
                (
                    '<span class="outlet-pill '
                    'pending-pill">'
                    f'{code} • {outlets[code]}'
                    '</span>'
                )
                for code
                in pending_codes
            )

            st.markdown(
                pending_html,
                unsafe_allow_html=True,
            )

        else:

            st.success(
                "All outlets have submitted. 🎉"
            )

        st.markdown(
            "</div>",
            unsafe_allow_html=True,
        )

    # --------------------------------------------------------
    # RECEIVED OUTLETS
    # --------------------------------------------------------

    if received_codes:

        st.markdown(
            """
<div class="fin-card">

    <div class="fin-card-title">
        🟢 Received Outlets
    </div>
""",
            unsafe_allow_html=True,
        )

        received_html = "".join(
            (
                '<span class="outlet-pill '
                'received-pill">'
                f'{code} • {outlets[code]}'
                '</span>'
            )
            for code
            in received_codes
        )

        st.markdown(
            received_html,
            unsafe_allow_html=True,
        )

        st.markdown(
            "</div>",
            unsafe_allow_html=True,
        )

    # --------------------------------------------------------
    # PERFORMANCE CHARTS
    # --------------------------------------------------------

    if daily:

        performance_rows = []

        for code, record in (
            daily.items()
        ):

            performance_rows.append(
                {
                    "Outlet":
                        code,

                    "Guests":
                        clean_number(
                            record.get(
                                "Guests Interacted",
                                0,
                            )
                        ),

                    "Conversions":
                        clean_number(
                            record.get(
                                "Conversions",
                                0,
                            )
                        ),

                    "Appointment Value":
                        clean_number(
                            record.get(
                                "Appointment Value",
                                0,
                            )
                        ),
                }
            )

        performance_df = (
            pd.DataFrame(
                performance_rows
            )
        )

        chart1, chart2 = (
            st.columns(
                2,
                gap="large",
            )
        )

        with chart1:

            st.markdown(
                "### 👥 Guests vs Conversions"
            )

            st.bar_chart(
                performance_df
                .set_index(
                    "Outlet"
                )[
                    [
                        "Guests",
                        "Conversions",
                    ]
                ],
                height=280,
            )

        with chart2:

            st.markdown(
                "### 💰 Appointment Value"
            )

            value_df = (
                performance_df[
                    [
                        "Outlet",
                        "Appointment Value",
                    ]
                ]
                .sort_values(
                    "Appointment Value",
                    ascending=False,
                )
                .set_index(
                    "Outlet"
                )
            )

            st.bar_chart(
                value_df,
                height=280,
            )

    # --------------------------------------------------------
    # WHATSAPP FOLLOW-UP
    # --------------------------------------------------------

    st.markdown(
        "### 💬 WhatsApp Follow-up"
    )

    pending_text = (
        ", ".join(
            pending_codes
        )
        if pending_codes
        else "None"
    )

    summary = (
        f"FINORA Lobby Activity | "
        f"{selected_date.strftime('%d %b %Y')}\n"
        f"Received: "
        f"{len(received_codes)}/{len(outlets)} | "
        f"Pending: {len(pending_codes)}\n"
        f"Guests: {int(total_guests)} | "
        f"Conversions: {int(total_conversions)} | "
        f"Conversion: {conversion_rate:.1f}%\n"
        f"Appointment Value: {money(total_value)}\n"
        f"Pending Outlets: {pending_text}"
    )

    st.markdown(
        f"""
<div class="whatsapp-box">
{summary}
</div>
""",
        unsafe_allow_html=True,
    )

    # --------------------------------------------------------
    # DETAILS
    # --------------------------------------------------------

    with st.expander(
        "📋 View complete outlet-wise details"
    ):

        rows = []

        for code, name in (
            outlets.items()
        ):

            record = (
                daily.get(
                    code
                )
            )

            if record:

                rows.append(
                    {
                        "Code":
                            code,

                        "Outlet":
                            name,

                        "Status":
                            "Received",

                        "Therapist":
                            record.get(
                                "Therapist",
                                "",
                            ),

                        "Shift":
                            record.get(
                                "Shift Timings",
                                "",
                            ),

                        "Guests":
                            clean_number(
                                record.get(
                                    "Guests Interacted",
                                    0,
                                )
                            ),

                        "Conversions":
                            clean_number(
                                record.get(
                                    "Conversions",
                                    0,
                                )
                            ),

                        "Appointment Value":
                            clean_number(
                                record.get(
                                    "Appointment Value",
                                    0,
                                )
                            ),
                    }
                )

            else:

                rows.append(
                    {
                        "Code":
                            code,

                        "Outlet":
                            name,

                        "Status":
                            "Pending",

                        "Therapist":
                            "",

                        "Shift":
                            "",

                        "Guests":
                            "",

                        "Conversions":
                            "",

                        "Appointment Value":
                            "",
                    }
                )

        st.dataframe(
            pd.DataFrame(
                rows
            ),
            use_container_width=True,
            hide_index=True,
            height=470,
        )

    if duplicate_count:

        st.caption(
            f"FINORA ignored "
            f"{duplicate_count} duplicate "
            f"historical record(s) while "
            f"calculating this dashboard."
        )


# ============================================================
# PERIOD DASHBOARD
# ============================================================

with period_tab:

    st.markdown(
        """
<div class="section-title">
    Period Dashboard
</div>

<div class="section-subtitle">
    Analyse lobby activity across a selected
    period and identify the exact missing
    dates for each outlet.
</div>
""",
        unsafe_allow_html=True,
    )

    d1, d2, blank = (
        st.columns(
            [1, 1, 2]
        )
    )

    with d1:

        start_date = (
            st.date_input(
                "From Date",
                value=date.today(),
                format="DD/MM/YYYY",
                key="period_from",
            )
        )

    with d2:

        end_date = (
            st.date_input(
                "To Date",
                value=date.today(),
                format="DD/MM/YYYY",
                key="period_to",
            )
        )

    if (
        end_date
        < start_date
    ):

        st.error(
            "To Date cannot be "
            "before From Date."
        )

    else:

        (
            outlet_df,
            daily_df,
            period_duplicates,
        ) = period_activity(
            start_date,
            end_date,
            outlets,
        )

        days = (
            end_date
            - start_date
        ).days + 1

        expected = (
            days
            * len(outlets)
        )

        received = int(
            outlet_df[
                "Received"
            ].sum()
        )

        pending = (
            expected
            - received
        )

        guests = int(
            outlet_df[
                "Guests"
            ].sum()
        )

        conversions = int(
            outlet_df[
                "Conversions"
            ].sum()
        )

        total_value = float(
            outlet_df[
                "Appointment Value"
            ].sum()
        )

        conversion_rate = (
            (
                conversions
                / guests
            )
            * 100
            if guests
            else 0
        )

        p1, p2, p3, p4, p5, p6, p7 = (
            st.columns(7)
        )

        p1.metric(
            "Days",
            days,
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
            guests,
        )

        p6.metric(
            "Conversion %",
            f"{conversion_rate:.1f}%",
        )

        p7.metric(
            "Appointment Value",
            money(
                total_value
            ),
        )

        # ----------------------------------------------------
        # PERIOD CHARTS
        # ----------------------------------------------------

        if not daily_df.empty:

            chart1, chart2 = (
                st.columns(
                    2,
                    gap="large",
                )
            )

            with chart1:

                st.markdown(
                    "### 📊 Submission Trend"
                )

                st.line_chart(
                    daily_df
                    .set_index(
                        "Date"
                    )[
                        [
                            "Received",
                            "Pending",
                        ]
                    ],
                    height=280,
                )

            with chart2:

                st.markdown(
                    "### 👥 Guests & Conversions"
                )

                st.line_chart(
                    daily_df
                    .set_index(
                        "Date"
                    )[
                        [
                            "Guests",
                            "Conversions",
                        ]
                    ],
                    height=280,
                )

            st.markdown(
                "### 💰 Appointment Value Trend"
            )

            st.line_chart(
                daily_df
                .set_index(
                    "Date"
                )[
                    [
                        "Appointment Value"
                    ]
                ],
                height=240,
            )

        # ----------------------------------------------------
        # PENDING DETAILS
        # ----------------------------------------------------

        pending_df = (
            outlet_df[
                outlet_df[
                    "Pending"
                ] > 0
            ]
            .copy()
        )

        st.markdown(
            f"### 🔴 Follow-up Required "
            f"({len(pending_df)} outlets)"
        )

        if pending_df.empty:

            st.success(
                "All lobby activities are "
                "complete for this period. 🎉"
            )

        else:

            st.dataframe(
                pending_df[
                    [
                        "Code",
                        "Outlet",
                        "Received",
                        "Pending",
                        "Missing Dates",
                    ]
                ],
                use_container_width=True,
                hide_index=True,
                height=360,
            )

        with st.expander(
            "📋 View complete period performance"
        ):

            st.dataframe(
                outlet_df,
                use_container_width=True,
                hide_index=True,
                height=470,
            )

        if period_duplicates:

            st.caption(
                f"FINORA ignored "
                f"{period_duplicates} duplicate "
                f"historical record(s)."
            )


# ============================================================
# FOOTER
# ============================================================

st.markdown(
    """
<div class="finora-footer">
    FINORA • Your Finance AI • Lobby Activity Intelligence
</div>
""",
    unsafe_allow_html=True,
)
