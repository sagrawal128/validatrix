import inspect
import logging
from abc import ABC, abstractmethod
from functools import wraps
from typing import Union, List, Any, Callable, Dict, Tuple
from warnings import warn


class ValidationResult:
    """Base class for validation result."""

    pass


class ValidationError(Exception):
    """Base class for validation errors."""

    def __init__(
        self, message: str = None, validation_result: "ValidationResult" = None
    ):
        super().__init__(message or "")
        self._validation_result = validation_result

    def __str__(self):
        msg = super().__str__()
        if self._validation_result is not None:
            msg += "\n" + str(self._validation_result)
        return msg


def _normalise_func_inputs(
    args: Tuple,
    kwargs: Dict[str, Any],
    inputs: Union[bool, str, List[str]],
    func: Callable,
) -> Dict[str, Any]:
    bound_args = inspect.signature(func).bind(*args, **kwargs)
    bound_args.apply_defaults()
    arguments = bound_args.arguments
    if bound_args.kwargs:
        _kwargs = arguments.pop(list(arguments.keys())[-1])
        arguments = {**arguments, **_kwargs}

    if inputs is True:
        return arguments

    if not set(inputs).issubset(set(arguments.keys())):
        raise ValueError(
            f"Failed to validate inputs `{inputs}` of function `"
            f"{func.__name__}`. They "
            f"are not subset of argument names `{list(arguments.keys())}`"
        )

    return {key: value for key, value in arguments.items() if key in inputs}


def _normalise_func_outputs(result, outputs, func: Callable) -> Dict[str, Any]:
    func_name = "`" + func.__name__ + "`"

    if outputs is True:
        return {"": result}

    if not isinstance(result, dict):
        raise ValueError(
            f"Failed to validate `outputs` {outputs} of function "
            f"{func_name}. When validating output, function should "
            f"return a dictionary and not {type(result).__name__}"
        )

    if not set(outputs).issubset(set(result.keys())):
        raise ValueError(
            f"Failed to validate outputs {list(outputs)} of function "
            f"{func_name} as they are not subset of the returned keys "
            f"{list(result.keys())}"
        )

    return {key: value for key, value in result.items() if key in outputs}


class Rule(ABC):
    """Base Class for all Rules."""

    def __init__(
        self,
        raise_exc: bool,
        inputs: Union[bool, str, List[str]],
        outputs: Union[bool, str, List[str]],
    ):
        self._raise_exc = raise_exc
        self._enable_logging = True
        outputs = inputs is False if outputs is None else outputs

        if not inputs and not outputs:
            raise ValueError("Specify atleast one value to run validation on.")
        self._inputs = [inputs] if isinstance(inputs, str) else inputs
        self._outputs = [outputs] if isinstance(outputs, str) else outputs

    @property
    def _logger(self):
        return logging.getLogger(__name__)

    def validate(self, data: Any, silent: bool = False) -> ValidationResult:
        """Validates data against the logic specified in ``_validate()``.

        If validation fails, it is recommended to populate result in the
        ``ValidationResult``.

        Args:
            data: Data to validate.
            silent: Flag to raise exceptions or express logging warnings.

        Returns:
            ValidationResult object with True/False outcome along with examples if
            validation failed.
        """
        result = self._validate(data)
        if result is False:
            warn(
                "A ValidationResult with useful information must be returned on "
                "failure instead and not just ``False``."
            )
            result = f"Validation failed. {self._name} provides no failure details."
        if result is True:
            result = ValidationResult(str(self))
        elif isinstance(result, str):
            result = ValidationResult(str(self)).error(result)
        elif not isinstance(result, ValidationResult):
            raise RuntimeError(
                f"Validation function {str(self)} should return "
                f"either a error message, ValidationResult or bool "
                f"value. Got {type(result).__name__} instead."
            )
        else:
            result.message = str(self)
        if not silent and self._raise_exc and not result:
            raise ValidationError(validation_result=result)

        if not silent and self._enable_logging and not result:
            self._logger.warning(result)

        return result

    @abstractmethod
    def _validate(self, data: Any) -> Union[bool, str, ValidationResult]:
        """
        Implement the logic for validating the data.

        Args:
            data: Data to be validated.

        Returns:
            Validation outcome.
        """
        raise NotImplemented

    @property
    def _name(self) -> str:
        return self.__class__.__name__

    def __call__(self, func: Callable) -> Callable:
        """
        Allows this class to be used as a decorator.

        Args:
            func: wrapped function.

        Returns:
            wrapped function
        """

        @wraps(func)
        def __wrapper(*args, **kwargs):
            return self._validate_and_call(func, *args, **kwargs)

        return __wrapper

    def _validate_and_call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Validates the inputs and outputs of the specified ``func``.

        Args:
            func: the function whose properties need to be validated.
            *args: args for the ``func``
            **kwargs: kwargs for the ``func``

        Returns:
            result returned when calling ``func``.
        """
        func_name = func.__name__

        if self._inputs:
            inputs = _normalise_func_inputs(args, kwargs, self._inputs, func)
            self._validate_data(inputs, func_name, "Input")
        result = func(*args, **kwargs)

        if self._outputs:
            outputs = _normalise_func_outputs(result, self._outputs, func)
            self._validate_data(outputs, func_name, "Output")

        return result

    def _validate_data(self, data: Dict[str, Any], func_name, message):
        for key, value in data.items():
            validation_res = self.validate(value, silent=True)
            if validation_res:
                continue

            if key:
                msg = (
                    f"{message} `{key}` of function `{func_name}` failed to "
                    f"validate."
                )
            else:
                msg = f"{message} of function `{func_name}` failed to validate."

            if self._raise_exc:
                raise ValidationError(msg, validation_res)

            if self._enable_logging:
                msg += "\n" + str(validation_res)
                self._logger.warning(msg)
