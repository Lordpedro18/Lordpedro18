import pandas as pd
import numpy as np

class Portfolio:
    """Clase que maneja un portafolio de inversión y ejecuta reequilibrio de activos basado en costos y liquidez del mercado."""
    
    def __init__(self, holdings, allocations, transaction_costs, traded_volume):
        """
        Inicializa el portafolio con posiciones actuales, asignaciones objetivo y restricciones de operación.

        holdings: Dict con el ticker como clave y (cantidad de acciones, precio actual) como valor.
        allocations: Dict con el ticker como clave y porcentaje objetivo de asignación (ej. 0.5 para 50%).
        transaction_costs: Dict con el ticker como clave y el costo de transacción (ej. 0.002 para 0.2%).
        traded_volume: Dict con el ticker como clave y el volumen negociado en la última hora.
        """
        self.holdings = holdings
        self.allocations = allocations
        self.transaction_costs = transaction_costs
        self.traded_volume = traded_volume
        self.rebalance_threshold = 0.02  # Solo rebalancear si la desviación es mayor al 2%
        self.liquidity_constraint = 0.001  # No operar más del 0.1% del volumen negociado

    def total_value(self):
        """Calcula el valor total del portafolio sumando todas las posiciones."""
        return sum(shares * price for shares, price in self.holdings.values())

    def rebalance_needed(self):
        """
        Determina si es necesario reequilibrar el portafolio basado en la desviación de asignación y costos de transacción.
        Retorna True si el rebalanceo es justificable, False si no es necesario.
        """
        total_value = self.total_value()
        
        # Calcular la asignación actual basada en la cantidad de acciones y su precio
        current_allocations = {
            ticker: (shares * price) / total_value 
            for ticker, (shares, price) in self.holdings.items()
        }
        
        # Evaluar si la desviación supera el umbral del 2%
        deviations = {
            ticker: abs(current_allocations[ticker] - self.allocations[ticker]) 
            for ticker in self.allocations
        }
        exceeds_threshold = any(deviations[ticker] > self.rebalance_threshold for ticker in deviations)

        if not exceeds_threshold:
            return False  # No es necesario reequilibrar si la diferencia es menor al umbral

        # Calcular costos de transacción estimados
        transaction_cost = sum(
            abs((total_value * self.allocations[ticker] / self.holdings[ticker][1]) - self.holdings[ticker][0]) *
            self.holdings[ticker][1] * self.transaction_costs[ticker]
            for ticker in self.holdings
        )

        total_adjustment_value = sum(
            abs((total_value * self.allocations[ticker] / self.holdings[ticker][1]) - self.holdings[ticker][0]) *
            self.holdings[ticker][1]
            for ticker in self.holdings
        )

        return total_adjustment_value > transaction_cost

    def apply_liquidity_constraint(self, trades):
        """Asegura que ninguna operación exceda el 0.1% del volumen negociado en la última hora."""
        return {
            ticker: min(trades[ticker], self.liquidity_constraint * self.traded_volume[ticker])
            for ticker in trades
        }

    def rebalance(self):
        """
        Ejecuta el reequilibrio si todas las condiciones se cumplen:
        - La desviación de asignación excede el umbral.
        - Los costos de transacción justifican la operación.
        - Se respeta el límite de volumen negociado.
        """
        if not self.rebalance_needed():
            print("No se necesita reequilibrar en este momento.")
            return {}

        total_value = self.total_value()
        new_holdings = {
            ticker: (total_value * self.allocations[ticker] / self.holdings[ticker][1])
            for ticker in self.allocations
        }

        trades = {
            ticker: round(new_holdings[ticker] - self.holdings[ticker][0]) 
            for ticker in self.holdings
        }

        # Aplicar restricciones de liquidez
        trades = self.apply_liquidity_constraint(trades)
        print("Instrucciones de reequilibrio:", trades)
        return trades

