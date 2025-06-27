
# Stock Class needs to hold its symbol and its price
# Intially, current price will be a given value.
# It can then be updated to fetch real-time price from an API (yahoo finance).

class Stock:
    def __init__(self, symbol, current_price):
        self.symbol = symbol
        self._price = current_price
    
    def current_price(self):
        return self._price  
    

# Portfolio Class needs to hold a list of Stock objects and a target allocation
# It also needs to hold the current holdings of the portfolio

# It needs to calculate the current value of the portfolio
# It needs to calculate the current allocation of the portfolio
# It needs to calculate the rebalance amount for each stock

# Once the rebalance amount is calculated, it needs to update the holdings of the portfolio

# I am adding a list of all tradable stocks to the Portfolio class so I can deal with stocks outside my initial holdings
# (i.e. if I have a target allocation of 50% for a stock that I don't own, I need to buy it, therefore the "portfolio" needs to know about it)
# It will also allow me to validate that a new stock added to the portfolio is valid

class Portfolio:
    def __init__(self, all_tradable_stocks: list[Stock], target_allocation: dict[str, float], initial_holdings: dict[str, float] = None):
        
        if not sum(target_allocation.values()) == 1.0:
            raise ValueError("Target allocation percentages must sum to 1.0")

        self.target_allocation = target_allocation
        self.stock_objects = {stock.symbol: stock for stock in all_tradable_stocks}
        self.holdings = initial_holdings if initial_holdings is not None else {}

        for symbol in self.target_allocation:
            if symbol not in self.stock_objects:
                raise ValueError(f"Stock '{symbol}' in target allocation is not in tradable stocks list.")

    def add_position(self, symbol: str, shares: float):
        if symbol not in self.stock_objects:
            raise ValueError(f"Error: Cannot add position for '{symbol}'. It is not a known tradable stock.")
        if shares > 0:
            self.holdings[symbol] = self.holdings.get(symbol, 0.0) + shares

    def get_total_value(self) -> float:
        total_value = 0.0
        for symbol, shares in self.holdings.items():
            total_value += shares * self.stock_objects[symbol].current_price()
        return total_value

    # This function will print the current state of the portfolio
    # Helpful for monitoring and debuging

    def get_current_allocation(self):
        total_value = self.get_total_value()
        if total_value == 0:
            print("  Portfolio is currently empty.")
            return
            
        print(f"Total Portfolio Value: ${total_value:,.2f}")
        for symbol, shares in sorted(self.holdings.items()):
            value = shares * self.stock_objects[symbol].current_price()
            percentage = (value / total_value) * 100 if total_value > 0 else 0
            if percentage > 0:
                print(f"  {symbol}: {shares:.4f} shares, Value: ${value:,.2f} ({percentage:.2f}%)")

    # To rebalance the portfolio first calculate the total value of the portfolio
    # Then calculate the target value for each stock
    # Then calculate the current value for each stock
    # Then calculate the difference between the target value and the current value
    # Then calculate the rebalance amount for each stock

    # Given that I can either buy or sell (or do nothing), the posible actions are:
    # If the difference is greater than 0.01, add it to the buy list
    # If the difference is less than -0.01, add it to the sell list
    # If the difference is between -0.01 and 0.01, do nothing

    # Its better to have a small margin than to be deterministic with the numbers, as stock prices fluctuate real-time 

    def create_rebalance_plan(self) -> dict[str, list]:
        total_portfolio_value = self.get_total_value()
        actions = {"buy": [], "sell": []}

        # Quick check to see if the portfolio is empty
        if total_portfolio_value == 0:
            return actions
        
        # bug found: If the target allocation does not have the same stocks as the
        # total market stock, the rebalance plan will not work as expected
        # because it wont be assigned a 0 in my target allocation

        # to fix this, I need to add the missing stocks to the target allocation
        # and assign them a 0 percentage
        
        for symbol in self.stock_objects:
            if symbol not in self.target_allocation:
                self.target_allocation[symbol] = 0.0
        
        for symbol, target_percent in self.target_allocation.items():
            target_value = total_portfolio_value * target_percent
            current_value = self.holdings.get(symbol, 0.0) * self.stock_objects[symbol].current_price()
            value_difference = target_value - current_value
            
            if value_difference > 0.01:
                actions["buy"].append({"symbol": symbol, "amount_in_dollars": round(value_difference, 2)})
            elif value_difference < -0.01:
                actions["sell"].append({"symbol": symbol, "amount_in_dollars": round(abs(value_difference), 2)})
        return actions


    # Once we have the plan (buy and sell orders inside "actions"), we could execute it
    # We will need to update the holdings of the portfolio

    def execute_rebalance(self, plan: dict[str, list]):
       
        for order in plan.get("sell", []):
            symbol, amount_to_sell = order["symbol"], order["amount_in_dollars"]
            price = self.stock_objects[symbol].current_price()
            # Quick check to see if the stock has a positive price
            if price > 0:
                shares_to_sell = amount_to_sell / price
                # Update the holdings
                self.holdings[symbol] = max(0.0, self.holdings.get(symbol, 0.0) - shares_to_sell)

        for order in plan.get("buy", []):
            symbol, amount_to_buy = order["symbol"], order["amount_in_dollars"]
            price = self.stock_objects[symbol].current_price()
            # Quick check to see if the stock has a positive price
            if price > 0:
                shares_to_buy = amount_to_buy / price
                # Update the holdings
                self.holdings[symbol] = self.holdings.get(symbol, 0.0) + shares_to_buy


if __name__ == "__main__":
    # 1. Define all tradable stocks in the market
    all_stocks = [
        Stock("AAPL", 150.00),
        Stock("META", 300.00),
        Stock("GOOG", 135.00),
        Stock("MSFT", 250.00),
    ]

    # 2. Define our initial holdings
    initial_holdings = {
        "AAPL": 10.0,
        "GOOG": 5.0,
        "MSFT": 8.0,
    }
    

    # 3. Define our desired portfolio allocation.
    my_target_allocation = {
        "AAPL": 0.50,
        "META": 0.30,
        "GOOG": 0.20
    }

    # 4. Create the portfolio
    portfolio = Portfolio(all_stocks, my_target_allocation, initial_holdings)

    # 5. Check the current state of the portfolio
    portfolio.get_current_allocation()

    # 6. Show Target Allocation
    print("\n--- Target Allocation ---")
    for symbol, target_percent in my_target_allocation.items():
        print(f"  {symbol}: {target_percent * 100:.2f}%")
    print("\n")

    # 7. Create the rebalance plan.
    rebalance_plan = portfolio.create_rebalance_plan()

    if rebalance_plan["buy"]:
        print("Orders to BUY:")
        for order in rebalance_plan["buy"]:
            print(f"  Buy ${order['amount_in_dollars']:,.2f} of {order['symbol']}")
    if rebalance_plan["sell"]:
        print("Orders to SELL:")
        for order in rebalance_plan["sell"]:
            print(f"  Sell ${order['amount_in_dollars']:,.2f} of {order['symbol']}")
    
    if not rebalance_plan["buy"] and not rebalance_plan["sell"]:
        print("Portfolio is already balanced. No trades needed.")
    

    # 8. Execute the rebalance plan
    portfolio.execute_rebalance(rebalance_plan)
    
    # 9. Check the current state of the portfolio
    portfolio.get_current_allocation()