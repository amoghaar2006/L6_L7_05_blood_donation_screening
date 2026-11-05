import pytest

from blood_donation_screening import (
    process_donor_cohort,
    verify_storage_centrifuge,
)


def test_invalid_cohort_input():
    with pytest.raises(ValueError):
        process_donor_cohort("invalid", 450)


def test_invalid_standard_volume():
    with pytest.raises(ValueError):
        process_donor_cohort([], 0)


def test_unregistered_cohort():
    cohorts = [{"clinic_registered": False}]
    result = process_donor_cohort(cohorts, 450)
    assert result["status"] == "ZERO_YIELD"


def test_donor_rejected_due_to_age():
    cohorts = [{
        "clinic_registered": True,
        "donors": [{"age": 16, "weight_kg": 65, "hb": 14.0}],
    }]
    result = process_donor_cohort(cohorts, 450)
    assert result["status"] == "ZERO_YIELD"


def test_donor_rejected_due_to_weight():
    cohorts = [{
        "clinic_registered": True,
        "donors": [{"age": 25, "weight_kg": 45, "hb": 14.0}],
    }]
    result = process_donor_cohort(cohorts, 450)
    assert result["status"] == "ZERO_YIELD"


def test_low_hemoglobin_in_high_altitude_cohort():
    cohorts = [{
        "clinic_registered": True,
        "type": "high_altitude",
        "donors": [{"age": 25, "weight_kg": 65, "hb": 12.0}],
    }]
    result = process_donor_cohort(cohorts, 450)
    assert result["status"] == "ZERO_YIELD"


def test_high_hemoglobin_donor():
    cohorts = [{
        "clinic_registered": True,
        "donors": [{"age": 25, "weight_kg": 65, "hb": 19.0}],
    }]
    result = process_donor_cohort(cohorts, 450)
    assert result["status"] == "ZERO_YIELD"


def test_accepted_donor_and_fast_track():
    cohorts = [{
        "clinic_registered": True,
        "fast_track": True,
        "donors": [{"age": 25, "weight_kg": 65, "hb": 14.0}],
    }]
    result = process_donor_cohort(cohorts, 450)
    assert result == {"collected_ml": 500, "status": "ACCEPTED"}


def test_high_deferral_status():
    cohorts = [{
        "clinic_registered": True,
        "donors": [
            {"age": 16, "weight_kg": 65, "hb": 14.0}
            for _ in range(5)
        ],
    }]
    result = process_donor_cohort(cohorts, 450)
    assert result["status"] == "HIGH_DEFERRAL"


def test_empty_centrifuge_data():
    assert verify_storage_centrifuge([]) == "NO_DATA"


def test_centrifuge_aborts_after_two_low_readings():
    runs = [[3500, 2800, 2700]]
    assert verify_storage_centrifuge(runs) == "ABORT_SPIN"


def test_centrifuge_stable_after_speed_recovers():
    runs = [[2800, 3500, 2800]]
    assert verify_storage_centrifuge(runs) == "STABLE"