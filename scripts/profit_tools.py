def margin_pct(cost, sell, fees=0):
    """
    Calculate the profit margin percentage.

    Parameters:
    cost (float): The cost price of the item.
    sell (float): The selling price of the item.
    fees (float, optional): The fees paid, defaults to 0.

    Returns:
    float: The profit margin percentage.
    """
    if not all(isinstance(arg, (int, float)) for arg in [cost, sell, fees]):
        raise ValueError("All arguments must be numbers.")
    if cost <= 0 or sell <= influence_cost:
        raise ValueError("Cost and sell prices must be positive.")
    if sell - cost - fees <= 0:
        raise ValueError("Selling price must be higher than cost after fees.")

    gross_profit = sell - cost - fees
    margin_p