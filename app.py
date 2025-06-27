# I will create a simple streamlit UI to interact with the portfolio rebalancer
# The UI will allow the user to input their target allocation and their current holdings
# The UI will also allow the user to input select the initial holdings of the portfolio

import streamlit as st
import pandas as pd

from portfolio import Portfolio
from portfolio import Stock

st.set_page_config(page_title="Portfolio Rebalancer", layout="wide")
st.title("Portfolio Rebalancer")
st.write("This app helps you rebalance your stock portfolio to match your target allocation.")

# 1. Define Investment Universe and Default values
ALL_STOCKS = [
    Stock("AAPL", 150.00), 
    Stock("META", 300.00), 
    Stock("GOOG", 135.00),
    Stock("MSFT", 450.00), 
    Stock("NVDA", 130.00)
]
DEFAULT_TARGET_ALLOCATION = {
    "AAPL": 0.30, "META": 0.20, "GOOG": 0.20, "MSFT": 0.20, "NVDA": 0.10
}

DEFAULT_INITIAL_HOLDINGS = {
    "AAPL": 10.0, "META": 5.0,
}

# 2. Create Portfolio
# We will use the session state to prevent the portfolio from being created multiple times and withstand refreshes
if 'portfolio' not in st.session_state: 
    st.session_state.target_allocation = DEFAULT_TARGET_ALLOCATION.copy()
    
    st.session_state.portfolio = Portfolio(
        ALL_STOCKS, 
        st.session_state.target_allocation,
        initial_holdings=DEFAULT_INITIAL_HOLDINGS
    )
    st.session_state.rebalance_plan = None


# 3. Sidebar for User Inputs
with st.sidebar:
    st.header("Your Current Holdings")
    st.write("Enter the number of shares you own for each stock.")

    with st.form("holdings_form"):
        share_inputs = {stock.symbol: st.number_input(
            f"Shares of {stock.symbol}", min_value=0.0,
            value=st.session_state.portfolio.holdings.get(stock.symbol, 0.0),
            step=1.0, format="%.4f"
        ) for stock in ALL_STOCKS}
        
        if st.form_submit_button("Update Portfolio Holdings"):
            st.session_state.portfolio = Portfolio(ALL_STOCKS, st.session_state.target_allocation)
            for symbol, shares in share_inputs.items():
                if shares > 0:
                    st.session_state.portfolio.add_position(symbol, shares)
            st.session_state.rebalance_plan = None
            st.success("Portfolio updated!")
            st.rerun()

    if st.button("Reset All"):
        st.session_state.target_allocation = DEFAULT_TARGET_ALLOCATION.copy()
        st.session_state.portfolio = Portfolio(ALL_STOCKS, st.session_state.target_allocation)
        st.session_state.rebalance_plan = None
        st.rerun()


# 4. Main Content

current_holdings_df = st.session_state.portfolio.get_holdings_dataframe()
total_value = st.session_state.portfolio.get_total_value()

# Section 1: Portfolio overview

st.header("Current Portfolio State")
if total_value == 0:
    st.info("Your portfolio is empty. Add some holdings in the sidebar to get started.")
else:
    st.metric(label="Total Portfolio Value", value=f"${total_value:,.2f}")
    st.dataframe(current_holdings_df.set_index('Symbol'), use_container_width=True)

st.divider()

# Section 2: Target Allocation
st.header("Target Allocation")
with st.expander("Edit Target Allocation", expanded=False):
    with st.form("target_form"):
        st.write("Use the sliders to set your desired allocation. The total must be 100%.")
        new_targets_percent = {}
        # Streamlit has prebuilt sliders
        for symbol, target_pct in st.session_state.target_allocation.items():
            new_targets_percent[symbol] = st.slider(
                f"Allocation for {symbol}", 0, 100, int(target_pct * 100)
            )
        
        total_allocation = sum(new_targets_percent.values())
        print("TOTAL total_allocation", total_allocation)
        st.write(f"**Total Allocation: {total_allocation}%**")

        if st.form_submit_button("Update Targets"):
            if not total_allocation == 100:
                st.error("Error: Total allocation must be exactly 100%. Please adjust the sliders.")
            else:
                # when a new target allocation is set, its best to create a "new" portfolio
                # this will ensure that the portfolio is updated with the new target allocation
                # even though is "counterintuitive", its better to do it this way when dealing with app state
                st.session_state.target_allocation = {s: p / 100.0 for s, p in new_targets_percent.items()}
                st.session_state.portfolio = Portfolio(
                    ALL_STOCKS,
                    st.session_state.target_allocation,
                    initial_holdings=st.session_state.portfolio.holdings
                )
                st.session_state.rebalance_plan = None
                st.success("Target allocation updated!")
                st.rerun()

# We show updated target allocation in a clean table
target_df = pd.DataFrame(list(st.session_state.target_allocation.items()), columns=['Symbol', 'Target'])
target_df['Target'] = target_df['Target'].apply(lambda x: f"{x:.2%}")
st.dataframe(target_df.set_index('Symbol'), use_container_width=True)

st.divider()

# Section 3: Rebalancing Actions
# For simplicity, we will only show the rebalance actions if the portfolio is not empty

if total_value > 0:
    st.divider()
    st.header("Rebalancing Actions")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Generate Rebalance Plan", type="primary", use_container_width=True):
            st.session_state.rebalance_plan = st.session_state.portfolio.create_rebalance_plan()

    if st.session_state.rebalance_plan:
        plan = st.session_state.rebalance_plan
        if not plan["buy"] and not plan["sell"]:
            st.success("Your portfolio is already balanced. No trades needed!")
            st.session_state.rebalance_plan = None # Clear the plan
            st.rerun()
        else:
            st.subheader("Recommended Trades")
            col_buy, col_sell = st.columns(2)
            with col_buy:
                st.write("**Buy Orders**")
                if plan["buy"]:
                    buy_df = pd.DataFrame(plan["buy"]).rename(columns={"symbol": "Symbol", "amount_in_dollars": "Amount ($)"})
                    st.dataframe(buy_df.set_index('Symbol'), use_container_width=True)
                else:
                    st.write("None")
            with col_sell:
                st.write("**Sell Orders**")
                if plan["sell"]:
                    sell_df = pd.DataFrame(plan["sell"]).rename(columns={"symbol": "Symbol", "amount_in_dollars": "Amount ($)"})
                    st.dataframe(sell_df.set_index('Symbol'), use_container_width=True)
                else:
                    st.write("None")
            with col2:
                if st.button("Execute Rebalance Plan", use_container_width=True):
                    st.session_state.portfolio.execute_rebalance(plan)
                    st.session_state.rebalance_plan = None # Clear the plan
                    st.success("Rebalance complete! Your portfolio is now updated.")
                    st.rerun()

