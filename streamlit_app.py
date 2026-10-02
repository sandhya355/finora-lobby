import streamlit as st
import pandas as pd
import re
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import gspread
from google.oauth2.service_account import Credentials


# ============================================================
# PAGE SETUP
# ============================================================

st.set_page_config(
    page_title="FINORA | Lobby Activity",
    page_icon="💠",
    layout="wide",
    initial_sidebar_state="collapsed",
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
# PREMIUM UI
# ============================================================

st.markdown(
    """
<style>

/* ---------- PAGE ---------- */

html, body, [class*="css"] {
    font-family: Inter, Arial, sans-serif;
}

.stApp {
    background: #f5f8fb;
}

.block-container {
    max-width: 1380px;
    padding-top: 24px;
    padding-left: 32px;
    padding-right: 32px;
    padding-bottom: 50px;
}


/* ---------- HEADER ---------- */

.finora-hero {
    width: 100%;
    box-sizing: border-box;

    background:
        linear-gradient(
            120deg,
            #08233d 0%,
            #0b3d55 55%,
            #08766f 100%
        );

    border-radius: 22px;

    padding: 34px 30px 30px 30px;

    text-align: center;

    margin-bottom: 18px;

    box-shadow:
        0 12px 30px
        rgba(8, 35, 61, 0.14);
}

.finora-logo {
    color: #ffffff !important;
    font-size: 44px !important;
    font-weight: 800 !important;
    letter-spacing: 4px !important;
    line-height: 1.1 !important;
    margin: 0 !important;
    padding: 0 !important;
}

.finora-tagline {
    color: #d7f5ef !important;
    font-size: 16px !important;
    font-weight: 500 !important;
    margin-top: 10px !important;
}


/* ---------- SECTION TITLES ---------- */

.page-title {
    color: #102a43;
    font-size: 28px;
    font-weight: 750;
    margin-top: 15px;
    margin-bottom: 4px;
}

.page-subtitle {
    color: #718096;
    font-size: 14px;
    margin-bottom: 20px;
}


/* ---------- TABS ---------- */

div[data-baseweb="tab-list"] {
    gap: 8px;
    border-bottom: 1px solid #dfe7ed;
}

button[data-baseweb="tab"] {
    height: 50px;
    padding-left: 20px !important;
    padding-right: 20px !important;
    border-radius: 10px 10px 0 0;
    font-size: 14px !important;
    font-weight: 650 !important;
}

button[data-baseweb="tab"][aria-selected="true"] {
    color: #08766f !important;
    background: #eaf6f4 !important;
}


/* ---------- FORM CARDS ---------- */

.form-card {
    background: white;
    border: 1px solid #e1e8ee;
    border-radius: 18px;
    padding: 20px 22px;
    margin-bottom: 16px;

    box-shadow:
        0 4px 14px
        rgba(15, 40, 65, 0.05);
}


/* ---------- INPUTS ---------- */

div[data-baseweb="input"] {
    border-radius: 10px !important;
}

textarea {
    border-radius: 12px !important;
    font-size: 15px !important;
}

div[data-testid="stFileUploader"] section {
    border-radius: 12px;
}


/* ---------- BUTTON ---------- */

div.stButton > button[kind="primary"] {
    width: 100%;
    min-height: 50px;

    border: none;
    border-radius: 12px;

    background:
        linear-gradient(
            90deg,
            #08766f,
            #11988d
        );

    color: white;

    font-size: 15px;
    font-weight: 700;

    box-shadow:
        0 7px 16px
        rgba(8, 118, 111, 0.18);
}

div.stButton > button[kind="primary"]:hover {
    color: white;
    border: none;
    background:
        linear-gradient(
            90deg,
            #066861,
            #0d877d
        );
}


/* ---------- KPI CARDS ---------- */

div[data-testid="stMetric"] {
    background: #ffffff;

    border:
        1px solid #e1e8ee;

    border-radius:
        15px;

    padding:
        14px 15px;

    min-height:
        100px;

    box-shadow:
        0 4px 12px
        rgba(15, 40, 65, 0.045);
}

div[data-testid="stMetricLabel"] {
    color: #718096;
    font-size: 12px;
    font-weight: 650;
}

div[data-testid="stMetricValue"] {
    color: #102a43;
    font-size: 25px;
    font-weight: 750;
}


/* ---------- DASHBOARD CARDS ---------- */

.dashboard-card {
    background: white;

    border:
        1px solid #e1e8ee;

    border-radius:
        17px;

    padding:
        18px;

    margin-top:
        8px;

    margin-bottom:
        12px;

    box-shadow:
        0 4px 14px
        rgba(15, 40, 65, 0.045);
}

.card-title {
    color: #102a43;
    font-size: 17px;
    font-weight: 750;
    margin-bottom: 10px;
}


/* ---------- STATUS PILLS ---------- */

.outlet-pill {
    display: inline-block;

    padding:
        6px 10px;

    margin:
        4px 3px;

    border-radius:
        20px;

    font-size:
        12px;

    font-weight:
        650;
}

.pending-pill {
    color: #9b2c2c;
    background: #fff1f1;
    border: 1px solid #ffd5d5;
}

.received-pill {
    color: #12664f;
    background: #eaf8f3;
    border: 1px solid #c9ecdf;
}


/* ---------- STATUS COUNTERS ---------- */

.status-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
}

.status-stat {
    padding: 17px;
    border-radius: 14px;
    text-align: center;
}

.status-received {
    background: #eaf8f3;
    color: #12664f;
}

.status-pending {
    background: #fff1f1;
    color: #a33939;
}

.status-number {
    font-size: 32px;
    font-weight: 800;
    line-height: 1;
}

.status-label {
    font-size: 12px;
    font-weight: 650;
    margin-top: 6px;
}


/* ---------- TABLE ---------- */

div[data-testid="stDataFrame"] {
    border:
        1px solid #e1e8ee;

    border-radius:
        14px;

    overflow:
        hidden;
}


/* ---------- ALERT ---------- */

div[data-testid="stAlert"] {
    border-radius: 12px;
}


/* ---------- EXPANDER ---------- */

div[data-testid="stExpander"] {
    background: white;
    border: 1px solid #e1e8ee;
    border-radius: 14px;
}


/* ---------- MOBILE ---------- */

@media (max-width: 800px) {

    .block-container {
        padding-left: 14px;
        padding-right: 14px;
        padding-top: 14px;
    }

    .finora-hero {
        padding: 27px 16px;
        border-radius: 16px;
    }

    .finora-logo {
        font-size: 35px !important;
    }

    .finora-tagline {
        font-size: 13px !important;
    }

    .status-grid {
        grid-template-columns: 1fr;
    }
}


/* ---------- HIDE STREAMLIT BRANDING ---------- */

#MainMenu {
    visibility: hidden;
}

footer {
    visibility: hidden;
}

</style>
""",
    unsafe_allow_html=True,
)


# ============================================================
# HEADER
# ============================================================

st.markdown(
    """
<div class="finora-hero">
    <div class="finora-logo">FINORA</div>
    <div class="finora-tagline">
        Lobby Activity Intelligence &nbsp;•&nbsp;
        Performance &nbsp;•&nbsp; Monitoring
    </div>
</div>
""",
    unsafe_allow_html=True,
)


# ============================================================
# GOOGLE SHEETS CONNECTION
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
# MESSAGE PARSER
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
# ACTIVITY DATA
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
# SAVE ACTIVITY
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

        for row_number in (
            sorted(
                duplicates,
                reverse=True,
            )
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
# UNIQUE ACTIVITY
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

        day = normalize_date(
            record.get(
                "Date",
                "",
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
# PERIOD ACTIVITY
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

        records = []

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

                records.append(
                    record
                )

        guests = sum(
            clean_number(
                r.get(
                    "Guests Interacted",
                    0,
                )
            )
            for r in records
        )

        conversions = sum(
            clean_number(
                r.get(
                    "Conversions",
                    0,
                )
            )
            for r in records
        )

        value = sum(
            clean_number(
                r.get(
                    "Appointment Value",
                    0,
                )
            )
            for r in records
        )

        daily_rows.append(
            {
                "Date":
                    day.strftime(
                        "%d %b"
                    ),

                "Received":
                    len(records),

                "Pending":
                    len(outlets)
                    - len(records),

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

        received = 0
        missing = []

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

                received += 1

                guests += clean_number(
                    record.get(
                        "Guests Interacted",
                        0,
                    )
                )

                conversions += clean_number(
                    record.get(
                        "Conversions",
                        0,
                    )
                )

                value += clean_number(
                    record.get(
                        "Appointment Value",
                        0,
                    )
                )

            else:

                missing.append(
                    day
                )

        outlet_rows.append(
            {
                "Code":
                    code,

                "Outlet":
                    name,

                "Received":
                    received,

                "Pending":
                    len(missing),

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
                        for d in missing
                    )
                    if missing
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
# CONNECT
# ============================================================

try:

    outlets = (
        load_outlet_master()
    )

    if not outlets:

        st.error(
            "No active outlets "
            "found in Outlet Master."
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
# NAVIGATION
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
<div class="page-title">
    Enter Lobby Activity
</div>
<div class="page-subtitle">
    Paste the outlet's WhatsApp activity.
    FINORA will recognise the outlet and
    update the dashboard automatically.
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
                "Optional photo",
                type=[
                    "jpg",
                    "jpeg",
                    "png",
                ],
            )
        )

        st.caption(
            "Photos are not saved "
            "by FINORA."
        )

    with right:

        whatsapp_text = (
            st.text_area(
                "WhatsApp Activity",
                height=205,
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
        "Read & Save Activity",
        type="primary",
        use_container_width=True,
    ):

        if not (
            whatsapp_text.strip()
        ):

            st.error(
                "Please paste "
                "the activity."
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
                    "FINORA could not "
                    "recognise the outlet code."
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
                        "Activity saved successfully — "
                        f"{parsed['Outlet Code']} | "
                        f"{parsed['Outlet Name']}"
                    )

                else:

                    st.success(
                        "Existing activity updated — "
                        f"{parsed['Outlet Code']} | "
                        f"{parsed['Outlet Name']}"
                    )

                if removed:

                    st.info(
                        f"{removed} duplicate "
                        f"record(s) removed."
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
<div class="page-title">
    Daily Lobby Dashboard
</div>
<div class="page-subtitle">
    Daily submission status,
    outlet performance and pending follow-up.
</div>
""",
        unsafe_allow_html=True,
    )

    date_col, blank = (
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
        for record in (
            daily.values()
        )
    )

    total_conversions = sum(
        clean_number(
            record.get(
                "Conversions",
                0,
            )
        )
        for record in (
            daily.values()
        )
    )

    total_value = sum(
        clean_number(
            record.get(
                "Appointment Value",
                0,
            )
        )
        for record in (
            daily.values()
        )
    )

    conversion_rate = (
        total_conversions
        / total_guests
        * 100
        if total_guests
        else 0
    )

    k1, k2, k3, k4, k5, k6, k7 = (
        st.columns(7)
    )

    k1.metric(
        "Outlets",
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
        "Conversion",
        f"{conversion_rate:.1f}%",
    )

    k7.metric(
        "Appointment",
        money(total_value),
    )

    st.write("")

    status_col, follow_col = (
        st.columns(
            [0.8, 2.2],
            gap="large",
        )
    )

    with status_col:

        st.markdown(
            """
<div class="dashboard-card">
<div class="card-title">
Submission Status
</div>
""",
            unsafe_allow_html=True,
        )

        st.markdown(
            f"""
<div class="status-grid">

<div class="status-stat status-received">
<div class="status-number">
{len(received_codes)}
</div>
<div class="status-label">
RECEIVED
</div>
</div>

<div class="status-stat status-pending">
<div class="status-number">
{len(pending_codes)}
</div>
<div class="status-label">
PENDING
</div>
</div>

</div>
</div>
""",
            unsafe_allow_html=True,
        )

    with follow_col:

        st.markdown(
            f"""
<div class="dashboard-card">
<div class="card-title">
Pending Follow-up
</div>
""",
            unsafe_allow_html=True,
        )

        if pending_codes:

            pills = "".join(
                (
                    '<span class="outlet-pill '
                    'pending-pill">'
                    f'{code} · {outlets[code]}'
                    '</span>'
                )
                for code
                in pending_codes
            )

            st.markdown(
                pills,
                unsafe_allow_html=True,
            )

        else:

            st.success(
                "All outlets have submitted."
            )

        st.markdown(
            "</div>",
            unsafe_allow_html=True,
        )

    # ---------------- PERFORMANCE ----------------

    if daily:

        performance = []

        for code, record in (
            daily.items()
        ):

            performance.append(
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
                performance
            )
        )

        chart_left, chart_right = (
            st.columns(
                2,
                gap="large",
            )
        )

        with chart_left:

            st.markdown(
                "#### Guests vs Conversions"
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
                height=250,
            )

        with chart_right:

            st.markdown(
                "#### Appointment Value"
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
                height=250,
            )

    # ---------------- WHATSAPP SUMMARY ----------------

    st.markdown(
        "#### WhatsApp Follow-up"
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
        f"{selected_date.strftime('%d %b %Y')}\n\n"
        f"Received: "
        f"{len(received_codes)}/{len(outlets)}\n"
        f"Pending: {len(pending_codes)}\n"
        f"Guests: {int(total_guests)}\n"
        f"Conversions: {int(total_conversions)}\n"
        f"Conversion Rate: "
        f"{conversion_rate:.1f}%\n"
        f"Appointment Value: "
        f"{money(total_value)}\n\n"
        f"Pending Outlets: "
        f"{pending_text}"
    )

    st.code(
        summary,
        language=None,
    )

    # ---------------- DETAILS ----------------

    with st.expander(
        "View outlet-wise details"
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
            height=430,
        )

    if duplicate_count:

        st.caption(
            f"{duplicate_count} duplicate "
            f"historical record(s) were "
            f"ignored in the totals."
        )


# ============================================================
# PERIOD DASHBOARD
# ============================================================

with period_tab:

    st.markdown(
        """
<div class="page-title">
    Period Dashboard
</div>
<div class="page-subtitle">
    Review outlet submissions and performance
    across a selected date range.
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

        rate = (
            conversions
            / guests
            * 100
            if guests
            else 0
        )

        p1, p2, p3, p4, p5, p6 = (
            st.columns(6)
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
            "Conversion",
            f"{rate:.1f}%",
        )

        p6.metric(
            "Appointment",
            money(
                total_value
            ),
        )

        if not daily_df.empty:

            trend1, trend2 = (
                st.columns(
                    2,
                    gap="large",
                )
            )

            with trend1:

                st.markdown(
                    "#### Submission Trend"
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
                    height=260,
                )

            with trend2:

                st.markdown(
                    "#### Guests vs Conversions"
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
                    height=260,
                )

        pending_df = (
            outlet_df[
                outlet_df[
                    "Pending"
                ] > 0
            ]
        )

        st.markdown(
            f"#### Pending Follow-up "
            f"({len(pending_df)} outlets)"
        )

        if pending_df.empty:

            st.success(
                "No pending activity "
                "for this period."
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
                height=330,
            )

        with st.expander(
            "View complete period details"
        ):

            st.dataframe(
                outlet_df,
                use_container_width=True,
                hide_index=True,
                height=430,
            )

        if period_duplicates:

            st.caption(
                f"{period_duplicates} "
                f"duplicate historical "
                f"record(s) were ignored."
            )


# ============================================================
# FOOTER
# ============================================================

st.markdown(
    """
<br>
<div style="
    text-align:center;
    color:#94a3b8;
    font-size:12px;
    padding:15px;
">
    FINORA • Lobby Activity Intelligence
</div>
""",
    unsafe_allow_html=True,
)
