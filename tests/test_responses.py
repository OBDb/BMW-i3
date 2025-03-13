import glob
import os
import pytest
from pathlib import Path
from typing import Dict, Any

from schemas.python.can_frame import CANIDFormat
from schemas.python.json_formatter import format_file
from schemas.python.signals_testing import obd_testrunner_by_year

REPO_ROOT = Path(__file__).parent.parent.absolute()

TEST_CASES = [
    {
        "model_year": 2018,
        "tests": [
            # Charger state
            ("""
61AF1101C62DE0000B8
61AF121160000000000
61AF122000A2407D005
61AF12300000000000D
61AF1244B001A050EFF
""", {
    "I3_HVBAT_HVPM_SOC": 18.4,
    "I3_HVBAT_HVPM_MIN_SOC": 11,
    "I3_HVBAT_CHG_CON": 0,
    "I3_HVBAT_CHG_CON_EXT": 0,
    "I3_HVBAT_CHG_RDY": 0,
    }),
            ("""
61AF1101C62DE0000C5
61AF121160000010100
61AF1225E0A2B07D005
61AF123D2012A00120D
61AF1242E018F05D2FF
""", {
    "I3_HVBAT_HVPM_SOC": 19.7,
    "I3_HVBAT_HVPM_MIN_SOC": 11,
    "I3_HVBAT_CHG_CON": 0,
    "I3_HVBAT_CHG_CON_EXT": 0,
    "I3_HVBAT_CHG_RDY": 1,
    }),

            # State of health
            ("""
607F110076263350000
607F1210058FFFFFFFF
""", {"I3_HVBAT_SOH": 88}),
        ],
    },
    {
        "model_year": 2019,
        "tests": [
            # Range remaining
            ("""
660F1100B62420C00B8
660F121008B00B200C4
""", {
    "I3_RANGE": 178,
    "I3_RANGE_ECO": 184,
    "I3_RANGE_COMF": 139,
    }),

            # Odometer
            ("""
660F1100B62D10D0002
660F1218A1200028A12
""", {
    "I3_ODO1": 166418.0,
    "I3_ODO2": 166418.0,
    }),

            # Speed
            ("660F10562D1070000", {"I3_VSS": 0}),
            ("660F10562D1070123", {"I3_VSS": 29.1}),

            # State of charge
            ("""
607F1100962DDBC0372
607F121036D006EFFFF
""", {
    "I3_HVBAT_SOC": 88.2,
    "I3_HVBAT_SOC_MAX": 87.7,
    "I3_HVBAT_SOC_MIN": 11,
    }),

            # State of health
            ("""
607F110076263350000
607F1210059FFFFFFFF
""", {"I3_HVBAT_SOH": 89}),
        ]
    },
]

@pytest.mark.parametrize(
    "test_group",
    TEST_CASES,
    ids=lambda test_case: f"MY{test_case['model_year']}"
)
def test_signals(test_group: Dict[str, Any]):
    """Test signal decoding against known responses."""
    # Run each test case in the group
    for response_hex, expected_values in test_group["tests"]:
        try:
            obd_testrunner_by_year(
                test_group['model_year'],
                response_hex,
                expected_values,
                can_id_format=CANIDFormat.ELEVEN_BIT,
                extended_addressing_enabled=True
            )
        except Exception as e:
            pytest.fail(
                f"Failed on response {response_hex} "
                f"(Model Year: {test_group['model_year']}: {e}"
            )

def get_json_files():
    """Get all JSON files from the signalsets/v3 directory."""
    signalsets_path = os.path.join(REPO_ROOT, 'signalsets', 'v3')
    json_files = glob.glob(os.path.join(signalsets_path, '*.json'))
    # Convert full paths to relative filenames
    return [os.path.basename(f) for f in json_files]

@pytest.mark.parametrize("test_file",
    get_json_files(),
    ids=lambda x: x.split('.')[0].replace('-', '_')  # Create readable test IDs
)
def test_formatting(test_file):
    """Test signal set formatting for all vehicle models in signalsets/v3/."""
    signalset_path = os.path.join(REPO_ROOT, 'signalsets', 'v3', test_file)

    formatted = format_file(signalset_path)

    with open(signalset_path) as f:
        assert f.read() == formatted

if __name__ == '__main__':
    pytest.main([__file__])
