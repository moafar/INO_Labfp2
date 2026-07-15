# src/transform/ergoespirometry.py
"""Decodifica los campos binarios de las pruebas de ergoespirometría."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
import struct
from typing import Final

import pandas as pd


RAW_VERSION: Final = 10
RAW_CHANNEL_COUNT: Final = 12
RAW_HEADER_SIZE: Final = 36
RAW_SIGNAL_COUNT: Final = 10
RAW_SIGNAL_DESCRIPTOR_SIZE: Final = 6
RAW_TRAILER_SIZE: Final = 230
MMHG_PER_KPA: Final = 7.50062
OLE_AUTOMATION_EPOCH: Final = datetime(1899, 12, 30)


# Los alias salvo elapsed_time_s son hipótesis funcionales. El identificador y
# el descriptor originales se conservan para no convertirlas en hechos.
SIGNAL_CATALOG: Final = {
    1: ("elapsed_time_s", "confirmed"),
    11: ("breath_duration_s", "provisional"),
    10: ("tidal_volume_l", "provisional"),
    12: ("vo2_ml_min", "provisional"),
    18: ("heart_rate_bpm", "provisional"),
    20: ("fio2_fraction", "provisional"),
    19: ("feo2_fraction", "provisional"),
    15: ("ventilation_l_min", "provisional"),
    17: ("fico2_fraction", "provisional"),
    16: ("feco2_fraction", "provisional"),
}

MANUAL_MEASUREMENT_CATALOG: Final = {
    3037: ("systolic_bp", "mmHg", MMHG_PER_KPA),
    3038: ("diastolic_bp", "mmHg", MMHG_PER_KPA),
    3068: ("heart_rate", "bpm", 1.0),
    3180: ("spo2", "%", 1.0),
}


class ErgoespirometryDecodeError(ValueError):
    """Indica que un binario no cumple la estructura Breeze esperada."""


@dataclass(frozen=True)
class RawHeader:
    """Campos estructurales confirmados de GXTestRawData."""

    version: int
    declared_size: int
    channel_count: int
    observation_count: int
    raw_bytes: bytes


@dataclass(frozen=True)
class SignalBlock:
    """Serie de un canal con su descriptor original y valores escalados."""

    channel_id: int
    scale: int
    name: str
    confidence: str
    descriptor: bytes
    raw_values: tuple[int, ...]
    values: tuple[float, ...]


@dataclass(frozen=True)
class RawData:
    """Contenido decodificado de GXTestRawData."""

    header: RawHeader
    auxiliary_channel_1: tuple[int, ...]
    auxiliary_channel_2: tuple[int, ...]
    signals: tuple[SignalBlock, ...]
    trailer: bytes


@dataclass(frozen=True)
class ManualMeasurement:
    """Medición introducida manualmente durante una prueba."""

    code: int
    raw_value: float
    name: str | None
    unit: str | None
    value: float


@dataclass(frozen=True)
class ManualEvent:
    """Grupo de mediciones manuales registrado en un instante."""

    timestamp: datetime
    measurements: tuple[ManualMeasurement, ...]


@dataclass(frozen=True)
class ManualData:
    """Contenido decodificado de ManuallyEnteredData."""

    reserved: int
    events: tuple[ManualEvent, ...]


def _as_bytes(blob: bytes | bytearray | memoryview) -> bytes:
    """Normaliza los tipos binarios entregados por pyodbc."""

    if not isinstance(blob, (bytes, bytearray, memoryview)):
        raise TypeError("El binario debe ser bytes, bytearray o memoryview.")
    return bytes(blob)


def expected_raw_size(observation_count: int) -> int:
    """Calcula la longitud de GXTestRawData para N observaciones."""

    return 326 + (44 * observation_count)


def decode_raw_data(blob: bytes | bytearray | memoryview) -> RawData:
    """Decodifica GXTestRawData versión 10 y valida toda su estructura."""

    data = _as_bytes(blob)
    if len(data) < RAW_HEADER_SIZE:
        raise ErgoespirometryDecodeError(
            f"GXTestRawData demasiado corto: {len(data)} bytes."
        )

    version, declared_size = struct.unpack_from("<II", data, 0)
    channel_count, observation_count = struct.unpack_from("<HH", data, 8)

    if version != RAW_VERSION:
        raise ErgoespirometryDecodeError(
            f"Versión GXTestRawData no soportada: {version}."
        )
    if channel_count != RAW_CHANNEL_COUNT:
        raise ErgoespirometryDecodeError(
            f"Número de canales inesperado: {channel_count}."
        )

    calculated_size = expected_raw_size(observation_count)
    if declared_size != len(data):
        raise ErgoespirometryDecodeError(
            "La longitud declarada no coincide con el binario: "
            f"{declared_size} != {len(data)}."
        )
    if calculated_size != len(data):
        raise ErgoespirometryDecodeError(
            "El binario no cumple 326 + 44*N: "
            f"{len(data)} != {calculated_size}."
        )

    header = RawHeader(
        version=version,
        declared_size=declared_size,
        channel_count=channel_count,
        observation_count=observation_count,
        raw_bytes=data[:RAW_HEADER_SIZE],
    )

    offset = RAW_HEADER_SIZE
    auxiliary_1: list[int] = []
    auxiliary_2: list[int] = []
    for first, second in struct.iter_unpack(
        "<HH", data[offset : offset + (4 * observation_count)]
    ):
        auxiliary_1.append(first)
        auxiliary_2.append(second)
    offset += 4 * observation_count

    signals: list[SignalBlock] = []
    for position in range(RAW_SIGNAL_COUNT):
        descriptor = data[offset : offset + RAW_SIGNAL_DESCRIPTOR_SIZE]
        if len(descriptor) != RAW_SIGNAL_DESCRIPTOR_SIZE:
            raise ErgoespirometryDecodeError(
                f"Descriptor incompleto en el bloque {position + 1}."
            )

        channel_id = descriptor[0]
        scale = struct.unpack_from("<H", descriptor, 2)[0]
        if scale == 0:
            raise ErgoespirometryDecodeError(
                f"Escala cero en el canal {channel_id}."
            )
        offset += RAW_SIGNAL_DESCRIPTOR_SIZE

        values_size = 4 * observation_count
        raw_values = tuple(
            value[0]
            for value in struct.iter_unpack(
                "<i", data[offset : offset + values_size]
            )
        )
        if len(raw_values) != observation_count:
            raise ErgoespirometryDecodeError(
                f"Canal {channel_id} incompleto."
            )
        offset += values_size

        name, confidence = SIGNAL_CATALOG.get(
            channel_id,
            (f"channel_{channel_id}", "unknown"),
        )
        signals.append(
            SignalBlock(
                channel_id=channel_id,
                scale=scale,
                name=name,
                confidence=confidence,
                descriptor=descriptor,
                raw_values=raw_values,
                values=tuple(value / scale for value in raw_values),
            )
        )

    trailer = data[offset:]
    if len(trailer) != RAW_TRAILER_SIZE:
        raise ErgoespirometryDecodeError(
            f"Bloque final inesperado: {len(trailer)} bytes."
        )

    return RawData(
        header=header,
        auxiliary_channel_1=tuple(auxiliary_1),
        auxiliary_channel_2=tuple(auxiliary_2),
        signals=tuple(signals),
        trailer=trailer,
    )


def raw_data_to_dataframe(decoded: RawData) -> pd.DataFrame:
    """Convierte las series decodificadas en una tabla por observación."""

    result: dict[str, object] = {
        "observation_index": range(decoded.header.observation_count),
        "auxiliary_channel_1": decoded.auxiliary_channel_1,
        "auxiliary_channel_2": decoded.auxiliary_channel_2,
    }
    used_names: set[str] = set(result)

    for signal in decoded.signals:
        column_name = signal.name
        if column_name in used_names:
            column_name = f"{column_name}_{signal.channel_id}"
        used_names.add(column_name)
        result[column_name] = signal.values

    return pd.DataFrame(result)


def _read_exact(data: bytes, offset: int, size: int, label: str) -> bytes:
    """Lee un tramo completo o produce un error estructural legible."""

    chunk = data[offset : offset + size]
    if len(chunk) != size:
        raise ErgoespirometryDecodeError(
            f"ManuallyEnteredData termina durante {label}."
        )
    return chunk


def decode_manual_data(blob: bytes | bytearray | memoryview) -> ManualData:
    """Decodifica los eventos de presión, pulso y SpO2 introducidos a mano."""

    data = _as_bytes(blob)
    _read_exact(data, 0, 6, "la cabecera")
    reserved, event_count = struct.unpack_from("<HI", data, 0)
    offset = 6
    events: list[ManualEvent] = []

    for event_index in range(event_count):
        event_header = _read_exact(
            data,
            offset,
            10,
            f"la cabecera del evento {event_index + 1}",
        )
        ole_date, measurement_count = struct.unpack("<dH", event_header)
        offset += 10
        measurements: list[ManualMeasurement] = []

        for measurement_index in range(measurement_count):
            encoded = _read_exact(
                data,
                offset,
                10,
                "la medición "
                f"{measurement_index + 1} del evento {event_index + 1}",
            )
            code, raw_value = struct.unpack("<Hd", encoded)
            offset += 10
            catalog_entry = MANUAL_MEASUREMENT_CATALOG.get(code)

            if catalog_entry is None:
                name = None
                unit = None
                factor = 1.0
            else:
                name, unit, factor = catalog_entry

            measurements.append(
                ManualMeasurement(
                    code=code,
                    raw_value=raw_value,
                    name=name,
                    unit=unit,
                    value=raw_value * factor,
                )
            )

        events.append(
            ManualEvent(
                timestamp=OLE_AUTOMATION_EPOCH + timedelta(days=ole_date),
                measurements=tuple(measurements),
            )
        )

    if offset != len(data):
        raise ErgoespirometryDecodeError(
            "ManuallyEnteredData contiene bytes no consumidos: "
            f"{len(data) - offset}."
        )

    return ManualData(reserved=reserved, events=tuple(events))


def manual_data_to_dataframe(decoded: ManualData) -> pd.DataFrame:
    """Convierte los eventos manuales en formato largo auditable."""

    rows = []
    for event_index, event in enumerate(decoded.events):
        for measurement in event.measurements:
            rows.append(
                {
                    "event_index": event_index,
                    "timestamp": event.timestamp,
                    "measurement_code": measurement.code,
                    "measurement_name": measurement.name,
                    "raw_value": measurement.raw_value,
                    "value": measurement.value,
                    "unit": measurement.unit,
                }
            )

    return pd.DataFrame(
        rows,
        columns=[
            "event_index",
            "timestamp",
            "measurement_code",
            "measurement_name",
            "raw_value",
            "value",
            "unit",
        ],
    )
