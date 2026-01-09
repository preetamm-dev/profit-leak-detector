import streamlit as st
import pandas as pd

# ---------------- PAGE SETUP ----------------
st.set_page_config(page_title="Profit Leak Detector", layout="wide")

st.title("💸 Profit Leak Detector")
st.caption("Find which products are silently losing you money — and what to fix first.")

# ---------------- FILE UPLOAD ----------------
uploaded_file = st.file_uploader(
    "Upload your Shopify Orders CSV",
    type=["csv"]
)

# ---------------- NO FILE YET ----------------
if uploaded_file is None:
    st.info("Upload a CSV to begin the audit.")

    st.subheader("📄 Sample CSV Format")

    sample_csv = """order_id,sku,price,quantity,discount,refund,order_date
1001,SKU_A,999,1,0,0,2025-06-01
1002,SKU_A,999,1,200,0,2025-06-02
1003,SKU_A,999,1,0,999,2025-06-03
1004,SKU_B,499,2,100,0,2025-06-04
1005,SKU_B,499,2,0,0,2025-06-05
"""

    st.download_button(
        "⬇️ Download sample CSV",
        sample_csv,
        file_name="sample_profit_leak_data.csv",
        mime="text/csv"
    )

    st.stop()   # 🔴 IMPORTANT: stops app here

# ---------------- FROM HERE, FILE EXISTS ----------------
df = pd.read_csv(uploaded_file)

# ---------------- DATE PARSING ----------------
df["order_date"] = pd.to_datetime(df["order_date"], errors="coerce")

# ---------------- AUDIT WINDOW ----------------
st.subheader("📆 Audit Window")

audit_days = st.radio(
    "Select audit period",
    [7, 30, 90],
    horizontal=True
)

cutoff_date = df["order_date"].max() - pd.Timedelta(days=audit_days)
df = df[df["order_date"] >= cutoff_date]

# ---------------- DATA CONFIDENCE ----------------
st.subheader("📊 Data Confidence")

st.write(f"• Orders analyzed: **{len(df)}**")
st.write(f"• Unique SKUs: **{df['sku'].nunique()}**")

# ---------------- COST ----------------
st.subheader("💰 Cost Assumption")

cost_per_unit = st.number_input(
    "Average cost per unit (₹)",
    min_value=0.0,
    value=300.0,
    step=50.0
)

st.caption(
    "Use an approximate average cost. Exact per-product costing is NOT required."
)

# ---------------- REVENUE & PROFIT ----------------
df["gross_revenue"] = df["price"] * df["quantity"]
df["net_revenue"] = df["gross_revenue"] - df["discount"] - df["refund"]
df["cost"] = df["quantity"] * cost_per_unit
df["net_profit"] = df["net_revenue"] - df["cost"]

# ---------------- SKU SUMMARY ----------------
st.subheader("📦 Net Profit by Product (SKU)")

sku_summary = (
    df.groupby("sku")
    .agg(
        gross_revenue=("gross_revenue", "sum"),
        discounts=("discount", "sum"),
        refunds=("refund", "sum"),
        total_cost=("cost", "sum"),
        net_profit=("net_profit", "sum")
    )
    .reset_index()
    .sort_values("net_profit")
)

st.dataframe(sku_summary, use_container_width=True)

# ---------------- DECISIONS ----------------
st.subheader("🚨 Profit Leak Alerts & Decisions")

leaks = False

for _, row in sku_summary.iterrows():
    if row["net_profit"] < 0:
        leaks = True
        if row["refunds"] > row["discounts"]:
            action = "Investigate refunds"
            save = row["refunds"]
        else:
            action = "Reduce discounts"
            save = row["discounts"]

        st.error(
            f"""
            **SKU {row['sku']} is losing ₹{abs(row['net_profit']):,.0f}**

            👉 Recommended action: **{action}**
            Potential save: ₹{save:,.0f}
            """
        )

if not leaks:
    st.success("No profit leaks detected 👍")

# ---------------- PRIVACY ----------------
st.caption("🔐 Your data is processed in-session only. Nothing is stored.")