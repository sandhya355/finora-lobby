import streamlit as st
import pandas as pd
import re
from datetime import date

# ============================================================
# FINORA - LOBBY ACTIVITY
# ============================================================

st.set_page_config(
    page_title="FINORA | Lobby Activity",
    page_icon="💠",
    layout="wide",
)

# ============================================================
# OUTLET MASTER
# ============================================================

OUTLETS = {
    "BDAL": "Bangalore Domestic Airport",
    "BALM": "Bangalore La Marvella hotel",
    "CCMA": "Chennai - Courtyard Marriot",
    "CFVM": "Chennai - Forum Vijaya Mall",
    "CHEA": "Chennai Express Avenue",
    "CIAL": "Cochin Domestic Airport",
    "GORC": "Goa Regenta Candolim",
    "KKCH": "Kodaikanal Carlton Hotel",
    "AHNO": "Ahmadabad - Novotel",
    "AHPP": "Ahmedabad - Pride Plaza",
    "DLLT": "Delhi Airport - Lemon Tree Premi",
    "HYJH": "Hyd - Jubilee Hills",
    "RJMS": "Rajahmundry Manjeera Sarovar",
    "GVK": "Hyd - GVK One Mall",
    "HYRM": "Hyd - Ramada Manohar",
    "HYGN": "Hyd - Svm Grand Nagole",
    "HYTV": "Hyd - Taj Vivanta",
    "HYRD": "Hyd-Radisson",
    "JIAL": "Jaipur Airport",
    "MCMA": "Mumbai - Courtyard Marriott",
    "MULT": "Mumbai Lemon Tree",
}

# ============================================================
# SESSION STORAGE
# Temporary for first online test.
# Google Sheets will replace this in the next step.
# ============================================================

if "records" not in st.session_state:
    st.session_state.records = {}

# ============================================================
# HELPERS
# ============================================================

def clean_number(value):
    if value is None:
        return 0

    value = str(value).replace(",", "").replace("₹", "").strip()

    match = re.search(r"-?\d+(?:\.\d+)?", value)

    if not match:
        return 0

    number = float(match.group())

    if number.is_integer():
        return int(number)

    return number


def extract_after_labels(text, labels):
    for label in labels:
        pattern = rf"(?im)^\s*{re.escape(label)}\s*[:\-]\s*(.+?)\s*$"
        match = re.search(pattern, text)

        if match:
            return match.group(1).strip()

    return ""


def detect_outlet(text):
    upper_text = text.upper()

    # First look for exact outlet codes
    for code, outlet_name in OUTLETS.items():
        if re.search(rf"\b{re.escape(code)}\b", upper_text):
            return code, outlet_name

    # Then try outlet names
    for code, outlet_name in OUTLETS.items():
        if outlet_name.upper() in upper_text:
            return code, outlet_name

    return None, None


