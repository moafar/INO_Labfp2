# tests/unit/test_transform_ergoespirometry.py
"""Pruebas sintéticas del decodificador de ergoespirometría."""

from datetime import datetime
import math
import struct

import pytest

from src.transform.ergoespirometry import (
    ErgoespirometryDecodeError,
    MMHG_PER_KPA,
    RAW_CHANNEL_LAYOUT,
    RAW_HEADER_SIZE,
    decode_manual_data,
    decode_optional_raw_data,
    decode_raw_data,
    expected_raw_size,
    haldane_gas_exchange_ml_min,
    manual_data_to_dataframe,
    minute_ventilation_atps_l_min,
    oxygen_pulse_ml_beat,
    raw_data_to_dataframe,
    respiratory_exchange_ratio,
    respiratory_rate_br_min,
    tidal_volume_atps_l,
    ventilatory_equivalent,
)


def build_raw_blob(observation_count: int = 3) -> bytes:
    """Construye un GXTestRawData versión 10 sin datos clínicos."""

    size = expected_raw_size(observation_count)
    header = bytearray(RAW_HEADER_SIZE)
    struct.pack_into("<IIHH", header, 0, 10, size, 12, observation_count)

    blocks = []

    for block_index, definition in enumerate(RAW_CHANNEL_LAYOUT):
        channel_id, scale, storage_type = definition
        descriptor = struct.pack(
            "<BBHBB",
            channel_id,
            0xA0 + block_index,
            scale,
            storage_type,
            0xB0 + block_index,
        )
        value_format = "<H" if storage_type == 0 else "<i"
        base_value = (block_index + 1) * scale
        values = b"".join(
            struct.pack(value_format, base_value + index * scale)
            for index in range(observation_count)
        )
        blocks.append(descriptor + values)

    return bytes(header) + b"".join(blocks) + bytes(230)


def build_manual_blob() -> bytes:
    """Construye dos eventos manuales sin identificadores personales."""

    first_ole_date = (datetime(2025, 1, 2, 12) - datetime(1899, 12, 30)).total_seconds() / 86400
    second_ole_date = (datetime(2025, 1, 2, 12, 5) - datetime(1899, 12, 30)).total_seconds() / 86400

    return b"".join(
        [
            struct.pack("<HI", 0, 2),
            struct.pack("<dH", first_ole_date, 2),
            struct.pack("<Hd", 3037, 16.0),
            struct.pack("<Hd", 3068, 90.0),
            struct.pack("<dH", second_ole_date, 1),
            struct.pack("<Hd", 3180, 97.0),
        ]
    )


def test_decode_raw_data_reads_all_twelve_channels() -> None:
    """Verifica cabecera y los doce bloques columnares escalados."""

    decoded = decode_raw_data(build_raw_blob())

    assert len(decoded.header.raw_bytes) == 24
    assert decoded.header.observation_count == 3
    assert decoded.auxiliary_channel_1 == (10, 20, 30)
    assert decoded.auxiliary_channel_2 == (20, 30, 40)
    assert [signal.channel_id for signal in decoded.signals] == [
        24, 25, 1, 11, 10, 12, 18, 20, 19, 15, 17, 16
    ]
    assert [signal.storage_type for signal in decoded.signals] == [
        0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1
    ]
    assert [signal.scale for signal in decoded.signals] == [
        10, 10, 1000, 1000, 1000, 1000,
        1000, 10000, 10000, 1000, 10000, 10000,
    ]
    assert [signal.name for signal in decoded.signals] == [
        "work_watts",
        "speed_rpm",
        "elapsed_time_s",
        "breath_duration_s",
        "inspiratory_time_s",
        "tidal_volume_atps_ml",
        "gross_expired_o2_volume_ml_per_breath",
        "fio2_fraction",
        "feto2_fraction",
        "gross_expired_co2_volume_ml_per_breath",
        "fico2_fraction",
        "fetco2_fraction",
    ]
    assert [signal.unit for signal in decoded.signals] == [
        "W",
        "rpm",
        "s",
        "s/breath",
        "s",
        "mL/breath",
        "mL O2/breath",
        "fraction",
        "fraction",
        "mL CO2/breath",
        "fraction",
        "fraction",
    ]
    assert [signal.values[0] for signal in decoded.signals] == [
        float(index) for index in range(1, 13)
    ]
    assert decoded.signals[0].values == (1.0, 2.0, 3.0)
    assert decoded.signals[0].name == "work_watts"
    assert decoded.signals[0].unit == "W"
    assert decoded.signals[1].name == "speed_rpm"
    assert decoded.signals[1].unit == "rpm"
    assert decoded.signals[4].name == "inspiratory_time_s"
    assert decoded.signals[6].name == (
        "gross_expired_o2_volume_ml_per_breath"
    )
    assert decoded.signals[8].name == "feto2_fraction"
    assert decoded.signals[9].name == (
        "gross_expired_co2_volume_ml_per_breath"
    )
    assert decoded.signals[11].name == "fetco2_fraction"
    assert all(signal.confidence != "unknown" for signal in decoded.signals)
    assert decoded.signals[0].descriptor == bytes.fromhex("18a00a0000b0")
    assert decoded.signals[11].descriptor == bytes.fromhex("10ab102701bb")
    assert len(decoded.trailer) == 230


