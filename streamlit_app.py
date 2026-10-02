import streamlit as st
import pandas as pd
import re
from datetime import date, datetime, timedelta
import gspread
from google.oauth2.service_account import Credentials

# ============================================================
# FINORA - LOBBY ACTIVITY MANAGEMENT
# ============================================================

st.set_page_config(
    page_title="FINORA | Lobby Activity",
    page_icon="💠",
    layout="wide",
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
# GOOGLE SHEETS CONNECTION
# ============================================================

@st.cache_resource
def get_spreadsheet():

    service_account_info = dict(
        st.secrets["google_service_account"]
    )

    scopes = [
        "https://www.googleapis.com/auth/spreadsheets"
    ]

    credentials = Credentials.from_service_account_info(
        service_account_info,
        scopes=scopes,
    )

    client = gspread.authorize(credentials)

    return client.open_by_key(
        st.secrets["spreadsheet_id"]
    )


def get_activity_sheet():
    return get_spreadsheet().worksheet(ACTIVITY_SHEET)


def get_master_sheet():
    return get_spreadsheet().worksheet(OUTLET_MASTER_SHEET)


# ============================================================
# BASIC HELPERS
# ============================================================

def clean_number(value):

    if value is None:
        return 0

    text = str(value)

    text = text.replace(",", "")
    text = text.replace("₹", "")
    text = text.strip()

    match = re.search(
        r"-?\d+(?:\.\d+)?",
        text
    )

    if not match:
        return 0

    number = float(match.group())

    if number.is_integer():
        return int(number)

    return number


def money(value):

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
                value,
                fmt
            ).date().isoformat()

        except ValueError:
            pass

    try:

        return pd.to_datetime(
            value,
            dayfirst=True
        ).date().isoformat()

    except Exception:

        return value


# ============================================================
# OUTLET MASTER
# ============================================================

def load_outlet_master():

    worksheet = get_master_sheet()

    records = worksheet.get_all_records()

    outlets = {}

    for row in records:

        code = str(
            row.get("Outlet Code", "")
        ).strip().upper()

        name = str(
            row.get("Outlet Name", "")
        ).strip()

        active = str(
            row.get("Active", "Yes")
        ).strip().lower()

        if (
            code
            and name
            and active in [
                "yes",
                "y",
                "true",
                "1",
                "active",
            ]
        ):
            outlets[code] = name

    return outlets


# ============================================================
# WHATSAPP MESSAGE RECOGNITION
# ============================================================

def extract_field(text, labels):

    for label in labels:

        pattern = (
            rf"(?im)^\s*"
            rf"{re.escape(label)}"
            rf"\s*[:\-]\s*(.+?)\s*$"
        )

        match = re.search(
            pattern,
            text
        )

        if match:
            return match.group(1).strip()

    return ""


def detect_outlet(text, outlets):

    upper_text = text.upper()

    # First detect outlet code
    for code, name in outlets.items():

        if re.search(
            rf"(?<![A-Z0-9])"
            rf"{re.escape(code)}"
            rf"(?![A-Z0-9])",
            upper_text,
        ):

            return code, name

    # Then try outlet name
    for code, name in outlets.items():

        if name.upper() in upper_text:

            return code, name

    return None, None


def parse_activity(text, outlets):

    code, name = detect_outlet(
        text,
        outlets
    )

    therapist = extract_field(
        text,
        [
            "Therapist",
            "Therapist Name",
            "Name of Therapist",
            "Staff",
        ],
    )

    shift = extract_field(
        text,
        [
            "Shift",
            "Shift Timing",
            "Shift Timings",
            "Timing",
            "Timings",
        ],
    )

    guests = clean_number(
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
    )

    conversions = clean_number(
        extract_field(
            text,
            [
                "Conversions",
                "Conversion",
                "Converted",
            ],
        )
    )

    appointment = clean_number(
        extract_field(
            text,
            [
                "Appointment Value",
                "Appointment Amount",
                "Appointment",
                "Value",
            ],
        )
    )

    return {
        "Outlet Code": code,
        "Outlet Name": name,
        "Therapist": therapist,
        "Shift Timings": shift,
        "Guests Interacted": guests,
        "Conversions": conversions,
        "Appointment Value": appointment,
    }


# ============================================================
# READ ACTIVITY DATA
# ============================================================

