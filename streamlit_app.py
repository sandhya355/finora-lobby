import streamlit as st
import pandas as pd
import re
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo
import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="FINORA | Your Finance AI", page_icon="💠", layout="wide", initial_sidebar_state="expanded")

ACTIVITY_SHEET = "Activity"
MASTER_SHEET = "Outlet Master"
HEADERS = ["Date","Outlet","Therapist","Shift Timings","Guests Interacted","Conversions","Appointment Value","Saved At"]

st.markdown("""
<style>
:root{--navy:#07345a;--navy2:#092744;--bg:#f5f7fb;--text:#17324d;--muted:#6f8093}
.stApp{background:var(--bg)}
.block-container{max-width:1450px;padding:1.25rem 2rem 3rem}
#MainMenu,footer{visibility:hidden}
header[data-testid="stHeader"]{background:#fff;border-bottom:1px solid #e6ebf1}
section[data-testid="stSidebar"]{background:linear-gradient(180deg,#063657 0%,#082743 100%);border-right:0}
section[data-testid="stSidebar"] .stButton>button{width:100%;min-height:46px;justify-content:flex-start;text-align:left;border:0;border-radius:5px;background:transparent;color:#eaf4fb;font-size:15px;font-weight:650;padding:0 15px;margin:2px 0}
section[data-testid="stSidebar"] .stButton>button:hover{background:#0b506d;color:#fff}
section[data-testid="stSidebar"] p{color:#d9e9f5}
.brand{font-size:28px!important;font-weight:850!important;color:white!important;margin:6px 0 0}
.tag{font-size:13px!important;color:#8ec6e4!important;margin:0 0 24px}
.navlabel{font-size:11px!important;font-weight:800!important;letter-spacing:1.4px;color:#73a8c8!important;margin:10px 0 7px}
.status{margin-top:24px;padding:12px;border:1px solid rgba(255,255,255,.12);border-radius:7px;background:rgba(255,255,255,.05);color:#dff8ee;font-size:13px}
.topline{font-size:13px!important;color:#718096!important;margin-bottom:0}
h1{font-size:30px!important;color:#15324c!important;margin:.1rem 0 .2rem!important}
h2{font-size:24px!important;color:#17324d!important}
h3{font-size:19px!important;color:#17324d!important}
.stApp p,.stApp label{font-size:15px}
div[data-testid="stMetric"]{background:#fff;border:1px solid #e1e8ef;border-radius:8px;padding:14px 16px;box-shadow:0 2px 7px rgba(21,50,76,.05)}
div[data-testid="stMetricValue"]{font-size:28px!important;font-weight:800;color:#17324d}
div[data-testid="stMetricLabel"] p{font-size:13px!important;font-weight:700!important;color:#718096!important}
div[data-testid="stVerticalBlockBorderWrapper"]{background:#fff;border-radius:8px!important;box-shadow:0 2px 8px rgba(21,50,76,.05)}
div[data-testid="stVerticalBlockBorderWrapper"] .stButton>button{min-height:48px;font-size:15px;font-weight:750;border-radius:6px}
div[data-baseweb="tab-list"]{gap:4px;background:#fff;border-bottom:1px solid #dfe6ee}
button[data-baseweb="tab"]{height:48px;font-size:15px!important;font-weight:700!important}
textarea{font-size:16px!important;line-height:1.55!important;background:#fff!important}
input{font-size:15px!important}
div[data-testid="stFileUploader"] section{background:#f7fbfd;border:1px dashed #9abacb;border-radius:7px}
.stButton>button[kind="primary"]{border:0;border-radius:6px;background:#0d8ea2;color:#fff;font-weight:800;min-height:48px}
.stButton>button[kind="primary"]:hover{background:#08798a;color:#fff}
[data-testid="stAlert"]{border-radius:7px}
.project-strip{height:5px;background:linear-gradient(90deg,#16c7bd,#1e91c5,#665cf5);border-radius:6px;margin:0 0 18px}
@media(max-width:900px){.block-container{padding:1rem}.stApp p{font-size:14px}}
</style>
""", unsafe_allow_html=True)

if "project" not in st.session_state:
    st.session_state.project = "Home"

def goto(name):
    st.session_state.project = name

with st.sidebar:
    st.markdown('<p class="brand">💠 FINORA</p><p class="tag">Your Finance AI</p><p class="navlabel">GENERAL</p>', unsafe_allow_html=True)
    for label, name in [
        ("🏠  Dashboard","Home"),
        ("📊  Lobby Activity","Lobby Activity"),
        ("🧾  GST Returns","GST Returns"),
        ("📈  Zenoti Reports","Zenoti Reports"),
        ("💰  Cash Reconciliation","Cash Reconciliation"),
        ("📁  Files","Files"),
        ("⚙️  Settings","Settings"),
    ]:
        if st.button(label, key="nav_"+name, use_container_width=True):
            goto(name); st.rerun()
    st.markdown('<div class="status">● &nbsp; FINORA Online</div>', unsafe_allow_html=True)

