"""Streamlit decision-support dashboard."""
from __future__ import annotations
import streamlit as st
import pandas as pd
from decision_intelligence.database import connect
from decision_intelligence.risk_engine import assess_customer

st.set_page_config(page_title="Renewal Intelligence", page_icon="📈", layout="wide")
st.title("Enterprise Renewal Decision Intelligence")
st.caption("Transparent, local decision support powered by deterministic business rules.")
with connect() as con:
    customers = pd.read_sql_query("SELECT customer_id, customer_name FROM customers ORDER BY customer_name", con)
if customers.empty:
    st.error("No integrated data found. Run the data generator and ingestion pipeline first.")
    st.stop()
choice = st.selectbox("Select customer", customers["customer_name"].tolist())
customer_id = customers.loc[customers.customer_name.eq(choice), "customer_id"].iloc[0]
assessment = assess_customer(customer_id)
customer, contract = assessment["customer"], assessment["contract"]
col1,col2,col3 = st.columns(3)
col1.metric("Renewal risk", assessment["risk_level"])
col2.metric("Weighted score", f"{assessment['risk_score']} / 100")
col3.metric("Annual contract value", f"${contract['annual_contract_value']:,.0f}" if contract else "No contract")
st.subheader("Customer summary")
st.write(f"**{customer['customer_name']}** · {customer['segment']} · {customer['industry']} · {customer['region']}")
st.write(f"Account manager: **{customer['account_manager_name']}** ({customer['account_manager_email']})")
if contract:
    st.subheader("Contract")
    st.dataframe(pd.DataFrame([contract]), use_container_width=True, hide_index=True)
st.subheader("Why this customer has this risk")
if not assessment["factors"]: st.success("No configured renewal-risk factors are currently triggered.")
for factor in assessment["factors"]:
    with st.expander(f"{factor['points']} points — {factor['name']}", expanded=True):
        st.write(factor["explanation"])
        st.caption("Source records: " + ", ".join(factor["evidence_record_ids"]))
        st.info("Recommended action: " + factor["recommended_action"])
st.subheader("Recommended next actions")
for action in assessment["recommended_actions"]: st.write("• " + action)
with connect() as con:
    usage = pd.read_sql_query("SELECT event_date, active_users, seats_purchased, sessions, feature_adoption_pct FROM product_usage_events WHERE customer_id=? ORDER BY event_date", con, params=(customer_id,))
    tickets = pd.read_sql_query("SELECT ticket_id, opened_at, resolved_at, priority, ticket_status, ticket_category, csat_score, ticket_summary FROM support_tickets WHERE customer_id=? ORDER BY opened_at DESC", con, params=(customer_id,))
st.subheader("Product usage trend")
st.line_chart(usage.set_index("event_date")[["active_users", "seats_purchased"]])
st.dataframe(usage, use_container_width=True, hide_index=True)
st.subheader("Support history")
st.dataframe(tickets, use_container_width=True, hide_index=True)