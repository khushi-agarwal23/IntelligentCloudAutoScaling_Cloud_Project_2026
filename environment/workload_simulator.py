"""Workload Simulator for E-Commerce Autoscaling RL Environment.

This module provides the WorkloadSimulator class that generates or replays realistic
workload patterns for cloud autoscaling environments. It supports:
1. Loading and normalizing Alibaba 2018 cluster trace data (machine_usage.csv format).
2. Generating realistic synthetic e-commerce workload patterns with diurnal sinusoidal
   cycles, stochastic flash sale spikes, and realistic noise.
3. Simulating request response time using a queuing latency model based on instance capacity.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, Optional, Union

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class WorkloadSimulator:
    """Simulates incoming traffic and resource utilization for e-commerce cloud instances.

    Can replay real-world Alibaba Cloud 2018 cluster trace data or synthesize
    diurnal e-commerce traffic with flash-sale spikes and Gaussian noise.

    Attributes:
        data_path: Optional path to the Alibaba trace CSV file.
        episode_length: Number of time steps in a single episode (default 288 for 24h at 5-min steps).
        seed: Random seed for reproducibility.
        capacity: Request serving capacity per application instance (requests/second).
        base_latency: Baseline latency when instances are unloaded (milliseconds).
        load_factor: Latency scaling coefficient under load (milliseconds).
        max_response_time: Upper bound on simulated response time (milliseconds).
        min_request_rate: Lower bound on request rate (requests/second).
        max_request_rate: Upper bound on request rate (requests/second).
        data_source: Origin of workload data ('alibaba_trace' or 'synthetic').
    """

    # Expected column schema for Alibaba 2018 cluster trace machine_usage.csv
    ALIBABA_COLUMNS = [
        "machine_id",
        "time_stamp",
        "cpu_util_percent",
        "mem_util_percent",
        "mem_gig",
        "mpki",
        "net_in",
        "net_out",
        "disk_io_percent",
    ]

    # Common column schemas for UCI Online Retail II dataset
    UCI_RETAIL_COLUMNS = [
        "Invoice",
        "StockCode",
        "Description",
        "Quantity",
        "InvoiceDate",
        "Price",
        "Customer ID",
        "Country",
    ]

    def __init__(
        self,
        data_path: Optional[Union[str, Path]] = None,
        episode_length: int = 288,
        seed: int = 42,
        capacity: float = 200.0,
        base_latency: float = 50.0,
        load_factor: float = 200.0,
        max_response_time: float = 5000.0,
        min_request_rate: float = 100.0,
        max_request_rate: float = 8000.0,
    ) -> None:
        """Initialize the WorkloadSimulator.

        Args:
            data_path: Optional path to Alibaba 2018 cluster trace CSV file.
            episode_length: Length of an episode in steps (default 288: 24h at 5-min intervals).
            seed: Random seed for reproducibility.
            capacity: Per-instance capacity in requests/second (default 200.0).
            base_latency: Base processing latency in milliseconds (default 50.0).
            load_factor: Load factor multiplier for queuing delay in ms (default 200.0).
            max_response_time: Maximum allowable response time cap in ms (default 5000.0).
            min_request_rate: Minimum baseline request rate in requests/sec (default 100.0).
            max_request_rate: Maximum baseline request rate in requests/sec (default 8000.0).
        """
        self.data_path = Path(data_path) if data_path is not None else None
        self.episode_length = int(episode_length)
        self.seed = int(seed)
        self.capacity = float(capacity)
        self.base_latency = float(base_latency)
        self.load_factor = float(load_factor)
        self.max_response_time = float(max_response_time)
        self.min_request_rate = float(min_request_rate)
        self.max_request_rate = float(max_request_rate)

        # Internal workload series buffers (length == episode_length)
        self._request_rates = np.zeros(self.episode_length, dtype=np.float32)
        self._cpu_utils = np.zeros(self.episode_length, dtype=np.float32)
        self._mem_utils = np.zeros(self.episode_length, dtype=np.float32)
        self.data_source: str = "synthetic"

        # Initialize pseudo-random number generator
        self.rng = np.random.default_rng(self.seed)

        # Load real trace if available; otherwise fall back to synthetic data
        self._initialize_workload()

    def _initialize_workload(self) -> None:
        """Load Alibaba trace or UCI Online Retail dataset if available; otherwise generate synthetic traffic."""
        if self.data_path is not None and self.data_path.exists():
            try:
                # Inspect file to detect format
                sample_df = pd.read_csv(self.data_path, nrows=10)
                cols_lower = [str(c).strip().lower() for c in sample_df.columns]

                # Check if this matches UCI Online Retail format
                uci_indicators = ["invoicedate", "invoice", "quantity", "stockcode", "price"]
                if any(ind in cols_lower for ind in uci_indicators):
                    self._load_uci_retail_trace(self.data_path)
                    return

                # Otherwise try Alibaba format
                self._load_alibaba_trace(self.data_path)
                return
            except Exception as exc:
                logger.warning(
                    "Failed to load dataset trace from '%s': %s. "
                    "Falling back to synthetic traffic generator.",
                    self.data_path,
                    exc,
                )

        self._generate_synthetic_workload()

    def _load_uci_retail_trace(self, path: Path) -> None:
        """Load and process UCI Online Retail II dataset into time-series workload trace.

        UCI Online Retail II contains e-commerce transaction logs (Invoices, Quantities,
        InvoiceDate, Prices, etc.). We aggregate transactions into 5-minute time intervals
        to construct real-world e-commerce request rate, transaction volume, and derive
        realistic CPU and memory load.

        Args:
            path: Path to UCI Online Retail CSV file.
        """
        logger.info("Loading UCI Online Retail II dataset from %s", path)
        df = pd.read_csv(path)

        # Standardize column names
        col_map = {c: c.strip().lower() for c in df.columns}
        df = df.rename(columns=col_map)

        # Identify date column
        date_col = None
        for candidate in ["invoicedate", "invoice_date", "date", "timestamp", "time_stamp"]:
            if candidate in df.columns:
                date_col = candidate
                break

        if date_col is None:
            raise ValueError("UCI Online Retail dataset requires an InvoiceDate column.")

        df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
        df = df.dropna(subset=[date_col]).sort_values(date_col)

        # Group into 5-minute bins (or resample to episode_length)
        df.set_index(date_col, inplace=True)
        # Transactions count per bin
        resampled = df.resample("5min").size().rename("requests")
        resampled_quantities = df["quantity"].resample("5min").sum().abs().fillna(0) if "quantity" in df.columns else resampled

        # If empty or too few bins, fallback
        if len(resampled) < 10:
            raise ValueError("UCI Online Retail resampled series contains too few data points.")

        # Take a continuous slice of length episode_length (or peak activity day)
        if len(resampled) > self.episode_length:
            # Pick a 24h window (288 steps) with high activity (e.g. peak rolling sum)
            rolling_traffic = resampled.rolling(self.episode_length).sum()
            peak_end_idx = rolling_traffic.argmax()
            start_idx = max(0, peak_end_idx - self.episode_length + 1)
            active_slice = resampled.iloc[start_idx : start_idx + self.episode_length]
            active_qty = resampled_quantities.iloc[start_idx : start_idx + self.episode_length]
        else:
            active_slice = resampled
            active_qty = resampled_quantities

        raw_req = active_slice.to_numpy(dtype=np.float64)
        raw_qty = active_qty.to_numpy(dtype=np.float64)

        # Resample/interpolate to exact episode_length if needed
        if len(raw_req) != self.episode_length:
            orig_indices = np.linspace(0, len(raw_req) - 1, self.episode_length)
            sample_indices = np.arange(len(raw_req))
            raw_req = np.interp(orig_indices, sample_indices, raw_req)
            raw_qty = np.interp(orig_indices, sample_indices, raw_qty)

        # Normalize request rate into realistic server requests/sec range [min_req, max_req]
        r_min, r_max = np.nanmin(raw_req), np.nanmax(raw_req)
        if r_max > r_min:
            norm_traffic = (raw_req - r_min) / (r_max - r_min)
        else:
            norm_traffic = np.full(self.episode_length, 0.5)

        request_rate = self.min_request_rate + norm_traffic * (self.max_request_rate - self.min_request_rate)
        request_rate = np.clip(request_rate, self.min_request_rate, self.max_request_rate)

        # Derive simulated CPU & memory utilization matching real-world e-commerce behavior:
        # baseline idle CPU + proportional CPU with noise
        cpu_util = 15.0 + norm_traffic * 75.0 + self.rng.normal(0.0, 2.5, size=self.episode_length)
        cpu_util = np.clip(cpu_util, 5.0, 98.0)

        # Memory utilization tracks active sessions/transactions
        q_min, q_max = np.nanmin(raw_qty), np.nanmax(raw_qty)
        qty_norm = (raw_qty - q_min) / (q_max - q_min + 1e-6) if q_max > q_min else norm_traffic
        mem_util = 25.0 + (0.6 * norm_traffic + 0.4 * qty_norm) * 60.0 + self.rng.normal(0.0, 2.0, size=self.episode_length)
        mem_util = np.clip(mem_util, 10.0, 95.0)

        self._request_rates = request_rate.astype(np.float32)
        self._cpu_utils = cpu_util.astype(np.float32)
        self._mem_utils = mem_util.astype(np.float32)
        self.data_source = "uci_online_retail"
        logger.info(
            "Successfully loaded UCI Online Retail workload with %d steps.",
            self.episode_length,
        )

    def _load_alibaba_trace(self, path: Path) -> None:
        """Load and normalize Alibaba 2018 cluster trace data from CSV.

        Expected format: machine_usage.csv
        Columns: machine_id, time_stamp, cpu_util_percent, mem_util_percent,
                 mem_gig, mpki, net_in, net_out, disk_io_percent

        Args:
            path: Path to the Alibaba trace CSV file.
        """
        logger.info("Loading Alibaba cluster trace from %s", path)

        # Check if file has header or not by reading a sample
        sample_df = pd.read_csv(path, nrows=5)
        has_header = False
        if any(col in sample_df.columns for col in ["cpu_util_percent", "machine_id", "time_stamp"]):
            has_header = True

        if has_header:
            df = pd.read_csv(path)
        else:
            df = pd.read_csv(path, header=None, names=self.ALIBABA_COLUMNS)

        # Ensure required columns are present
        required_cols = ["cpu_util_percent", "mem_util_percent"]
        for col in required_cols:
            if col not in df.columns:
                raise ValueError(f"Required column '{col}' missing from Alibaba trace CSV.")

        # Ensure time_stamp is present or create synthetic monotonic index
        if "time_stamp" in df.columns:
            df = df.sort_values("time_stamp")
        else:
            df["time_stamp"] = np.arange(len(df))

        # Handle multi-machine cluster traces by averaging across machines per timestamp
        if "machine_id" in df.columns and df["machine_id"].nunique() > 1:
            numeric_cols = [c for c in df.columns if c not in ["machine_id", "time_stamp"] and pd.api.types.is_numeric_dtype(df[c])]
            df = df.groupby("time_stamp")[numeric_cols].mean().reset_index()

        df = df.dropna(subset=["cpu_util_percent", "mem_util_percent"]).reset_index(drop=True)

        if len(df) == 0:
            raise ValueError("Alibaba trace CSV contains no valid data rows.")

        raw_cpu = df["cpu_util_percent"].to_numpy(dtype=np.float64)
        raw_mem = df["mem_util_percent"].to_numpy(dtype=np.float64)

        # Check if values are normalized to [0, 1] instead of [0, 100]
        if np.nanmax(raw_cpu) <= 1.05:
            raw_cpu = raw_cpu * 100.0
        if np.nanmax(raw_mem) <= 1.05:
            raw_mem = raw_mem * 100.0

        cpu_util = np.clip(raw_cpu, 0.0, 100.0)
        mem_util = np.clip(raw_mem, 0.0, 100.0)

        # Derive request rate from cluster workload:
        # If network in/out is present, use combined traffic + CPU signal, else use CPU
        if "net_in" in df.columns and pd.api.types.is_numeric_dtype(df["net_in"]):
            net_in = df["net_in"].to_numpy(dtype=np.float64)
            net_min, net_max = np.nanmin(net_in), np.nanmax(net_in)
            if net_max > net_min:
                net_norm = (net_in - net_min) / (net_max - net_min)
                load_signal = 0.65 * net_norm + 0.35 * (cpu_util / 100.0)
            else:
                load_signal = cpu_util / 100.0
        else:
            load_signal = cpu_util / 100.0

        request_rate = self.min_request_rate + load_signal * (self.max_request_rate - self.min_request_rate)
        request_rate = np.clip(request_rate, self.min_request_rate, self.max_request_rate)

        # Resample or interpolate to exactly episode_length steps
        n_points = len(df)
        if n_points != self.episode_length:
            orig_indices = np.linspace(0, n_points - 1, self.episode_length)
            sample_indices = np.arange(n_points)
            cpu_util = np.interp(orig_indices, sample_indices, cpu_util)
            mem_util = np.interp(orig_indices, sample_indices, mem_util)
            request_rate = np.interp(orig_indices, sample_indices, request_rate)

        self._request_rates = request_rate.astype(np.float32)
        self._cpu_utils = cpu_util.astype(np.float32)
        self._mem_utils = mem_util.astype(np.float32)
        self.data_source = "alibaba_trace"
        logger.info("Successfully loaded %d Alibaba trace steps.", self.episode_length)

    def _generate_synthetic_workload(self) -> None:
        """Generate realistic synthetic e-commerce traffic.

        Components:
        1. Diurnal sinusoidal base pattern representing time-of-day traffic:
           Trough in early morning (~04:00), peak in late afternoon/evening (~18:00).
        2. Flash sale spikes: Sudden bursts simulating high-demand promotional events.
        3. Gaussian noise: Stochastic variations in real-time user activity.
        """
        # Time steps across 24 hours (288 steps -> 5 minutes each)
        steps = np.arange(self.episode_length)
        hours = (steps / self.episode_length) * 24.0

        # 1. Base Diurnal Cycle:
        # Negative cosine shifted so lowest traffic is at ~04:00 AM, highest at ~16:00-19:00
        diurnal_1 = -np.cos(2.0 * np.pi * (hours - 4.0) / 24.0)
        # Secondary harmonic for evening checkout surge
        diurnal_2 = 0.3 * np.sin(4.0 * np.pi * (hours - 10.0) / 24.0)
        diurnal_combined = diurnal_1 + diurnal_2

        # Normalize diurnal curve to [0, 1]
        diurnal_norm = (diurnal_combined - diurnal_combined.min()) / (
            diurnal_combined.max() - diurnal_combined.min() + 1e-6
        )

        # Baseline request rate spans min_request_rate to ~60% of max_request_rate
        base_rate = self.min_request_rate + diurnal_norm * (
            (self.max_request_rate * 0.55) - self.min_request_rate
        )

        # 2. Flash Sale Spikes:
        # Generate 2-3 flash sale bursts during active hours (step 60 to 250)
        spikes = np.zeros(self.episode_length, dtype=np.float64)
        num_flash_sales = self.rng.integers(2, 4)
        flash_sale_centers = self.rng.choice(
            np.arange(60, min(250, self.episode_length - 20)),
            size=num_flash_sales,
            replace=False,
        )

        for center in flash_sale_centers:
            # Amplitude: sudden burst adding 2000 - 3800 requests/sec
            amplitude = self.rng.uniform(2000.0, 3800.0)
            # Duration: standard deviation between 4 and 10 steps (20 to 50 minutes)
            width = self.rng.uniform(4.0, 10.0)
            # Bell curve for flash sale buildup and decay
            spike_curve = amplitude * np.exp(-0.5 * ((steps - center) / width) ** 2)
            spikes += spike_curve

        # 3. Gaussian Noise:
        noise = self.rng.normal(0.0, 120.0, size=self.episode_length)

        total_request_rate = np.clip(
            base_rate + spikes + noise,
            self.min_request_rate,
            self.max_request_rate,
        )

        # 4. Realistic CPU and Memory Utilization:
        # CPU tracks request load closely with random variations
        norm_load = (total_request_rate - self.min_request_rate) / (
            self.max_request_rate - self.min_request_rate + 1e-6
        )
        synthetic_cpu = 15.0 + norm_load * 72.0 + self.rng.normal(0.0, 3.5, size=self.episode_length)
        synthetic_cpu = np.clip(synthetic_cpu, 5.0, 98.0)

        # Memory tracks load with session memory buffering
        synthetic_mem = 25.0 + norm_load * 55.0 + self.rng.normal(0.0, 2.5, size=self.episode_length)
        synthetic_mem = np.clip(synthetic_mem, 10.0, 95.0)

        self._request_rates = total_request_rate.astype(np.float32)
        self._cpu_utils = synthetic_cpu.astype(np.float32)
        self._mem_utils = synthetic_mem.astype(np.float32)
        self.data_source = "synthetic"

    def simulate_response_time(self, request_rate: float, active_instances: int) -> float:
        """Simulate end-to-end response time using a queuing latency model.

        Formula:
            response_time = base_latency + (request_rate / (active_instances * capacity)) * load_factor

        Args:
            request_rate: Incoming request rate in requests/sec.
            active_instances: Number of healthy active application instances.

        Returns:
            Simulated response time in milliseconds, bounded between
            base_latency and max_response_time.
        """
        instances = max(1, int(active_instances))
        total_capacity = max(1e-6, instances * self.capacity)
        utilization = max(0.0, float(request_rate)) / total_capacity
        latency = self.base_latency + utilization * self.load_factor

        return float(np.clip(latency, self.base_latency, self.max_response_time))

    def get_workload(self, step: int, active_instances: int = 1) -> Dict[str, float]:
        """Retrieve workload metrics for a given step.

        Args:
            step: Discrete time step index (0-indexed). Handled cyclically modulo episode_length.
            active_instances: Number of active instances used to compute simulated response time.
                Defaults to 1 if not explicitly provided.

        Returns:
            Dictionary containing:
                - 'request_rate' (float): Incoming requests per second.
                - 'cpu_util' (float): Percentage CPU utilization (0-100).
                - 'memory_util' (float): Percentage memory utilization (0-100).
                - 'response_time' (float): Simulated response latency in milliseconds.
        """
        idx = int(step) % self.episode_length
        req_rate = float(self._request_rates[idx])
        cpu_u = float(self._cpu_utils[idx])
        mem_u = float(self._mem_utils[idx])
        rt = self.simulate_response_time(req_rate, active_instances)

        return {
            "request_rate": req_rate,
            "cpu_util": cpu_u,
            "memory_util": mem_u,
            "response_time": rt,
        }

    def reset(self, seed: Optional[int] = None) -> None:
        """Reset the simulator with an optional new random seed.

        If using synthetic data, regenerates traffic with new flash sales.

        Args:
            seed: Optional integer seed for reproducible traffic generation.
        """
        if seed is not None:
            self.seed = int(seed)
            self.rng = np.random.default_rng(self.seed)

        if self.data_source == "synthetic":
            self._generate_synthetic_workload()