def parse_activity(text):
    code, outlet_name = detect_outlet(text)

    therapist = extract_after_labels(
        text,
        [
            "Therapist",
            "Therapist Name",
            "Name of Therapist",
            "Staff",
        ],
    )

    shift = extract_after_labels(
        text,
        [
            "Shift",
            "Shift Timing",
            "Shift Timings",
            "Timing",
            "Timings",
        ],
    )

    guests_raw = extract_after_labels(
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

    conversions_raw = extract_after_labels(
        text,
        [
            "Conversions",
            "Conversion",
            "Converted",
        ],
    )

    appointment_raw = extract_after_labels(
        text,
        [
            "Appointment Value",
            "Appointment",
            "Appointment Amount",
            "Value",
        ],
    )

    guests = clean_number(guests_raw)
    conversions = clean_number(conversions_raw)
    appointment_value = clean_number(appointment_raw)

    return {
        "Outlet Code": code,
        "Outlet": outlet_name,
        "Therapist": therapist,
        "Shift Timings": shift,
        "Guests Interacted": guests,
        "Conversions": conversions,
        "Appointment Value": appointment_value,
    }


def money(value):
    try:
        return f"₹{float(value):,.0f}"
    except:
        return "₹0"


# ============================================================
# DESIGN
# ============================================================

st.markdown(
    """
    <style>

    .block-container {
        padding-top: 1.4rem;
        padding-bottom: 3rem;
    }

    .finora-header {
        padding: 22px 26px;
        border-radius: 18px;
        background: linear-gradient(
            120deg,
            #071b33 0%,
            #0d3550 55%,
            #116b6d 100%
        );
        margin-bottom: 22px;
    }

    .finora-title {
        color: white;
        font-size: 34px;
        font-weight: 800;
        margin: 0;
    }

    .finora-subtitle {
        color: #d6f4ee;
        font-size: 15px;
        margin-top: 4px;
    }

    .status-received {
        color: #0a7a3d;
        font-weight: 700;
    }

    .status-pending {
        color: #b26a00;
        font-weight: 700;
    }

    div[data-testid="stMetric"] {
        border: 1px solid #e6e9ef;
        padding: 14px;
        border-radius: 14px;
        background: white;
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
            Lobby Activity • Daily Outlet Dashboard
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ============================================================
# TABS
# ============================================================

entry_tab, dashboard_tab = st.tabs(
    ["📝 Enter Lobby Activity", "📊 Daily Dashboard"]
)

# ============================================================
# ENTRY TAB
# ============================================================

with entry_tab:

    st.subheader("Paste WhatsApp Lobby Activity")

    selected_date = st.date_input(
        "Activity Date",
        value=date.today(),
        format="DD/MM/YYYY",
    )

    st.caption(
        "Copy the lobby activity message from WhatsApp and paste it below."
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
        type=["jpg", "jpeg", "png"],
        help=(
            "FINORA will not save the photograph in this first version. "
            "Photo recognition will be connected separately."
        ),
    )

    if uploaded_photo is not None:
        st.info(
            "Photo received temporarily. It will not be added to the dashboard or saved by this app."
        )

    if st.button(
        "✨ FINORA - Read & Save Activity",
        type="primary",
        use_container_width=True,
    ):

        if not whatsapp_text.strip():
            st.error("Please paste the WhatsApp activity first.")

        else:
            result = parse_activity(whatsapp_text)

            if not result["Outlet Code"]:
                st.error(
                    "FINORA could not recognise the outlet code. "
                    "Please make sure the WhatsApp message contains the outlet code "
                    "such as JIAL, HYGN, CIAL, GVK, etc."
                )

            else:
                record_key = (
                    selected_date.isoformat(),
                    result["Outlet Code"],
                )

                was_existing = record_key in st.session_state.records

                st.session_state.records[record_key] = {
                    "Date": selected_date.isoformat(),
                    **result,
                }

                if was_existing:
                    st.success(
                        f"✅ Updated {result['Outlet Code']} - "
                        f"{result['Outlet']} for {selected_date.strftime('%d-%m-%Y')}."
                    )
                else:
                    st.success(
                        f"✅ Saved {result['Outlet Code']} - "
                        f"{result['Outlet']} for {selected_date.strftime('%d-%m-%Y')}."
                    )

                c1, c2 = st.columns(2)

                with c1:
                    st.write("**Outlet Code:**", result["Outlet Code"])
                    st.write("**Outlet:**", result["Outlet"])
                    st.write(
                        "**Therapist:**",
                        result["Therapist"] or "-",
                    )
                    st.write(
                        "**Shift:**",
                        result["Shift Timings"] or "-",
                    )

                with c2:
                    st.write(
                        "**Guests Interacted:**",
                        result["Guests Interacted"],
                    )
                    st.write(
                        "**Conversions:**",
                        result["Conversions"],
                    )
                    st.write(
                        "**Appointment Value:**",
                        money(result["Appointment Value"]),
                    )

# ============================================================
# DASHBOARD TAB
# ============================================================

with dashboard_tab:

    st.subheader("Daily Lobby Activity Dashboard")

    dashboard_date = st.date_input(
        "Dashboard Date",
        value=date.today(),
        format="DD/MM/YYYY",
        key="dashboard_date",
    )

    selected_date_string = dashboard_date.isoformat()

    daily_records = {}

    for (record_date, code), record in st.session_state.records.items():
        if record_date == selected_date_string:
            daily_records[code] = record

    received = len(daily_records)
    total_outlets = len(OUTLETS)
    pending = total_outlets - received

    total_guests = sum(
        clean_number(x.get("Guests Interacted", 0))
        for x in daily_records.values()
    )

    total_conversions = sum(
        clean_number(x.get("Conversions", 0))
        for x in daily_records.values()
    )

    total_appointment_value = sum(
        clean_number(x.get("Appointment Value", 0))
        for x in daily_records.values()
    )

    conversion_rate = (
        (total_conversions / total_guests * 100)
        if total_guests
        else 0
    )

    r1, r2, r3 = st.columns(3)

    r1.metric("Total Outlets", total_outlets)
    r2.metric("Received", received)
    r3.metric("Pending", pending)

    r4, r5, r6, r7 = st.columns(4)

    r4.metric("Guests", int(total_guests))
    r5.metric("Conversions", int(total_conversions))
    r6.metric("Conversion Rate", f"{conversion_rate:.1f}%")
    r7.metric(
        "Appointment Value",
        money(total_appointment_value),
    )

    st.divider()

    rows = []

    for code, outlet_name in OUTLETS.items():

        if code in daily_records:
            record = daily_records[code]

            guests = clean_number(
                record.get("Guests Interacted", 0)
            )

            conversions = clean_number(
                record.get("Conversions", 0)
            )

            outlet_conversion = (
                conversions / guests * 100
                if guests
                else 0
            )

            rows.append(
                {
                    "Code": code,
                    "Outlet": outlet_name,
                    "Status": "✅ Received",
                    "Therapist": record.get("Therapist", ""),
                    "Shift": record.get("Shift Timings", ""),
                    "Guests": guests,
                    "Conversions": conversions,
                    "Conversion %": f"{outlet_conversion:.1f}%",
                    "Appointment Value": money(
                        record.get("Appointment Value", 0)
                    ),
                }
            )

        else:
            rows.append(
                {
                    "Code": code,
                    "Outlet": outlet_name,
                    "Status": "⏳ Pending",
                    "Therapist": "",
                    "Shift": "",
                    "Guests": "",
                    "Conversions": "",
                    "Conversion %": "",
                    "Appointment Value": "",
                }
            )

    dashboard_df = pd.DataFrame(rows)

    st.dataframe(
        dashboard_df,
        use_container_width=True,
        hide_index=True,
        height=770,
    )

    st.caption(
        "FINORA Lobby Activity • "
        + dashboard_date.strftime("%d %B %Y")
    )

# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "FINORA • Lobby Activity Management"
)