@pytest.mark.parametrize("observation_count", [0, 1, 3, 815])
def test_expected_raw_size_uses_two_uint16_and_ten_int32_blocks(
    observation_count: int,
) -> None:
    """La anchura física por observación es 2 + 2 + 10*4 = 44 bytes."""

    fixed_size = RAW_HEADER_SIZE + 12 * 6 + 230

    assert fixed_size == 326
    assert expected_raw_size(observation_count) == (
        fixed_size + 44 * observation_count
    )


def test_raw_data_to_dataframe_preserves_observation_count() -> None:
    """Verifica la tabla longitudinal producida por el decodificador."""

    dataframe = raw_data_to_dataframe(decode_raw_data(build_raw_blob(4)))

    assert len(dataframe) == 4
    assert dataframe.loc[0, "elapsed_time_s"] == 3.0
    assert "tidal_volume_atps_ml" in dataframe.columns
    assert "auxiliary_channel_1" in dataframe.columns
    assert dataframe["work_watts"].tolist() == [1.0, 2.0, 3.0, 4.0]
    assert dataframe["speed_rpm"].tolist() == [2.0, 3.0, 4.0, 5.0]


def test_raw_data_to_dataframe_preserves_real_rpm_zero() -> None:
    """Un cero registrado de RPM sigue siendo cero y no se convierte a nulo."""

    blob = bytearray(build_raw_blob())
    first_values_offset = RAW_HEADER_SIZE + 6
    second_descriptor_offset = first_values_offset + 2 * 3
    speed_values_offset = second_descriptor_offset + 6
    struct.pack_into("<H", blob, speed_values_offset, 0)

    dataframe = raw_data_to_dataframe(decode_raw_data(blob))

    assert dataframe.loc[0, "speed_rpm"] == 0.0
    assert not dataframe["speed_rpm"].isna().any()


def test_decode_optional_raw_data_distinguishes_absent_binary() -> None:
    """La ausencia de GXTestRawData no se confunde con un fallo estructural."""

    assert decode_optional_raw_data(None) is None
    assert decode_optional_raw_data(build_raw_blob()) is not None


def test_decode_raw_data_rejects_inconsistent_length() -> None:
    """Evita interpretar silenciosamente un binario truncado."""

    with pytest.raises(ErgoespirometryDecodeError, match="longitud declarada"):
        decode_raw_data(build_raw_blob()[:-1])


def test_decode_raw_data_rejects_inconsistent_observation_count() -> None:
    """Rechaza un N de cabecera incompatible con los bloques físicos."""

    blob = bytearray(build_raw_blob(3))
    struct.pack_into("<H", blob, 10, 4)

    with pytest.raises(ErgoespirometryDecodeError, match=r"326 \+ 44\*N"):
        decode_raw_data(blob)


@pytest.mark.parametrize(
    ("descriptor_offset", "field_offset", "replacement", "message"),
    [
        (24, 0, 25, "Orden de canales"),
        (24, 2, 11, "Escala inesperada"),
        (24, 4, 1, "Tipo físico inesperado"),
    ],
)
def test_decode_raw_data_rejects_descriptor_inconsistencies(
    descriptor_offset: int,
    field_offset: int,
    replacement: int,
    message: str,
) -> None:
    """El orden, la escala y el ancho forman parte del contrato físico."""

    blob = bytearray(build_raw_blob())
    if field_offset == 2:
        struct.pack_into("<H", blob, descriptor_offset + field_offset, replacement)
    else:
        blob[descriptor_offset + field_offset] = replacement

    with pytest.raises(ErgoespirometryDecodeError, match=message):
        decode_raw_data(blob)