def read_activity():

    worksheet = get_activity_sheet()

    values = worksheet.get_all_values()

    if not values:

        worksheet.append_row(
            ACTIVITY_HEADERS
        )

        return []

    headers = values[0]

    records = []

    for row_number, row in enumerate(
        values[1:],
        start=2,
    ):

        if not any(row):
            continue

        if len(row) < len(headers):

            row = row + (
                [""] *
                (len(headers) - len(row))
            )

        record = dict(
            zip(headers, row)
        )

        record["_row"] = row_number

        records.append(record)

    return records


# ============================================================
# IDENTIFY OUTLET FROM OLD/NEW SHEET RECORD
# ============================================================

def sheet_outlet_code(value, outlets):

    value = str(value).strip()

    upper_value = value.upper()

    for code in outlets:

        if re.search(
            rf"(?<![A-Z0-9])"
            rf"{re.escape(code)}"
            rf"(?![A-Z0-9])",
            upper_value,
        ):

            return code

    for code, name in outlets.items():

        if name.upper() == upper_value:

            return code

    return None


# ============================================================
# SAVE / UPDATE / REMOVE DUPLICATES
# ============================================================

def save_activity(
    activity_date,
    parsed,
    outlets,
):

    worksheet = get_activity_sheet()

    records = read_activity()

    target_date = activity_date.isoformat()

    target_code = parsed["Outlet Code"]

    matches = []

    for record in records:

        record_date = normalize_date(
            record.get(
                "Date",
                ""
            )
        )

        record_code = sheet_outlet_code(
            record.get(
                "Outlet",
                ""
            ),
            outlets,
        )

        if (
            record_date == target_date
            and record_code == target_code
        ):

            matches.append(
                record["_row"]
            )

    saved_at = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    values = [
        target_date,
        f"{target_code}-Lobby",
        parsed["Therapist"],
        parsed["Shift Timings"],
        parsed["Guests Interacted"],
        parsed["Conversions"],
        parsed["Appointment Value"],
        saved_at,
    ]

    # Existing outlet/date
    if matches:

        main_row = matches[0]

        worksheet.update(
            range_name=(
                f"A{main_row}:H{main_row}"
            ),
            values=[values],
        )

        # Remove old duplicate rows
        duplicates = matches[1:]

        for row in sorted(
            duplicates,
            reverse=True,
        ):

            worksheet.delete_rows(row)

        return (
            "updated",
            len(duplicates)
        )

    # New outlet/date
    worksheet.append_row(
        values,
        value_input_option="USER_ENTERED",
    )

    return (
        "saved",
        0
    )


# ============================================================
# DAILY DATA
# ============================================================

def daily_activity(
    selected_date,
    outlets,
):

    target = selected_date.isoformat()

    records = read_activity()

    daily = {}

    for record in records:

        if normalize_date(
            record.get(
                "Date",
                ""
            )
        ) != target:

            continue

        code = sheet_outlet_code(
            record.get(
                "Outlet",
                ""
            ),
            outlets,
        )

        if not code:
            continue

        # Latest duplicate wins for dashboard.
        daily[code] = record

    return daily


# ============================================================
# DATE RANGE REPORT
# ============================================================

def date_range_report(
    start_date,
    end_date,
    outlets,
):

    records = read_activity()

    received_dates = {
        code: set()
        for code in outlets
    }

    for record in records:

        normalized = normalize_date(
            record.get(
                "Date",
                ""
            )
        )

        try:
            record_date = datetime.strptime(
                normalized,
                "%Y-%m-%d"
            ).date()

        except Exception:
            continue

        if not (
            start_date
            <= record_date
            <= end_date
        ):
            continue

        code = sheet_outlet_code(
            record.get(
                "Outlet",
                ""
            ),
            outlets,
        )

        if code in received_dates:

            received_dates[code].add(
                record_date
            )

    all_dates = []

    current = start_date

    while current <= end_date:

        all_dates.append(current)

        current += timedelta(days=1)

    rows = []

    for code, name in outlets.items():

        received = received_dates[
            code
        ]

        missing = [
            day
            for day in all_dates
            if day not in received
        ]

        rows.append(
            {
                "Code": code,
                "Outlet": name,
                "Days Expected":
                    len(all_dates),
                "Days Received":
                    len(received),
                "Days Pending":
                    len(missing),
                "Pending Dates":
                    ", ".join(
                        day.strftime(
                            "%d-%b"
                        )
                        for day in missing
                    )
                    if missing
                    else "✅ Complete",
            }
        )

    return pd.DataFrame(rows)


# ============================================================
# DESIGN
# ============================================================