@st.cache_resource
def spreadsheet():
    info = dict(st.secrets["google_service_account"])
    creds = Credentials.from_service_account_info(info, scopes=["https://www.googleapis.com/auth/spreadsheets"])
    return gspread.authorize(creds).open_by_key(st.secrets["spreadsheet_id"])

def activity_ws(): return spreadsheet().worksheet(ACTIVITY_SHEET)
def master_ws(): return spreadsheet().worksheet(MASTER_SHEET)

def num(v):
    m=re.search(r"-?\d+(?:\.\d+)?",str(v or "").replace(",","").replace("₹",""))
    if not m:return 0
    x=float(m.group()); return int(x) if x.is_integer() else x

def money(v):
    try:return f"₹{float(v):,.0f}"
    except:return "₹0"

def normdate(v):
    s=str(v).strip()
    for fmt in ("%Y-%m-%d","%d/%m/%Y","%d-%m-%Y","%m/%d/%Y","%Y/%m/%d","%d %b %Y","%d %B %Y"):
        try:return datetime.strptime(s,fmt).date().isoformat()
        except:pass
    try:return pd.to_datetime(s,dayfirst=True).date().isoformat()
    except:return s

def now_ist():
    return datetime.now(ZoneInfo("Asia/Kolkata")).strftime("%Y-%m-%d %H:%M:%S")

def get_outlets():
    vals=master_ws().get("A:C"); out={}
    for row in vals[1:]:
        row=row+[""]*(3-len(row)); code=str(row[0]).strip().upper(); name=str(row[1]).strip(); active=str(row[2]).strip().lower()
        if code and name and active in {"yes","y","true","1","active"}:out[code]=name
    return out

def clean_line(line):
    return re.sub(r"^\s*(?:\d+\s*[\.\)]\s*|[-•*]\s*)","",line).strip()

def field(text, labels):
    for raw in text.splitlines():
        line=clean_line(raw)
        for label in labels:
            m=re.match(rf"(?i)^\s*{re.escape(label)}\s*(?::|-)\s*(.+?)\s*$",line)
            if m:return m.group(1).strip()
    return ""

def identify(text,outlets):
    u=text.upper()
    for code,name in outlets.items():
        if re.search(rf"(?<![A-Z0-9]){re.escape(code)}(?![A-Z0-9])",u):return code,name
    for code,name in outlets.items():
        if name.upper() in u:return code,name
    return None,None

def parse(text,outlets):
    code,name=identify(text,outlets)
    return {
        "code":code,"name":name,
        "therapist":field(text,["Therapist","Therapist Name","Name of Therapist"]),
        "shift":field(text,["Shift timings","Shift timing","Shift","Timings","Timing"]),
        "guests":num(field(text,["Number of guests interacted","No of guests interacted","No. of guests interacted","Guests interacted","Guest interacted","Number of guests","Guests"])),
        "conversions":num(field(text,["Number of conversions","No of conversions","No. of conversions","Conversions","Conversion"])),
        "value":num(field(text,["Appointment value","Appointment amount","Value"]))
    }

def records():
    vals=activity_ws().get("A:H")
    if not vals:
        activity_ws().append_row(HEADERS); return []
    out=[]
    for rn,row in enumerate(vals[1:],2):
        if not any(str(x).strip() for x in row):continue
        row=row+[""]*(8-len(row))
        out.append(dict(zip(HEADERS,row))|{"_row":rn})
    return out

def outlet_code(value,outlets):
    u=str(value).upper()
    for code,name in outlets.items():
        if re.search(rf"(?<![A-Z0-9]){re.escape(code)}(?![A-Z0-9])",u):return code
        if name.upper()==u.strip():return code
    return None

def save(activity_date,p,outlets):
    ws=activity_ws(); matches=[]
    for r in records():
        if normdate(r["Date"])==activity_date.isoformat() and outlet_code(r["Outlet"],outlets)==p["code"]:
            matches.append(r["_row"])
    row=[activity_date.isoformat(),f'{p["code"]}-Lobby',p["therapist"],p["shift"],p["guests"],p["conversions"],p["value"],now_ist()]
    if matches:
        ws.update(values=[row],range_name=f"A{matches[0]}:H{matches[0]}")
        for rn in sorted(matches[1:],reverse=True):ws.delete_rows(rn)
        return "updated"
    ws.append_row(row,value_input_option="USER_ENTERED"); return "saved"