def test_decode_manual_data_converts_known_measurements() -> None:
    """Verifica fecha OLE, presión en kPa, pulso y SpO2."""

    decoded = decode_manual_data(build_manual_blob())

    assert len(decoded.events) == 2
    assert decoded.events[0].timestamp == datetime(2025, 1, 2, 12)
    assert decoded.events[0].measurements[0].name == "systolic_bp"
    assert decoded.events[0].measurements[0].value == pytest.approx(
        16.0 * MMHG_PER_KPA
    )
    assert decoded.events[0].measurements[1].value == 90.0


def test_manual_data_to_dataframe_keeps_unknown_codes() -> None:
    """Conserva códigos desconocidos para investigación posterior."""

    ole_date = (datetime(2025, 1, 1) - datetime(1899, 12, 30)).days
    blob = struct.pack("<HIdHHd", 0, 1, ole_date, 1, 9999, 3.5)

    dataframe = manual_data_to_dataframe(decode_manual_data(blob))

    assert dataframe.loc[0, "measurement_code"] == 9999
    assert dataframe.loc[0, "measurement_name"] is None
    assert dataframe.loc[0, "value"] == 3.5


def test_ventilatory_derivations_preserve_units() -> None:
    """Comprueba VT, RR y VE con un caso dimensionalmente trazable."""

    assert tidal_volume_atps_l(750.0) == pytest.approx(0.75)
    assert respiratory_rate_br_min(3.0) == pytest.approx(20.0)
    assert minute_ventilation_atps_l_min(750.0, 3.0) == pytest.approx(
        15.0
    )


@pytest.mark.parametrize(
    ("tidal_volume_ml", "duration_s"),
    [
        (0.0, 2.0),
        (-1.0, 2.0),
        (500.0, 0.0),
        (500.0, -1.0),
        (None, 2.0),
        (500.0, None),
        (math.nan, 2.0),
        (500.0, math.nan),
        (math.inf, 2.0),
        (-math.inf, 2.0),
        (500.0, math.inf),
        (500.0, -math.inf),
    ],
)
def test_ventilatory_derivations_reject_missing_or_nonphysical_values(
    tidal_volume_ml: float | None,
    duration_s: float | None,
) -> None:
    """Evita infinitos y resultados silenciosos ante entradas no físicas."""

    assert math.isnan(
        minute_ventilation_atps_l_min(tidal_volume_ml, duration_s)
    )


def test_haldane_gas_exchange_uses_explicit_fractions_and_units() -> None:
    """Contrasta signos y factor L->mL con un caso construido."""

    vo2_ml_min, vco2_ml_min = haldane_gas_exchange_ml_min(
        expired_ventilation_l_min=30.0,
        fio2_fraction=0.21,
        feo2_fraction=0.17,
        fico2_fraction=0.0,
        feco2_fraction=0.04,
    )

    inspired_ventilation_l_min = 30.0 * 0.79 / 0.79
    assert vo2_ml_min == pytest.approx(
        (inspired_ventilation_l_min * 0.21 - 30.0 * 0.17) * 1000.0
    )
    assert vco2_ml_min == pytest.approx(30.0 * 0.04 * 1000.0)


@pytest.mark.parametrize(
    "arguments",
    [
        (0.0, 0.21, 0.17, 0.0, 0.04),
        (30.0, math.nan, 0.17, 0.0, 0.04),
        (30.0, 0.8, 0.3, 0.3, 0.04),
        (30.0, 0.21, 0.17, 0.0, -0.04),
    ],
)
def test_haldane_gas_exchange_rejects_invalid_inputs(
    arguments: tuple[float, float, float, float, float],
) -> None:
    """No produce intercambios finitos con fracciones o flujos no físicos."""

    vo2_ml_min, vco2_ml_min = haldane_gas_exchange_ml_min(*arguments)
    assert math.isnan(vo2_ml_min)
    assert math.isnan(vco2_ml_min)


def test_ratios_use_consistent_units_and_safe_denominators() -> None:
    """Comprueba RER y equivalentes ventilatorios derivados."""

    assert respiratory_exchange_ratio(1000.0, 900.0) == pytest.approx(0.9)
    assert ventilatory_equivalent(30.0, 1000.0) == pytest.approx(30.0)
    assert oxygen_pulse_ml_beat(1200.0, 120.0) == pytest.approx(10.0)
    assert math.isnan(respiratory_exchange_ratio(0.0, 900.0))
    assert math.isnan(ventilatory_equivalent(30.0, 0.0))
    assert math.isnan(oxygen_pulse_ml_beat(1200.0, 0.0))
