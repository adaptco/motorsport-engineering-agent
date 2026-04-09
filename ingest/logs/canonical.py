"""ingest/logs/canonical module."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ChannelSpec:
    canonical: str
    aliases: tuple[str, ...]
    unit_out: str


CANONICAL_CHANNELS: tuple[ChannelSpec, ...] = (
    ChannelSpec("timestamp_ms", ("timestamp_ms", "timecodes", "time_ms", "Time", "time", "seconds", "Seconds"), "ms"),
    ChannelSpec("lap_index", ("lap_index", "lap", "Lap", "lap_number", "LapNo", "Lap Number"), "count"),
    ChannelSpec("sector_index", ("sector_index", "sector", "Sector", "sector_number", "Sector Number"), "count"),
    ChannelSpec("lap_distance_m", ("lap_distance_m", "LapDist", "Lap Distance", "lap_distance", "Corr Lap Dist", "distance"), "m"),
    ChannelSpec("speed_mps", ("speed_mps", "Speed", "speed", "GPS Speed", "velocity kmh", "velocity_kmh", "velocity"), "m/s"),
    ChannelSpec("rpm", ("rpm", "RPM", "Engine RPM", "engine_rpm"), "rpm"),
    ChannelSpec("gear", ("gear", "Gear", "gear_number"), "count"),
    ChannelSpec("throttle_pct", ("throttle_pct", "Throttle", "TPS", "Throttle Pos", "Throttle Position", "ecu_throttle_pedal"), "%"),
    ChannelSpec("brake_pct", ("brake_pct", "Brake", "Brake Pos", "Brake Position", "BrakePressure", "Brake Pressure"), "%"),
    ChannelSpec("steering_deg", ("steering_deg", "Steering", "Steering Angle", "Raw_eps_steerangle_Rx"), "deg"),
    ChannelSpec("accel_lat_g", ("accel_lat_g", "LatAcc", "Lat Acc", "Lateral G", "X_Acceleration", "psm_acc_lat"), "g"),
    ChannelSpec("accel_long_g", ("accel_long_g", "LongAcc", "Long Acc", "Longitudinal G", "Y_Acceleration", "psm_acc_long"), "g"),
    ChannelSpec("yaw_rate_dps", ("yaw_rate_dps", "YawRate", "Yaw Rate"), "deg/s"),
    ChannelSpec("gps_lat_deg", ("gps_lat_deg", "GPS Latitude", "gps_lat", "latitude"), "deg"),
    ChannelSpec("gps_lon_deg", ("gps_lon_deg", "GPS Longitude", "gps_long", "longitude"), "deg"),
    ChannelSpec("coolant_temp_c", ("coolant_temp_c", "CoolantTemp", "Water Temp", "water_temp"), "C"),
    ChannelSpec("oil_temp_c", ("oil_temp_c", "Oil Temp", "oil_temp"), "C"),
    ChannelSpec("afr", ("afr", "AFR", "LambdaAFR"), "afr"),
    ChannelSpec("lambda", ("lambda", "Lambda"), "lambda"),
    ChannelSpec("fl_tire_temp_c", ("fl_tire_temp_c", "FL Tire Temp", "Tyre Temp FL", "tyre_temp_fl"), "C"),
    ChannelSpec("fr_tire_temp_c", ("fr_tire_temp_c", "FR Tire Temp", "Tyre Temp FR", "tyre_temp_fr"), "C"),
    ChannelSpec("rl_tire_temp_c", ("rl_tire_temp_c", "RL Tire Temp", "Tyre Temp RL", "tyre_temp_rl"), "C"),
    ChannelSpec("rr_tire_temp_c", ("rr_tire_temp_c", "RR Tire Temp", "Tyre Temp RR", "tyre_temp_rr"), "C"),
)

SUPPORTED_SOURCE_EXTENSIONS: dict[str, tuple[str, ...]] = {
    "motec": (".ld", ".ldx"),
    "iracing": (".ibt",),
    "aim": (".xrk", ".xrz"),
    "vbox": (".vbo",),
    "pi": (".mat", ".pds"),
    "haltech": (".csv", ".txt"),
    "aem": (".csv", ".txt"),
    "csv_export": (".csv", ".txt"),
}
