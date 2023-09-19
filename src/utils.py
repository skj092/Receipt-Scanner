from datetime import datetime
from loguru import logger
import functools
import time
import inspect
import re

SLOW_LOG_SYNC_SEC = 3

def async_timed_app():
    """
    The `async_timed` function is a decorator that measures the execution time of an asynchronous
    function and logs it along with the function name and request ID.
    :return: The function `async_timed` returns a decorator function `wrapper`.
    """
    def wrapper(func):
        @functools.wraps(func)
        async def wrapped(*args, **kwargs):
            request = kwargs["req"]
            logger.debug(f"args >>>>>>>> {kwargs}")
            if request:
                request_id = request.state.request_id
            else:
                request_id = None

            start = time.monotonic()
            try:
                return await func(*args, **kwargs)
            finally:
                end = time.monotonic()
                total = end - start
                if total > SLOW_LOG_SYNC_SEC:
                    logger.info(f"FUNCTION_NAME: {func.__name__} | EXEC_TIME: {total:.4f} seconds | REQUEST_ID: {request_id}")
                else:
                    logger.info(f"FUNCTION_NAME: {func.__name__} | EXEC_TIME: {total:.4f} seconds | REQUEST_ID: {request_id}")

        return wrapped

    return wrapper

def timed_methods(cls):
    """
    The `timed_methods` function is a decorator that adds timing functionality to all methods of a
    class.

    :param cls: The parameter `cls` is a class object
    :return: The `timed_methods` function returns the modified class with the timed methods.
    """
    for name, method in cls.__dict__.items():
        if callable(method):
            if inspect.iscoroutinefunction(method):
                setattr(cls, name, async_timed(method))
            else:
                setattr(cls, name, timed(method))
    return cls

def timed(func):
    """
    The `timed` decorator is used to measure the execution time of a function and log the result.

    :param func: The `func` parameter is a function that will be timed
    :return: The function being returned is a wrapped version of the original function.
    """
    @functools.wraps(func)
    def wrapped(self,*args, **kwargs):
        start_time = time.monotonic()
        try:
            return func(self,*args, **kwargs)
        finally:
            end_time = time.monotonic()
            total_time = end_time - start_time
            request_id = getattr(self, 'request_id', None)
            logger.info(f"REQUEST_ID : {request_id} | FUNCTION_NAME : {func.__name__} | EXEC_TIME {total_time} seconds |")
    return wrapped

def async_timed(func):
    """
    The `async_timed` decorator is used to measure the execution time of an asynchronous function and
    log the result.

    :param func: The `func` parameter is the function that will be wrapped with the `async_timed`
    decorator
    :return: The function `wrapped` is being returned.
    """
    @functools.wraps(func)
    async def wrapped(self,*args, **kwargs):
        start_time = time.monotonic()
        try:
            return await func(self,*args, **kwargs)
        finally:
            end_time = time.monotonic()
            total_time = end_time - start_time
            request_id = getattr(self, 'request_id', None)
            logger.info(f" REQUEST_ID : {request_id} | FUNCTION_NAME : {func.__name__} | EXEC_TIME {total_time} seconds | REQUEST_ID : {request_id}")
    return wrapped

def validate_pan(pan_num):
    pan_pattern = r'^[A-Z]{5}[0-9]{4}[A-Z]$'

    # Using re.match to check if the PAN matches the pattern
    if re.match(pan_pattern, pan_num):
        return pan_num
    else:
        return ""


def validate_uan(uan_num):
    out = uan_num if len(uan_num) == 12 else ""
    return out

def validate_result(result_json):
    pan = result_json['additionalData']['pan']
    uan = result_json['additionalData']['uan']
    result_json['additionalData']['pan'] = validate_pan(pan)
    result_json['additionalData']['uan']  = validate_uan(uan)
    return result_json

def mask_card_number(card_number):
    try:
        card_number = ''.join(filter(str.isdigit, card_number))
        masked_number = '*' * (len(card_number) - 4) + card_number[-4:]
        return masked_number
    except:
        return ""

def convert_employee_data(input_data):
    # Initialize the output_data using the desired format
    output_data = {
        "employeeName": "",
        "employeeId": "",
        "designation": "",
        "employerName": "",
        "employerAddress": "",
        "workLocation": "",
        "dateOfJoining": "",
        "salaryCreditMonth": "",
        "netSalary": "",
        "grossSalary": "",
        "deductions": "",
        "additionalData": {
            "pan": "",
            "uan": "",
            "modeOfPayment": "",
            "basicSalary": "",
            "hra": ""
        }
    }
    # Update fields from input_data
    for key, value in input_data.items():
        if key in output_data:
            if key == "salaryCreditMonth":
                try:
                    # Try to parse as abbreviated month name, if fails, try full month name
                    date_obj = datetime.strptime(value, '%b %Y')
                    output_data[key] = date_obj.strftime('%m')
                except ValueError:
                    output_data[key] = ""
            elif key == "dateOfJoining":
                try:
                    date_obj = datetime.strptime(value, '%d %b %Y')
                    output_data[key] = date_obj.strftime('%d/%m/%Y')  # Format as "01/12/2022"
                except ValueError:
                    logger.debug(f"Date format is not correct for key '{key}': {value}")
            else:
                output_data[key] = value
        elif key in output_data['additionalData']:
            output_data['additionalData'][key] = value

    return output_data
