import pytest

from blood_donation_screening import (
    process_donor_cohort,
    verify_storage_centrifuge,
)


def test_invalid_cohort_type():
    with pytest.raises(ValueError):
        process_donor_cohort("invalid", 450)


def test_invalid_volume():
    with pytest.raises(ValueError):
        process_donor_cohort([], 0)


def test_valid_empty_cohort_list():
    result = process_donor_cohort([], 450)
    assert result["status"] == "ZERO_YIELD"


def test_unregistered_cohort():
    cohorts = [{"clinic_registered": False}]
    result = process_donor_cohort(cohorts, 450)
    assert result["status"] == "ZERO_YIELD"


def test_registered_cohort_without_donors():
    cohorts = [{"clinic_registered": True}]
    result = process_donor_cohort(cohorts, 450)
    assert result["status"] == "ZERO_YIELD"


def test_donor_below_minimum_age():
    cohorts = [{
        "clinic_registered": True,
        "donors": [{"age": 16, "weight_kg": 65, "hb": 14.0}],
    }]
    result = process_donor_cohort(cohorts, 450)
    assert result["status"] == "ZERO_YIELD"


def test_donor_below_minimum_weight():
    cohorts = [{
        "clinic_registered": True,
        "donors": [{"age": 25, "weight_kg": 49, "hb": 14.0}],
    }]
    result = process_donor_cohort(cohorts, 450)
    assert result["status"] == "ZERO_YIELD"


def test_donor_with_low_hemoglobin_standard_cohort():
    cohorts = [{
        "clinic_registered": True,
        "type": "standard",
        "donors": [
            {"age": 25, "weight_kg": 65, "hb": 12.0},
            {"age": 26, "weight_kg": 70, "hb": 14.0},
        ],
    }]
    result = process_donor_cohort(cohorts, 450)
    assert result == {"collected_ml": 450, "status": "ACCEPTED"}


def test_low_hemoglobin_high_altitude_cohort():
    cohorts = [{
        "clinic_registered": True,
        "type": "high_altitude",
        "donors": [
            {"age": 25, "weight_kg": 65, "hb": 12.0},
            {"age": 26, "weight_kg": 70, "hb": 14.0},
        ],
    }]
    result = process_donor_cohort(cohorts, 450)
    assert result["collected_ml"] == 0
    assert result["status"] == "ZERO_YIELD"


def test_high_hemoglobin_donor():
    cohorts = [{
        "clinic_registered": True,
        "donors": [{"age": 25, "weight_kg": 65, "hb": 19.0}],
    }]
    result = process_donor_cohort(cohorts, 450)
    assert result["status"] == "ZERO_YIELD"


def test_accepted_donor_with_fast_track():
    cohorts = [{
        "clinic_registered": True,
        "fast_track": True,
        "donors": [{"age": 25, "weight_kg": 65, "hb": 14.0}],
    }]
    result = process_donor_cohort(cohorts, 450)
    assert result == {"collected_ml": 500, "status": "ACCEPTED"}


def test_high_deferral_with_zero_yield():
    cohorts = [{
        "clinic_registered": True,
        "donors": [
            {"age": 16, "weight_kg": 65, "hb": 14.0}
            for _ in range(5)
        ],
    }]
    result = process_donor_cohort(cohorts, 450)
    assert result["status"] == "HIGH_DEFERRAL"


def test_high_deferral_with_positive_yield():
    cohorts = [{
        "clinic_registered": True,
        "donors": [
            {"age": 16, "weight_kg": 65, "hb": 14.0}
            for _ in range(5)
        ] + [
            {"age": 25, "weight_kg": 65, "hb": 14.0}
        ],
    }]
    result = process_donor_cohort(cohorts, 450)
    assert result == {"collected_ml": 450, "status": "HIGH_DEFERRAL"}


def test_no_centrifuge_data():
    assert verify_storage_centrifuge([]) == "NO_DATA"


def test_centrifuge_aborts_after_two_consecutive_low_readings():
    assert verify_storage_centrifuge([[3500, 2800, 2700]]) == "ABORT_SPIN"


def test_centrifuge_recovers_after_low_reading():
    assert verify_storage_centrifuge([[2800, 3500]]) == "STABLE"


def test_centrifuge_aborts_after_recovery_and_two_low_readings():
    assert verify_storage_centrifuge([[2800, 3500, 2800, 2700]]) == "ABORT_SPIN"


def test_centrifuge_multiple_stable_runs():
    assert verify_storage_centrifuge([[3500, 3600], [3400, 3500]]) == "STABLE"