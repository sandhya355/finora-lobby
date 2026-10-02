import streamlit as st
import pandas as pd
import re
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import gspread
from google.oauth2.service_account import Credentials


# ============================================================
# FINORA CONFIGURATION
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
# DESIGN
# ============================================================

st.markdown(
    """
<style>

/* Compact centered dashboard */
.block-container {
    max-width: 1250px;
    padding-top: 0.8rem;
    padding-bottom: 2rem;
}

/* Header */
.finora-header {
    background: linear-gradient(120deg,#08223b,#0b5961);
    padding: 18px 24px;
    border-radius: 16px;
    margin-bottom: 12px;
}

.finora-title {
    color: white;
    font-size: 30px;
    font-weight: 800;
    margin: 0;
}

.finora-subtitle {
    color: #d9f5f1;
    font-size: 14px;
    margin-top: 3px;
}

/* Reduce whitespace */
h1, h2, h3 {
    margin-top: 0.5rem !important;
    margin-bottom: 0.5rem !important;
}

/* Compact metrics */
div[data-testid="stMetric"] {
    border: 1px solid #e5e7eb;
    background: white;
    padding: 9px 12px;
    border-radius: 12px;
    min-height: 85px;
}

div[data-testid="stMetricLabel"] {
    font-size: 12px;
}

div[data-testid="stMetricValue"] {
    font-size: 23px;
}

/* Status boxes */
.status-box {
    border: 1px solid #e5e7eb;
    border-radius: 14px;
    padding: 14px 16px;
    background: white;
    margin-bottom: 10px;
}

.pending-box {
    border-left: 5px solid #e24a4a;
}

.received-box {
    border-left: 5px solid #25a56a;
}

.small-title {
    font-size: 16px;
    font-weight: 700;
    margin-bottom: 7px;
}

.code-pill {
    display: inline-block;
    padding: 4px 9px;
    margin: 3px;
    border-radius: 12px;
    background: #f3f4f6;
    font-size: 12px;
    font-weight: 600;
}

/* Make dataframe area compact */
div[data-testid="stDataFrame"] {
    border-radius: 10px;
}

/* Hide Streamlit decoration */
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

st.markdown(
    """
<div class="finora-header">
    <div class="finora-title">FINORA</div>
    <div class="finora-subtitle">
        Lobby Activity • Outlet Monitoring Dashboard
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
        st.secrets["google_service_account"]
    )

    credentials = Credentials.from_service_account_info(
        info,
        scopes=[
            "https://www.googleapis.com/auth/spreadsheets"
        ],
    )

    client = gspread.authorize(credentials)

    return client.open_by_key(
        st.secrets["spreadsheet_id"]
    )


def get_activity_sheet():
    return get_spreadsheet().worksheet(
        ACTIVITY_SHEET
    )


