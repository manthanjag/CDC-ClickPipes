import streamlit as st
import pandas as pd
import clickhouse_connect
import time
import datetime

# ⏱️ Auto-refresh every 2 minutes
st.query_params.update(update=int(time.time() // 120))

st.title("🌤️ Mumbai Weather Dashboard (Live, IST)")
st.caption("Powered by MySQL → ClickPipes → ClickHouse → Streamlit")

# 🔐 Secure credentials
client = clickhouse_connect.get_client(
    host=st.secrets["clickhouse"]["host"],
    user=st.secrets["clickhouse"]["user"],
    password=st.secrets["clickhouse"]["password"],
    secure=True,
    database='MySQL-CDC'  # Adjust if your DB name differs
)

# 🔹 Visual 1: Hourly Temperature Trends
st.subheader("📈 Temperature Trends (Hourly)")

# Optional date range filter (can be removed if not needed)
start_date = st.date_input("Start date", datetime.date.today() - datetime.timedelta(days=1))
end_date = st.date_input("End date", datetime.date.today())

query_mv = f"""
SELECT *
FROM temp_trend_mv
WHERE city = 'Mumbai'
  AND interval_time_ist BETWEEN toDateTime('{start_date}') AND toDateTime('{end_date + datetime.timedelta(days=1)}')
ORDER BY interval_time_ist
"""

result = client.query(query_mv)
df_mv = pd.DataFrame(result.result_rows, columns=result.column_names)

if not df_mv.empty:
    df_mv = df_mv.sort_values("interval_time_ist")
    st.line_chart(df_mv.set_index("interval_time_ist")[["avg_temp", "min_temp", "max_temp"]])
    with st.expander("📄 View Aggregated Data"):
        st.dataframe(df_mv)
else:
    st.warning("No data found in this time range.")

# 🔹 Visual 2: Latest Snapshot
st.subheader("🌡️ Latest Live Weather Snapshot")

query_latest = """
SELECT
    city,
    temperature,
    humidity,
    weather_description,
    toTimeZone(toDateTime(timestamp), 'Asia/Kolkata') AS ist_time
FROM live_weather_db_weather_data
WHERE city = 'Mumbai'
ORDER BY timestamp DESC
LIMIT 1
"""

latest = client.query(query_latest)
latest_df = pd.DataFrame(latest.result_rows, columns=latest.column_names)

if not latest_df.empty:
    row = latest_df.iloc[0]
    st.metric(label="Temperature (°C)", value=f"{row['temperature']}°")
    st.metric(label="Humidity (%)", value=f"{row['humidity']}%")
    st.write(f"**Description:** {row['weather_description']}")
    st.write(f"**Updated at:** {row['ist_time']} IST")
else:
    st.warning("No latest weather data found.")