def unique_records(outlets):
    d={}
    for r in records():
        code=outlet_code(r["Outlet"],outlets); dt=normdate(r["Date"])
        if code and dt:d[(dt,code)]=r
    return d

def title(text, sub=""):
    st.caption("FINORA  /  "+text.upper())
    st.title(text)
    if sub:st.write(sub)
    st.markdown('<div class="project-strip"></div>',unsafe_allow_html=True)

def placeholder(icon,name,desc):
    title(name,desc)
    with st.container(border=True):
        st.subheader(f"{icon} {name}")
        st.write("This project has its own FINORA workspace. We will connect its automation here.")

# HOME
if st.session_state.project=="Home":
    title("Dashboard","Welcome to FINORA — your finance and operations control panel.")
    c1,c2,c3,c4=st.columns(4)
    cards=[
        (c1,"📊","Lobby Activity","Daily outlet activity & pending monitoring","#14b8c4"),
        (c2,"🧾","GST Returns","GST return download & processing","#25b86b"),
        (c3,"📈","Zenoti Reports","Organisation report automation","#f0a323"),
        (c4,"💰","Cash Reconciliation","Cash sales vs deposit reconciliation","#ef5b4d"),
    ]
    for col,icon,name,desc,color in cards:
        with col:
            with st.container(border=True):
                st.markdown(f"### {icon} {name}")
                st.write(desc)
                if st.button("Open project →",key="card_"+name,use_container_width=True):
                    goto(name);st.rerun()
    st.write("")
    a,b,c=st.columns([1,1,2])
    with a:
        with st.container(border=True):
            st.metric("FINORA Status","Online")
    with b:
        with st.container(border=True):
            st.metric("Active Projects","4")
    with c:
        with st.container(border=True):
            st.subheader("Control Panel")
            st.write("Choose a project from the left menu. Each project opens in the same FINORA workspace.")

