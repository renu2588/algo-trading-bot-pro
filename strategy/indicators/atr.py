"""
Average True Range (ATR) indicator implementation.

ATR measures volatility using true range calculations.
"""

from typing import Optional, List
import pandas as pd
import numpy as np
from .base import BaseIndicator


class ATR(BaseIndicator):
    """
    Average True Range indicator.

    ATR measures market volatility by analyzing the range of price movement.
    Uses Wilder's smoothing method (RMA - Running Moving Average).
    """

    def __init__(self, period: int = 14) -> None:
        """
        Initialize ATR indicator.

        Args:
            period: Number of periods for ATR calculation (default: 14)

        Raises:
            ValueError: If period < 1
        """
        super().__init__(name=f"ATR_{period}", period=period)
        self.high_values: List[float] = []
        self.low_values: List[float] = []
        self.close_values: List[float] = []
        self._true_ranges: List[float] = []
        self._previous_atr: Optional[float] = None
        self._initialized: bool = False
        self._multiplier: float = 1.0 / period

    def calculate(self, high: pd.Series, low: pd.Series, close: pd.Series) -> pd.Series:
        """
        Calculate ATR from OHLC data.

        True Range = max(H-L, abs(H-PC), abs(L-PC))
        where PC = Previous Close

        Args:
            high: High prices series
            low: Low prices series
            close: Close prices series

        Returns:
            Series of ATR values

        Raises:
            ValueError: If input series are invalid or have different lengths
            TypeError: If input is wrong type
        """
        self._validate_input(high)
        self._validate_input(low)
        self._validate_input(close)

        if not (len(high) == len(low) == len(close)):
            raise ValueError("High, Low, and Close series must have same length")

        self._validate_period()

        high_array = high.values.astype(float)
        low_array = low.values.astype(float)
        close_array = close.values.astype(float)

        self.high_values = high_array.tolist()
        self.low_values = low_array.tolist()
        self.close_values = close_array.tolist()

        # Calculate true ranges
        self._calculate_true_ranges()

        # Calculate ATR using Wilder's smoothing
        atr_values = []

        if len(self._true_ranges) >= self.period:
            # First ATR is simple average of true ranges
            atr = np.mean(self._true_ranges[:self.period])
            atr_values.append(atr)
            self._previous_atr = atr

            # Subsequent ATRs use Wilder's smoothing
            for i in range(self.period, len(self._true_ranges)):
                tr = self._true_ranges[i]
                atr = (self._previous_atr * (self.period - 1) + tr) / self.period
                atr_values.append(atr)
                self._previous_atr = atr

        self.values = atr_values
        self._initialized = True

        return pd.Series(atr_values)

    def update(self, high: float, low: float, close: float) -> float:
        """
        Update ATR with new OHLC values.

        Args:
            high: New high price
            low: New low price
            close: New close price

        Returns:
            Updated ATR value

        Raises:
            ValueError: If ATR not initialized or invalid prices
        """
        if not self._initialized or self._previous_atr is None:
            raise ValueError("ATR must be calculated with series first")

        if any(not np.isfinite(v) for v in [high, low, close]):
            raise ValueError(f"Invalid OHLC values: H={high}, L={low}, C={close}")

        if low > high:
            raise ValueError(f"Low ({low}) cannot be greater than High ({high})")

        # Calculate true range for new values
        previous_close = self.close_values[-1] if self.close_values else close
        tr = self._calculate_single_true_range(high, low, previous_close)

        # Update ATR using Wilder's smoothing
        atr = (self._previous_atr * (self.period - 1) + tr) / self.period

        self.values.append(atr)
        self.high_values.append(high)
        self.low_values.append(low)
        self.close_values.append(close)
        self._true_ranges.append(tr)
        self._previous_atr = atr

        return atr

    def is_ready(self) -> bool:
        """
        Check if ATR is ready for use.

        Returns:
            True if ATR has been calculated, False otherwise
        """
        return self._initialized and len(self.values) >= 1

    def reset(self) -> None:
        """Reset ATR state."""
        super().reset()
        self.high_values = []
        self.low_values = []
        self.close_values = []
        self._true_ranges = []
        self._previous_atr = None
        self._initialized = False

    def _calculate_true_ranges(self) -> None:
        """Calculate true range for all candles."""
        self._true_ranges = []

        for i in range(len(self.high_values)):
            if i == 0:
                # First candle: TR = H - L
                tr = self.high_values[i] - self.low_values[i]
            else:
                # Subsequent candles: TR = max(H-L, abs(H-PC), abs(L-PC))
                previous_close = self.close_values[i - 1]
                tr = self._calculate_single_true_range(
                    self.high_values[i],
                    self.low_values[i],
                    previous_close
                )

            self._true_ranges.append(tr)

    @staticmethod
    def _calculate_single_true_range(
        high: float,
        low: float,
        previous_close: float
    ) -> float:
        """
        Calculate true range for a single candle.

        Args:
            high: High price
            low: Low price
            previous_close: Previous close price

        Returns:
            True range value
        """
        tr1 = high - low
        tr2 = abs(high - previous_close)
        tr3 = abs(low - previous_close)
        return max(tr1, tr2, tr3)

    @staticmethod
    def from_ohlc(high: pd.Series, low: pd.Series, close: pd.Series, period: int) -> "ATR":
        """
        Create and calculate ATR from OHLC series.

        Args:
            high: Series of high prices
            low: Series of low prices
            close: Series of close prices
            period: ATR period

        Returns:
            Initialized ATR indicator
        """
        atr = ATR(period=period)
        atr.calculate(high, low, close)
        return atr
