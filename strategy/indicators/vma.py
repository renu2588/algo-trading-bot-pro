"""
Volume Moving Average (VMA) indicator implementation.

VMA is a moving average weighted by trading volume.
"""

from typing import Optional, List
import pandas as pd
import numpy as np
from .base import BaseIndicator


class VMA(BaseIndicator):
    """
    Volume Moving Average indicator.

    VMA (also called VWMA - Volume Weighted Moving Average) gives more weight
    to periods with higher trading volume.
    """

    def __init__(self, period: int = 20) -> None:
        """
        Initialize VMA indicator.

        Args:
            period: Number of periods for VMA calculation (default: 20)

        Raises:
            ValueError: If period < 1
        """
        super().__init__(name=f"VMA_{period}", period=period)
        self.price_values: List[float] = []
        self.volume_values: List[float] = []

    def calculate(self, prices: pd.Series, volumes: pd.Series) -> pd.Series:
        """
        Calculate VMA from price and volume series.

        VMA = sum(Price * Volume) / sum(Volume)

        Args:
            prices: Price series
            volumes: Volume series

        Returns:
            Series of VMA values

        Raises:
            ValueError: If input series are invalid or have different lengths
            TypeError: If input is wrong type
        """
        self._validate_input(prices)
        self._validate_input(volumes)

        if len(prices) != len(volumes):
            raise ValueError("Price and Volume series must have same length")

        self._validate_period()

        price_array = prices.values.astype(float)
        volume_array = volumes.values.astype(float)

        # Validate that all volumes are non-negative
        if (volume_array < 0).any():
            raise ValueError("Volume values cannot be negative")

        self.price_values = price_array.tolist()
        self.volume_values = volume_array.tolist()

        vma_values = []

        # Calculate VMA for each window
        for i in range(len(price_array)):
            # Use period length window, or less if not enough data
            start_idx = max(0, i - self.period + 1)
            window_prices = price_array[start_idx:i + 1]
            window_volumes = volume_array[start_idx:i + 1]

            # Calculate volume-weighted average
            if window_volumes.sum() > 0:
                vma = np.sum(window_prices * window_volumes) / window_volumes.sum()
            else:
                # If no volume, use simple average
                vma = np.mean(window_prices)

            vma_values.append(vma)

        self.values = vma_values

        return pd.Series(vma_values)

    def update(self, price: float, volume: float) -> float:
        """
        Update VMA with new price and volume values.

        Args:
            price: New price value
            volume: New volume value

        Returns:
            Updated VMA value

        Raises:
            ValueError: If input values are invalid
        """
        if not np.isfinite(price):
            raise ValueError(f"Invalid price value: {price}")

        if volume < 0:
            raise ValueError(f"Volume cannot be negative: {volume}")

        self.price_values.append(price)
        self.volume_values.append(volume)

        # Calculate VMA for current window
        start_idx = max(0, len(self.price_values) - self.period)
        window_prices = np.array(self.price_values[start_idx:])
        window_volumes = np.array(self.volume_values[start_idx:])

        if window_volumes.sum() > 0:
            vma = np.sum(window_prices * window_volumes) / window_volumes.sum()
        else:
            vma = np.mean(window_prices)

        self.values.append(vma)

        return vma

    def is_ready(self) -> bool:
        """
        Check if VMA is ready for use.

        Returns:
            True if VMA has been calculated with at least one value
        """
        return len(self.values) >= 1

    def reset(self) -> None:
        """Reset VMA state."""
        super().reset()
        self.price_values = []
        self.volume_values = []

    def get_volume_profile(self) -> pd.DataFrame:
        """
        Get volume profile data.

        Returns:
            DataFrame with prices, volumes, and VMA values
        """
        return pd.DataFrame({
            "price": self.price_values,
            "volume": self.volume_values,
            "vma": self.values
        })

    @staticmethod
    def from_series(prices: pd.Series, volumes: pd.Series, period: int) -> "VMA":
        """
        Create and calculate VMA from price and volume series.

        Args:
            prices: Series of prices
            volumes: Series of volumes
            period: VMA period

        Returns:
            Initialized VMA indicator
        """
        vma = VMA(period=period)
        vma.calculate(prices, volumes)
        return vma
