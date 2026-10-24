"""Request-schema validation tests."""

import pytest
from pydantic import ValidationError

from src.models.schemas import (
    MAX_MEDICATIONS,
    DrugInteractionRequest,
    UserInput,
)


def _valid_input(**overrides):
    payload = {
        "meds": ["Adol 500"],
        "schedule": ["1+0+1"],
        "age": 35,
        "gender": "M",
    }
    payload.update(overrides)
    return payload


def test_user_input_accepts_valid_payload():
    user_input = UserInput(**_valid_input())
    assert user_input.meds == ["Adol 500"]


def test_user_input_rejects_too_many_medications():
    payload = _valid_input(
        meds=[f"drug {i}" for i in range(MAX_MEDICATIONS + 1)],
        schedule=["1+0+1"] * (MAX_MEDICATIONS + 1),
    )
    with pytest.raises(ValidationError):
        UserInput(**payload)


def test_user_input_rejects_blank_medication_name():
    with pytest.raises(ValidationError):
        UserInput(**_valid_input(meds=["   "]))


def test_user_input_rejects_oversized_medication_name():
    with pytest.raises(ValidationError):
        UserInput(**_valid_input(meds=["x" * 101]))


def test_user_input_strips_whitespace():
    user_input = UserInput(**_valid_input(meds=["  Adol 500  "]))
    assert user_input.meds == ["Adol 500"]


def test_user_input_rejects_out_of_range_age():
    with pytest.raises(ValidationError):
        UserInput(**_valid_input(age=0))


def test_drug_interaction_request_requires_two_medications():
    with pytest.raises(ValidationError):
        DrugInteractionRequest(medications=["aspirin"])


def test_drug_interaction_request_accepts_patient_info():
    request = DrugInteractionRequest(
        medications=["aspirin", "warfarin"],
        patient_info={"age": 70, "gender": "F", "medical_conditions": ["renal"]},
    )
    assert request.patient_info.age == 70
