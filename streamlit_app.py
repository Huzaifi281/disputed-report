import streamlit as st
import pandas as pd
import os
import glob
import calendar
from datetime import date, datetime

# --- PAGE CONFIG ---
st.set_page_config(page_title="📅 Missing Transactions", layout="wide")
st.title("📅 Missing Transactions Report")
st.markdown("Track daily transaction records for **April – June 2025**.")

# --- CACHE IMAGES ---
@st.cache_data
def get_images():
    return {os.path.basename(p) for p in glob.glob("data/*.jpg")}

images = get_images()

# --- LOAD DATA ---
df = pd.read_excel("disputed.xlsx", sheet_name="rep")
df.columns = df.columns.str.strip()
df['Amt'] = pd.to_numeric(df['Amt'], errors='coerce')
df['Date'] = pd.to_datetime(df['Date'], errors='coerce').dt.date
df.dropna(subset=['Date'], inplace=True)

df['File'] = df.get('File', None)
df = df[df['Date'].between(date(2025, 4, 1), date(2025, 6, 30))]
grouped = df.groupby('Date')

# --- CLICK STATE ---
clicked_date = st.session_state.get("clicked_date")
if isinstance(clicked_date, datetime):
    clicked_date = clicked_date.date()

# --- CALENDAR DRAW ---
def draw_calendar(year: int, month: int, grouped_data):
    st.markdown(f"### 📅 {calendar.month_name[month]} {year}")
    cal = calendar.Calendar()
    days = list(cal.itermonthdates(year, month))
    weeks = [days[i:i + 7] for i in range(0, len(days), 7)]

    for week in weeks:
        cols = st.columns(7)
        for i, day in enumerate(week):
            if day.month != month:
                cols[i].empty()
                continue

            if day in grouped_data.groups:
                group = grouped_data.get_group(day)
                amt = group['Amt'].sum()
                label = f"📌 {day.day}\n💰 ${amt:,.0f}\n🧾 {len(group)}"
                if cols[i].button(label, key=f"{year}-{month:02d}-{day.day:02d}"):
                    st.session_state.clicked_date = day
                    st.rerun()
            else:
                cols[i].markdown(
                    f"<div style='text-align:center; color:gray;'>{day.day}</div>",
                    unsafe_allow_html=True
                )

# --- TABS ---
tab_apr, tab_may, tab_jun, tab_summary = st.tabs(["🗓️ April", "🗓️ May", "🗓️ June", "📋 Summary"])

with tab_apr:
    draw_calendar(2025, 4, grouped)

with tab_may:
    draw_calendar(2025, 5, grouped)

with tab_jun:
    draw_calendar(2025, 6, grouped)

# --- SUMMARY TAB ---
with tab_summary:
    st.markdown("## 📋 Transaction Summary")

    full_dates = pd.date_range("2025-04-01", "2025-06-30").date
    available_dates = sorted(grouped.groups.keys())
    missing = sorted(set(full_dates) - set(available_dates))

    summary = []
    for d in available_dates:
        g = grouped.get_group(d)
        summary.append({
            "Date": d.strftime("%d-%b-%Y"),
            "Transactions": len(g),
            "Total Amount": f"${g['Amt'].sum():,.0f}",
            "Files": ", ".join(g['File'].dropna().astype(str).str.strip())
        })

    df_summary = pd.DataFrame(summary)
    st.dataframe(df_summary, use_container_width=True)

    st.download_button(
        "⬇️ Download Summary CSV",
        df_summary.to_csv(index=False).encode('utf-8'),
        file_name="transaction_summary.csv"
    )

    st.markdown(f"### ✅ Recorded Days: **{len(available_dates)} / {len(full_dates)}**")
    st.markdown(f"### ❌ Missing Days: **{len(missing)}**")

    if missing:
        with st.expander("📅 View Missing Dates"):
            st.markdown('\n'.join(f"• {d.strftime('%d-%b-%Y')}" for d in missing))
    else:
        st.success("All dates are covered for April–June 2025.")

    st.markdown(f"### 💰 Total Amount: **${df['Amt'].sum():,.2f}**")

# --- DETAILS ---
if clicked_date:
    st.markdown(f"## 🧾 Details for {clicked_date.strftime('%d %b %Y')}")
    with st.spinner("🔍 Loading details..."):
        if clicked_date in grouped.groups:
            sub_df = grouped.get_group(clicked_date)
            # Use 2 columns for better mobile compatibility
            num_cols = 2
            cols = st.columns(num_cols)


            for i, (_, row) in enumerate(sub_df.iterrows()):
                fname = str(row['File']).strip() if pd.notna(row['File']) else "unknown"
                img_name = f"{fname}.jpg"
                img_path = os.path.join("data", img_name)

                with cols[i % num_cols]:
                    if img_name in images:
                        st.image(img_path, use_container_width=True, caption=f"${row['Amt']:,.2f}")
                        with st.expander("Details"):
                            st.markdown(f"**Date:** {clicked_date.strftime('%d %b %Y')}")
                            st.markdown(f"**Amount:** ${row['Amt']:,.2f}")
                            st.markdown(f"**File:** {fname}")
                    else:
                        st.warning(f"⚠️ Image not found: {img_name}")
        else:
            st.error("❌ No records found for this date.")

st.markdown("---")
st.caption("📊 Generated by Audit Automation · Streamlit")