st.markdown(
    """
    <style>

    .block-container {
        padding-top: 1.2rem;
        padding-bottom: 3rem;
    }

    .finora-header {
        padding: 23px 28px;
        border-radius: 18px;
        background:
        linear-gradient(
            120deg,
            #071b33 0%,
            #0d3550 55%,
            #116b6d 100%
        );
        margin-bottom: 20px;
    }

    .finora-title {
        color: white;
        font-size: 36px;
        font-weight: 800;
    }

    .finora-subtitle {
        color: #d6f4ee;
        font-size: 15px;
    }

    div[data-testid="stMetric"] {
        border: 1px solid #e5e8ed;
        padding: 14px;
        border-radius: 14px;
    }

    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="finora-header">

    <div class="finora-title">
    FINORA
    </div>

    <div class="finora-subtitle">
    Lobby Activity • Outlet Monitoring Dashboard
    </div>

    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# CONNECT
# ============================================================

try:

    outlets = load_outlet_master()

    if not outlets:

        st.error(
            "No active outlets found in "
            "'Outlet Master'."
        )

        st.stop()

except Exception as error:

    st.error(
        "FINORA cannot connect to "
        "Google Sheets."
    )

    with st.expander(
        "Technical details"
    ):

        st.code(str(error))

    st.stop()


# ============================================================
# MAIN TABS
# ============================================================

entry_tab, daily_tab, range_tab = st.tabs(
    [
        "📝 Enter Activity",
        "📊 Daily Dashboard",
        "📅 Period Dashboard",
    ]
)


# ============================================================
# ENTRY TAB
# ============================================================

with entry_tab:

    st.subheader(
        "Paste WhatsApp Lobby Activity"
    )

    activity_date = st.date_input(
        "Activity Date",
        value=date.today(),
        format="DD/MM/YYYY",
    )

    whatsapp_text = st.text_area(
        "WhatsApp Activity",
        height=260,
        placeholder="""Example:

JIAL-Lobby Activity

Therapist: Neha
Shift Timings: 1 PM to 10 PM
Guests Interacted: 2
Conversions: 1
Appointment Value: 3381
""",
    )

    uploaded_photo = st.file_uploader(
        "Optional photo",
        type=[
            "jpg",
            "jpeg",
            "png",
        ],
    )

    if uploaded_photo:

        st.info(
            "Photo received temporarily. "
            "FINORA does not save the "
            "photograph or photo link."
        )

    if st.button(
        "✨ FINORA - Read & Save Activity",
        type="primary",
        use_container_width=True,
    ):

        if not whatsapp_text.strip():

            st.error(
                "Please paste the "
                "WhatsApp activity."
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

                if action == "saved":

                    st.success(
                        "✅ New activity saved: "
                        f"{parsed['Outlet Code']} - "
                        f"{parsed['Outlet Name']}"
                    )

                else:

                    st.success(
                        "🔄 Existing activity "
                        "updated: "
                        f"{parsed['Outlet Code']} - "
                        f"{parsed['Outlet Name']}"
                    )

                if removed:

                    st.info(
                        f"FINORA removed "
                        f"{removed} duplicate "
                        f"record(s)."
                    )

                col1, col2 = st.columns(2)

                with col1:

                    st.write(
                        "**Outlet:**",
                        parsed[
                            "Outlet Name"
                        ],
                    )

                    st.write(
                        "**Therapist:**",
                        parsed[
                            "Therapist"
                        ] or "-",
                    )

                    st.write(
                        "**Shift:**",
                        parsed[
                            "Shift Timings"
                        ] or "-",
                    )

                with col2:

                    st.write(
                        "**Guests:**",
                        parsed[
                            "Guests Interacted"
                        ],
                    )

                    st.write(
                        "**Conversions:**",
                        parsed[
                            "Conversions"
                        ],
                    )

                    st.write(
                        "**Appointment Value:**",
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

    st.subheader(
        "Daily Lobby Activity Dashboard"
    )

    selected_date = st.date_input(
        "Select Date",
        value=date.today(),
        format="DD/MM/YYYY",
        key="daily_date",
    )

    daily = daily_activity(
        selected_date,
        outlets,
    )

    received_codes = set(
        daily.keys()
    )

    pending_codes = [
        code
        for code in outlets
        if code not in received_codes
    ]

    total_guests = sum(
        clean_number(
            record.get(
                "Guests Interacted",
                0,
            )
        )
        for record in daily.values()
    )

    total_conversions = sum(
        clean_number(
            record.get(
                "Conversions",
                0,
            )
        )
        for record in daily.values()
    )

    total_value = sum(
        clean_number(
            record.get(
                "Appointment Value",
                0,
            )
        )
        for record in daily.values()
    )

    conversion_rate = (
        total_conversions
        / total_guests
        * 100
        if total_guests
        else 0
    )

    st.markdown(
        "### "
        + selected_date.strftime(
            "%d %B %Y"
        )
    )

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "Total Outlets",
        len(outlets),
    )

    c2.metric(
        "Received",
        len(received_codes),
    )

    c3.metric(
        "Pending",
        len(pending_codes),
    )

    c4, c5, c6, c7 = st.columns(4)

    c4.metric(
        "Guests",
        int(total_guests),
    )

    c5.metric(
        "Conversions",
        int(total_conversions),
    )

    c6.metric(
        "Conversion Rate",
        f"{conversion_rate:.1f}%",
    )

    c7.metric(
        "Appointment Value",
        money(total_value),
    )

    st.divider()

    # -------------------------------
    # PENDING OUTLETS
    # -------------------------------

    st.subheader(
        f"🔴 Pending Outlets "
        f"({len(pending_codes)})"
    )

    if pending_codes:

        pending_df = pd.DataFrame(
            [
                {
                    "Code": code,
                    "Outlet":
                        outlets[code],
                    "Status":
                        "⏳ Pending",
                }
                for code
                in pending_codes
            ]
        )

        st.dataframe(
            pending_df,
            use_container_width=True,
            hide_index=True,
        )

    else:

        st.success(
            "🎉 All active outlets "
            "have submitted activity."
        )

    st.divider()

    # -------------------------------
    # ALL OUTLETS
    # -------------------------------

    st.subheader(
        "All Outlet Status"
    )

    rows = []

    for code, name in outlets.items():

        record = daily.get(code)

        if record:

            guests = clean_number(
                record.get(
                    "Guests Interacted",
                    0,
                )
            )

            conversions = clean_number(
                record.get(
                    "Conversions",
                    0,
                )
            )

            rate = (
                conversions
                / guests
                * 100
                if guests
                else 0
            )

            rows.append(
                {
                    "Code": code,
                    "Outlet": name,
                    "Status":
                        "✅ Received",
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
                    "Conversion %":
                        f"{rate:.1f}%",
                    "Appointment Value":
                        money(
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
                        "⏳ Pending",
                    "Therapist": "",
                    "Shift": "",
                    "Guests": "",
                    "Conversions": "",
                    "Conversion %": "",
                    "Appointment Value": "",
                }
            )

    st.dataframe(
        pd.DataFrame(rows),
        use_container_width=True,
        hide_index=True,
        height=750,
    )


# ============================================================
# PERIOD DASHBOARD
# ============================================================

with range_tab:

    st.subheader(
        "Period Submission Dashboard"
    )

    col1, col2 = st.columns(2)

    with col1:

        start_date = st.date_input(
            "From Date",
            value=date.today(),
            format="DD/MM/YYYY",
            key="range_start",
        )

    with col2:

        end_date = st.date_input(
            "To Date",
            value=date.today(),
            format="DD/MM/YYYY",
            key="range_end",
        )

    if end_date < start_date:

        st.error(
            "To Date cannot be "
            "before From Date."
        )

    else:

        number_of_days = (
            end_date
            - start_date
        ).days + 1

        range_df = date_range_report(
            start_date,
            end_date,
            outlets,
        )

        total_expected = (
            len(outlets)
            * number_of_days
        )

        total_received = int(
            range_df[
                "Days Received"
            ].sum()
        )

        total_pending = (
            total_expected
            - total_received
        )

        p1, p2, p3, p4 = (
            st.columns(4)
        )

        p1.metric(
            "Active Outlets",
            len(outlets),
        )

        p2.metric(
            "Days",
            number_of_days,
        )

        p3.metric(
            "Submissions Received",
            total_received,
        )

        p4.metric(
            "Submissions Pending",
            total_pending,
        )

        st.divider()

        st.subheader(
            "Outlet-wise Pending Report"
        )

        st.dataframe(
            range_df,
            use_container_width=True,
            hide_index=True,
            height=750,
        )

        incomplete = range_df[
            range_df[
                "Days Pending"
            ] > 0
        ]

        st.subheader(
            "🔴 Outlets Requiring Follow-up"
        )

        if incomplete.empty:

            st.success(
                "🎉 No pending activity "
                "for this period."
            )

        else:

            st.dataframe(
                incomplete[
                    [
                        "Code",
                        "Outlet",
                        "Days Pending",
                        "Pending Dates",
                    ]
                ],
                use_container_width=True,
                hide_index=True,
            )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "FINORA • Lobby Activity Management"
)
