import pytest

import pandas as pd
from validatrix import HasColumns, HasSchema


@pytest.fixture
def dataframe():
    return pd.DataFrame(
        {
            "id": [100, None, 300, 400],
            "name": ["Alice", "Bob", "Car0l", "Denise"],
            "curr_emp": [True, False, True, False]
        }
    )


def test_has_columns(dataframe):
    rule = HasColumns(["id", "name", "curr_emp"], allow_subset=False)
    assert rule.validate(dataframe)


def test_has_not_columns(dataframe):
    rule = HasColumns(["id", "name"], allow_subset=False, raise_exc=False)
    assert not rule.validate(dataframe)


def test_has_schema_ok(dataframe):
    rule = HasSchema({"id": "float64", "name": "object", "curr_emp": "bool"})
    assert rule.validate(dataframe)


def test_schema_is_wrong(dataframe):
    rule = HasSchema({"id": "int64", "name": "object", "curr_emp": "bool"},
                     raise_exc=False)
    result = rule.validate(dataframe)
    assert not result
    assert "id" in str(result)