def get_master_sheet():
    return get_spreadsheet().worksheet(
        OUTLET_MASTER_SHEET
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

    number = float(match.group())

    return (
        int(number)
        if number.is_integer()
        else number
    )


def money(value):

    try:
        return f"₹{float(value):,.0f}"
    except Exception:
        return "₹0"


def normalize_date(value):

    text = str(value).strip()

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
            return datetime.strptime(
                text,
                fmt,
            ).date().isoformat()

        except ValueError:
            pass

    try:
        return pd.to_datetime(
            text,
            dayfirst=True,
        ).date().isoformat()

    except Exception:
        return text


def now_ist():

    return datetime.now(
        ZoneInfo("Asia/Kolkata")
    ).strftime(
        "%Y-%m-%d %H:%M:%S"
    )


# ============================================================
# OUTLET MASTER
# ============================================================

def load_outlet_master():

    worksheet = get_master_sheet()

    # Only A:C are required.
    values = worksheet.get("A:C")

    outlets = {}

    if len(values) < 2:
        return outlets

    for row in values[1:]:

        row = row + [""] * (
            3 - len(row)
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
# WHATSAPP PARSER
# ============================================================

def extract_field(text, labels):

    for label in labels:

        pattern = (
            rf"(?im)^\s*"
            rf"{re.escape(label)}"
            rf"\s*[:\-]\s*(.*?)\s*$"
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


def detect_outlet(text, outlets):

    upper = text.upper()

    # Detect outlet code first
    for code, name in outlets.items():

        if re.search(
            rf"(?<![A-Z0-9])"
            rf"{re.escape(code)}"
            rf"(?![A-Z0-9])",
            upper,
        ):
            return code, name

    # Then outlet name
    for code, name in outlets.items():

        if name.upper() in upper:
            return code, name

    return None, None


def parse_activity(text, outlets):

    code, name = detect_outlet(
        text,
        outlets,
    )

    return {
        "Outlet Code": code,
        "Outlet Name": name,

        "Therapist": extract_field(
            text,
            [
                "Therapist",
                "Therapist Name",
                "Name of Therapist",
                "Staff",
            ],
        ),

        "Shift Timings": extract_field(
            text,
            [
                "Shift",
                "Shift Timing",
                "Shift Timings",
                "Timing",
                "Timings",
            ],
        ),

        "Guests Interacted": clean_number(
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

        "Conversions": clean_number(
            extract_field(
                text,
                [
                    "Conversions",
                    "Conversion",
                    "Converted",
                ],
            )
        ),

        "Appointment Value": clean_number(
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
# ACTIVITY SHEET
# ============================================================

def read_activity():

    worksheet = get_activity_sheet()

    values = worksheet.get(
        "A:H"
    )

    if not values:

        worksheet.append_row(
            ACTIVITY_HEADERS
        )
        return []

    records = []

    # Use our fixed expected column order instead of
    # depending on blank/duplicate Sheet headers.
    for row_number, row in enumerate(
        values[1:],
        start=2,
    ):

        if not any(row):
            continue

        row = row + [""] * (
            8 - len(row)
        )

        record = {
            ACTIVITY_HEADERS[i]: row[i]
            for i in range(8)
        }

        record["_row"] = row_number

        records.append(record)

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

    for code, name in outlets.items():

        if name.upper() == upper:
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

    worksheet = get_activity_sheet()

    records = read_activity()

    target_date = (
        activity_date.isoformat()
    )

    target_code = parsed[
        "Outlet Code"
    ]

    matches = []

    for record in records:

        record_date = normalize_date(
            record.get(
                "Date",
                "",
            )
        )

        record_code = sheet_outlet_code(
            record.get(
                "Outlet",
                "",
            ),
            outlets,
        )

        if (
            record_date
            == target_date
            and record_code
            == target_code
        ):
            matches.append(
                record["_row"]
            )

    values = [
        target_date,
        f"{target_code}-Lobby",
        parsed["Therapist"],
        parsed["Shift Timings"],
        parsed["Guests Interacted"],
        parsed["Conversions"],
        parsed["Appointment Value"],
        now_ist(),
    ]

    if matches:

        main_row = matches[0]

        worksheet.update(
            range_name=(
                f"A{main_row}:H{main_row}"
            ),
            values=[values],
        )

        duplicates = matches[1:]

        # Delete from bottom upwards.
        for row_number in sorted(
            duplicates,
            reverse=True,
        ):
            worksheet.delete_rows(
                row_number
            )

        return (
            "updated",
            len(duplicates),
        )

    worksheet.append_row(
        values,
        value_input_option=(
            "USER_ENTERED"
        ),
    )

    return "saved", 0


# ============================================================
# DEDUPED ACTIVITY
# ============================================================

def build_unique_activity(outlets):

    records = read_activity()

    unique = {}

    duplicates = 0

    for record in records:

        day = normalize_date(
            record.get(
                "Date",
                "",
            )
        )

        code = sheet_outlet_code(
            record.get(
                "Outlet",
                "",
            ),
            outlets,
        )

        if not day or not code:
            continue

        key = (
            day,
            code,
        )

        if key in unique:
            duplicates += 1

        # Later row wins.
        unique[key] = record

    return unique, duplicates


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
        selected_date.isoformat()
    )

    daily = {}

    for (
        record_date,
        code,
    ), record in unique.items():

        if record_date == target:
            daily[code] = record

    return daily, duplicates


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

    while current <= end_date:

        all_dates.append(
            current
        )

        current += timedelta(
            days=1
        )

    outlet_rows = []

    daily_rows = []

    for day in all_dates:

        day_key = (
            day.isoformat()
        )

        day_records = []

        for code in outlets:

            record = unique.get(
                (
                    day_key,
                    code,
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

        appointment = sum(
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
                    len(day_records),
                "Pending":
                    len(outlets)
                    - len(day_records),
                "Guests":
                    guests,
                "Conversions":
                    conversions,
                "Appointment Value":
                    appointment,
            }
        )

    for code, name in outlets.items():

        received_dates = []

        missing_dates = []

        guests = 0
        conversions = 0
        appointment = 0

        for day in all_dates:

            record = unique.get(
                (
                    day.isoformat(),
                    code,
                )
            )

            if record:

                received_dates.append(
                    day
                )

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

                appointment += clean_number(
                    record.get(
                        "Appointment Value",
                        0,
                    )
                )

            else:

                missing_dates.append(
                    day
                )

        outlet_rows.append(
            {
                "Code": code,
                "Outlet": name,
                "Received":
                    len(received_dates),
                "Pending":
                    len(missing_dates),
                "Guests":
                    guests,
                "Conversions":
                    conversions,
                "Appointment Value":
                    appointment,
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
# CONNECTION
# ============================================================

try:

    outlets = load_outlet_master()

    if not outlets:

        st.error(
            "No active outlets found "
            "in 'Outlet Master'."
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


# ============================================================
# TABS
# ============================================================

entry_tab, daily_tab, period_tab = st.tabs(
    [
        "📝 Enter Activity",
        "📊 Daily Dashboard",
        "📅 Period Dashboard",
    ]
)


# ============================================================
# ENTER ACTIVITY
# ============================================================

with entry_tab:

    st.subheader(
        "Enter Lobby Activity"
    )

    left, right = st.columns(
        [1, 2]
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

        if uploaded_photo:

            st.caption(
                "The photo is temporary. "
                "FINORA does not save the "
                "photo or photo link."
            )

    with right:

        whatsapp_text = (
            st.text_area(
                "Paste WhatsApp Activity",
                height=190,
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
        "✨ Read & Save Activity",
        type="primary",
        use_container_width=True,
    ):

        if not (
            whatsapp_text.strip()
        ):

            st.error(
                "Paste the WhatsApp "
                "activity first."
            )

        else:

            parsed = parse_activity(
                whatsapp_text,
                outlets,
            )

            if not parsed[
                "Outlet Code"
            ]:

                st.error(
                    "FINORA could not "
                    "recognise the outlet. "
                    "Check that the outlet "
                    "code is in the message."
                )

            else:

                action, removed = (
                    save_activity(
                        activity_date,
                        parsed,
                        outlets,
                    )
                )

                if action == "saved":

                    st.success(
                        "✅ Activity saved — "
                        f"{parsed['Outlet Code']} "
                        f"| "
                        f"{parsed['Outlet Name']}"
                    )

                else:

                    st.success(
                        "🔄 Existing activity "
                        "updated — "
                        f"{parsed['Outlet Code']} "
                        f"| "
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

    top1, top2 = st.columns(
        [1, 3]
    )

    with top1:

        selected_date = (
            st.date_input(
                "Dashboard Date",
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
            r.get(
                "Guests Interacted",
                0,
            )
        )
        for r in daily.values()
    )

    total_conversions = sum(
        clean_number(
            r.get(
                "Conversions",
                0,
            )
        )
        for r in daily.values()
    )

    total_value = sum(
        clean_number(
            r.get(
                "Appointment Value",
                0,
            )
        )
        for r in daily.values()
    )

    conversion_rate = (
        total_conversions
        / total_guests
        * 100
        if total_guests
        else 0
    )

    st.markdown(
        f"### {selected_date.strftime('%d %B %Y')}"
    )

    # Compact KPI row
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
        "Conversion %",
        f"{conversion_rate:.1f}%",
    )

    k7.metric(
        "Appt. Value",
        money(total_value),
    )

    # --------------------------------------------------------
    # RECEIVED / PENDING VISUAL
    # --------------------------------------------------------

    left, right = st.columns(
        [1, 2]
    )

    with left:

        st.markdown(
            "#### Submission Status"
        )

        status_df = pd.DataFrame(
            {
                "Status": [
                    "Received",
                    "Pending",
                ],
                "Outlets": [
                    len(received_codes),
                    len(pending_codes),
                ],
            }
        ).set_index(
            "Status"
        )

        # Small compact chart
        st.bar_chart(
            status_df,
            height=210,
        )

    with right:

        st.markdown(
            f"#### 🔴 Pending Today "
            f"({len(pending_codes)})"
        )

        if pending_codes:

            pending_html = "".join(
                (
                    '<span class="code-pill">'
                    f'{code} · {outlets[code]}'
                    '</span>'
                )
                for code
                in pending_codes
            )

            st.markdown(
                (
                    '<div class="status-box '
                    'pending-box">'
                    f'{pending_html}'
                    '</div>'
                ),
                unsafe_allow_html=True,
            )

        else:

            st.success(
                "All outlets have "
                "submitted. 🎉"
            )

        st.markdown(
            f"#### 🟢 Received "
            f"({len(received_codes)})"
        )

        if received_codes:

            received_html = "".join(
                (
                    '<span class="code-pill">'
                    f'{code} · {outlets[code]}'
                    '</span>'
                )
                for code
                in received_codes
            )

            st.markdown(
                (
                    '<div class="status-box '
                    'received-box">'
                    f'{received_html}'
                    '</div>'
                ),
                unsafe_allow_html=True,
            )

        else:

            st.caption(
                "No submissions yet."
            )

    # --------------------------------------------------------
    # PERFORMANCE CHARTS
    # --------------------------------------------------------

    if daily:

        performance = []

        for code, record in daily.items():

            performance.append(
                {
                    "Outlet": code,
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

        chart1, chart2 = st.columns(
            2
        )

        with chart1:

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
                height=260,
            )

        with chart2:

            st.markdown(
                "#### Appointment Value"
            )

            value_chart = (
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
                value_chart,
                height=260,
            )

    # --------------------------------------------------------
    # WHATSAPP READY SUMMARY
    # --------------------------------------------------------

    st.markdown(
        "#### 📱 WhatsApp Status"
    )

    pending_text = (
        ", ".join(
            pending_codes
        )
        if pending_codes
        else "None"
    )

    whatsapp_summary = (
        f"FINORA - Lobby Activity | "
        f"{selected_date.strftime('%d %b %Y')}\n"
        f"Received: "
        f"{len(received_codes)}/{len(outlets)} | "
        f"Pending: {len(pending_codes)} | "
        f"Guests: {int(total_guests)} | "
        f"Conversions: {int(total_conversions)} | "
        f"Conversion: {conversion_rate:.1f}% | "
        f"Appointment Value: {money(total_value)}\n"
        f"Pending: {pending_text}"
    )

    st.code(
        whatsapp_summary,
        language=None,
    )

    # --------------------------------------------------------
    # DETAILS
    # --------------------------------------------------------

    with st.expander(
        "View outlet-wise details",
        expanded=False,
    ):

        rows = []

        for code, name in (
            outlets.items()
        ):

            record = daily.get(
                code
            )

            if record:

                guests = clean_number(
                    record.get(
                        "Guests Interacted",
                        0,
                    )
                )

                conversions = (
                    clean_number(
                        record.get(
                            "Conversions",
                            0,
                        )
                    )
                )

                rows.append(
                    {
                        "Code": code,
                        "Outlet": name,
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
                            guests,
                        "Conversions":
                            conversions,
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
                        "Code": code,
                        "Outlet": name,
                        "Status":
                            "Pending",
                        "Therapist": "",
                        "Shift": "",
                        "Guests": "",
                        "Conversions": "",
                        "Appointment Value": "",
                    }
                )

        st.dataframe(
            pd.DataFrame(rows),
            use_container_width=True,
            hide_index=True,
            height=430,
        )

    if duplicate_count:

        st.caption(
            f"FINORA ignored "
            f"{duplicate_count} duplicate "
            f"historical record(s) while "
            f"calculating the dashboard."
        )


# ============================================================
# PERIOD DASHBOARD
# ============================================================

with period_tab:

    st.subheader(
        "Period Dashboard"
    )

    d1, d2, spacer = st.columns(
        [1, 1, 2]
    )

    with d1:

        start_date = st.date_input(
            "From",
            value=date.today(),
            format="DD/MM/YYYY",
            key="period_from",
        )

    with d2:

        end_date = st.date_input(
            "To",
            value=date.today(),
            format="DD/MM/YYYY",
            key="period_to",
        )

    if end_date < start_date:

        st.error(
            "The To date cannot be "
            "before the From date."
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

        value = float(
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
            "Conversion %",
            f"{rate:.1f}%",
        )

        p6.metric(
            "Appt. Value",
            money(value),
        )

        # Daily trend charts
        if not daily_df.empty:

            c1, c2 = st.columns(
                2
            )

            with c1:

                st.markdown(
                    "#### Submission Trend"
                )

                st.line_chart(
                    daily_df.set_index(
                        "Date"
                    )[
                        [
                            "Received",
                            "Pending",
                        ]
                    ],
                    height=250,
                )

            with c2:

                st.markdown(
                    "#### Guests & Conversions"
                )

                st.line_chart(
                    daily_df.set_index(
                        "Date"
                    )[
                        [
                            "Guests",
                            "Conversions",
                        ]
                    ],
                    height=250,
                )

            st.markdown(
                "#### Appointment Value Trend"
            )

            st.line_chart(
                daily_df.set_index(
                    "Date"
                )[
                    [
                        "Appointment Value"
                    ]
                ],
                height=220,
            )

        # Pending follow-up
        pending_df = outlet_df[
            outlet_df[
                "Pending"
            ] > 0
        ].copy()

        st.markdown(
            f"#### 🔴 Follow-up Required "
            f"({len(pending_df)} outlets)"
        )

        if pending_df.empty:

            st.success(
                "No pending lobby activity "
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
                height=320,
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
                f"FINORA ignored "
                f"{period_duplicates} duplicate "
                f"historical record(s)."
            )


# ============================================================
# FOOTER
# ============================================================

st.caption(
    "FINORA • Lobby Activity Management"
)