elif st.session_state.project=="Lobby Activity":
    try:
        outlets=get_outlets()
        if not outlets:st.error("No active outlets found in 'Outlet Master'.");st.stop()
    except Exception as e:
        st.error("FINORA cannot connect to Google Sheets.")
        with st.expander("Technical details"):st.code(str(e))
        st.stop()

    title("Lobby Activity","Capture outlet activity, monitor performance and follow up pending submissions.")
    enter,daily,period=st.tabs(["✍️ Enter Activity","📊 Daily Dashboard","📅 Period Dashboard"])

    with enter:
        st.subheader("Enter Lobby Activity")
        left,right=st.columns([1,2],gap="large")
        with left:
            activity_date=st.date_input("Activity Date",value=date.today(),format="DD/MM/YYYY")
            photo=st.file_uploader("Optional Photo",type=["jpg","jpeg","png"])
            st.caption("Photos are not stored by FINORA.")
        with right:
            text=st.text_area("Paste WhatsApp Activity",height=230,placeholder="JIAL-Lobby Activity\n1. Therapist: Gayatri\n2. Shift timings: 7AM to 4PM\n3. Number of guests interacted- 5\n4. Number of conversions: 2\n5. Appointment value:7064")
        if st.button("✨ Read & Save Activity",type="primary",use_container_width=True):
            if not text.strip():st.error("Please paste the WhatsApp activity first.")
            else:
                p=parse(text,outlets)
                if not p["code"]:st.error("FINORA could not recognise the outlet code.")
                elif not p["therapist"] or not p["shift"]:st.error("FINORA could not read Therapist or Shift Timings. Please check the message.")
                else:
                    try:
                        action=save(activity_date,p,outlets)
                        st.success(("🔄 Existing activity updated" if action=="updated" else "✅ New activity saved")+f" — {p['code']} • {p['name']}")
                        x1,x2,x3,x4=st.columns(4)
                        x1.metric("Outlet",p["code"]);x2.metric("Guests",p["guests"]);x3.metric("Conversions",p["conversions"]);x4.metric("Appointment Value",money(p["value"]))
                    except Exception as e:
                        st.error("FINORA read the activity but Google Sheets could not be updated.")
                        with st.expander("Technical details"):st.code(str(e))

    with daily:
        st.subheader("Daily Lobby Activity Dashboard")
        selected=st.date_input("Select Date",value=date.today(),format="DD/MM/YYYY",key="daily_date")
        u=unique_records(outlets)
        d={code:r for (dt,code),r in u.items() if dt==selected.isoformat()}
        received=list(d); pending=[x for x in outlets if x not in d]
        guests=sum(num(r["Guests Interacted"]) for r in d.values())
        conv=sum(num(r["Conversions"]) for r in d.values())
        value=sum(num(r["Appointment Value"]) for r in d.values())
        rate=(conv/guests*100) if guests else 0
        m=st.columns(6)
        for col,label,val in zip(m,["Total Outlets","Received","Pending","Guests","Conversions","Appointment Value"],[len(outlets),len(received),len(pending),int(guests),int(conv),money(value)]):col.metric(label,val)
        st.write("")
        a,b=st.columns(2,gap="large")
        with a:
            with st.container(border=True):
                st.subheader("✅ Received Outlets")
                if received:st.dataframe(pd.DataFrame([{"Code":c,"Outlet":outlets[c]} for c in received]),hide_index=True,use_container_width=True)
                else:st.info("No submissions received yet.")
        with b:
            with st.container(border=True):
                st.subheader("⏳ Pending Outlets")
                if pending:st.dataframe(pd.DataFrame([{"Code":c,"Outlet":outlets[c]} for c in pending]),hide_index=True,use_container_width=True)
                else:st.success("All outlets submitted.")
        if d:
            chart=pd.DataFrame([{"Outlet":c,"Guests":num(r["Guests Interacted"]),"Conversions":num(r["Conversions"]),"Appointment Value":num(r["Appointment Value"])} for c,r in d.items()]).set_index("Outlet")
            c1,c2=st.columns(2)
            with c1:
                st.subheader("Guests vs Conversions");st.bar_chart(chart[["Guests","Conversions"]],height=280)
            with c2:
                st.subheader("Appointment Value");st.bar_chart(chart[["Appointment Value"]],height=280)
        st.subheader("WhatsApp Follow-up Summary")
        st.code(f"""FINORA Lobby Activity | {selected.strftime('%d %b %Y')}
Received: {len(received)}/{len(outlets)}
Pending: {len(pending)}
Guests: {int(guests)}
Conversions: {int(conv)}
Conversion Rate: {rate:.1f}%
Appointment Value: {money(value)}
Pending Outlets: {', '.join(pending) if pending else 'None'}""")

    with period:
        st.subheader("Period Dashboard")
        a,b=st.columns(2)
        start=a.date_input("From Date",value=date.today(),format="DD/MM/YYYY",key="pstart")
        end=b.date_input("To Date",value=date.today(),format="DD/MM/YYYY",key="pend")
        if end<start:st.error("To Date cannot be before From Date.")
        else:
            u=unique_records(outlets);days=[];x=start
            while x<=end:days.append(x);x+=timedelta(days=1)
            rows=[]
            for code,name in outlets.items():
                got=[];missing=[];g=c=v=0
                for day in days:
                    r=u.get((day.isoformat(),code))
                    if r:
                        got.append(day);g+=num(r["Guests Interacted"]);c+=num(r["Conversions"]);v+=num(r["Appointment Value"])
                    else:missing.append(day)
                rows.append({"Code":code,"Outlet":name,"Received Days":len(got),"Pending Days":len(missing),"Guests":g,"Conversions":c,"Appointment Value":v,"Missing Dates":", ".join(z.strftime("%d-%b") for z in missing) if missing else "Complete"})
            df=pd.DataFrame(rows);expected=len(days)*len(outlets);rec=int(df["Received Days"].sum());pend=expected-rec
            m=st.columns(6)
            for col,label,val in zip(m,["Days","Expected","Received","Pending","Guests","Appointment Value"],[len(days),expected,rec,pend,int(df["Guests"].sum()),money(df["Appointment Value"].sum())]):col.metric(label,val)
            st.subheader("Pending Outlet / Date Follow-up")
            pdf=df[df["Pending Days"]>0]
            if pdf.empty:st.success("All outlets are complete for this period.")
            else:st.dataframe(pdf[["Code","Outlet","Received Days","Pending Days","Missing Dates"]],hide_index=True,use_container_width=True,height=420)
            st.subheader("Outlet Performance")
            st.bar_chart(df.set_index("Code")[["Guests","Conversions"]],height=300)

elif st.session_state.project=="GST Returns":placeholder("🧾","GST Returns","GST return download and processing automation.")
elif st.session_state.project=="Zenoti Reports":placeholder("📈","Zenoti Reports","Automated Zenoti organisation report downloads.")
elif st.session_state.project=="Cash Reconciliation":placeholder("💰","Cash Reconciliation","Cash sales versus cash deposit reconciliation.")
elif st.session_state.project=="Files":placeholder("📁","Files","FINORA file and report centre.")
elif st.session_state.project=="Settings":placeholder("⚙️","Settings","FINORA administration and configuration.")
