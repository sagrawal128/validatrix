from typing import Union, List, Any, Dict

from validatrix.base import Rule, ValidationResult


class HasColumns(Rule):
    """Check whether a dataframe contains specified columns."""

    def __init__(
        self,
        columns: Union[str, List[str]],
        allow_subset: bool = True,
        raise_exc: bool = True,
        inputs: Union[bool, str, List[str]] = False,
        outputs: Union[bool, str, List[str]] = None,
    ):
        """
        Checks whether a dataframe contains the specified columns.

        Args:
            columns: One or more columns to check for
            allow_subset: Flag to check if specified columns are all or part.
        """
        super().__init__(raise_exc=raise_exc, inputs=inputs, outputs=outputs)
        self.columns = columns
        self.allow_subset = allow_subset

    def _validate(self, data: Any) -> Union[bool, str, ValidationResult]:
        return self._has_columns(list(data.columns))

    def _has_columns(self, data_cols: List[str]):
        bad = (
            set(self.columns) - set(data_cols)
            if self.allow_subset
            else set(self.columns) != set(data_cols)
        )
        result = ValidationResult()

        if not bad:
            return result

        if self.allow_subset:
            result.error(f"Missing cols: {str(bad)}")
        else:
            only_in_df = set(data_cols) - set(self.columns)
            only_in_val = set(self.columns) - set(data_cols)
            if only_in_df:
                result.error(f"Unexpected columns: {only_in_df}")
            if only_in_val:
                result.error(f"Missing columns: {only_in_val}")
        return result


class HasSchema(Rule):
    """Checks the schema: column and type of the dataframe."""

    def __init__(
        self,
        schema: Dict[str, str],
        allow_subset: bool = True,
        raise_exc: bool = True,
        inputs: Union[bool, str, List[str]] = False,
        outputs: Union[bool, str, List[str]] = None,
    ):
        """
        Checks if the dataframe conforms to particular schema.
        Args:
            schema: Schema to verify against.
            allow_subset: Allow if part of the information is correct.
        """
        super().__init__(raise_exc=raise_exc, inputs=inputs, outputs=outputs)
        self.schema = schema
        self.allow_subset = allow_subset

    def _validate(self, data: Any) -> Union[bool, str, ValidationResult]:
        result = self._has_columns(list(data.columns))

        for col, expected_type in self.schema.items():
            if col in data.columns:
                actual = str(data[col].dtype)
                if expected_type != actual:
                    result.error(
                        f"Column `{col}` contains `{actual}` instead of `"
                        f"{expected_type}`."
                    )
        return result

    def _has_columns(self, data_cols: List[str]):
        observed_cols = list(self.schema.keys())
        bad = (
            set(observed_cols) - set(data_cols)
            if self.allow_subset
            else set(observed_cols) != set(data_cols)
        )
        result = ValidationResult()

        if not bad:
            return result

        if self.allow_subset:
            result.error(f"Missing cols: {str(bad)}")
        else:
            only_in_df = set(data_cols) - set(observed_cols)
            only_in_val = set(observed_cols) - set(data_cols)
            if only_in_df:
                result.error(f"Unexpected columns: {only_in_df}")
            if only_in_val:
                result.error(f"Missing columns: {only_in_val}")
        return result
