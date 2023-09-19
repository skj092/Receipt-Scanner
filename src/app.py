import uuid
from fastapi import  Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
import traceback
from loguru import logger
from fastapi import FastAPI
from src.inferenceEngine import InferenceEngine
from src.schemas import *
import os
import sys
from src.utils import async_timed_app as async_timed

ENDPOINT1= "/ai/extraction/receipt"

if os.getenv("LOG_ENV", "production") == "production":
    # logger.disable("DEBUG")
    logger.remove()
    logger.add(sys.stderr, level="INFO")


tags_metadata = [
    {
        "name": "Serve",
        "description": "Manage items. So _fancy_ they have their own docs.",
        "externalDocs": {
            "description": "Items external docs",
            "url": "https://fastapi.tiangolo.com/",
        },
    },
]

app = FastAPI(
    title="receipt extraction",
    description="Information Extraction from photos",
    version="2.5.0",
    redoc_url=f"/documentation", docs_url="/explore",
    openapi_tags=tags_metadata,
)





@app.exception_handler(ErrorObject)
async def error_response_exception_handler(request: Request, exc: ErrorObject):
    """
    The function `error_response_exception_handler` handles exceptions and returns a JSON response with
    the error details.

    :param request: The `request` parameter is an instance of the `Request` class, which represents the
    incoming HTTP request
    :type request: Request
    :param exc: The `exc` parameter in the `error_response_exception_handler` function is an instance of
    the `ErrorObject` class. It represents an error that occurred during the processing of a request
    :type exc: ErrorObject
    :return: a JSONResponse object.
    """
    return JSONResponse(
        status_code=int(exc.error_obj.error.status),
        content=exc.error_obj.dict(),
    )
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    """
    The function `validation_exception_handler` handles validation errors in a request and returns an
    appropriate JSON response.

    :param request: The `request` parameter is the HTTP request object that contains information about
    the incoming request, such as headers, query parameters, and request body. It is used to handle
    validation exceptions for the request
    :param exc: The `exc` parameter in the `validation_exception_handler` function is an instance of
    the `pydantic.ValidationError` class. It represents the validation error that occurred during the
    validation of a request JSON
    :return: a JSONResponse object.
    """
    missing_fields = list()
    logger.debug(f"-------******* ------- {exc.errors()}")
    for error_dict in exc.errors():
        if len(error_dict['loc']) > 1 and 'value_error.any_str.min_length' in error_dict['type']\
                or 'value_error.url' in error_dict['type'] or \
                'min_items' in error_dict['type'] or 'value_error.number' in error_dict['type']\
                or 'url_parsing' in error_dict["type"]:
            return JSONResponse(status_code=422, content={
                "error": {
                            'name': "Invalid Input Request JSON Parameter",
                            'status': '422',
                            'msg': f"{'.'.join(str(i) for i in error_dict['loc'][1:])} - {error_dict['msg']}.",
                            'responseCode': 'fail',
                }
            })

        if len(error_dict['loc']) > 1 and error_dict['type'] in ['type_error' , 'url_type' , 'too_short' , 'list_type' , 'int_parsing', 'int_from_float', 'int_type', 'less_than_equal', 'greater_than_equal']:
            return JSONResponse(status_code=422, content={
                "error": {
                            'name': "Invalid Request JSON Key Type",
                            'status': '422',
                            'msg': f"{'.'.join(str(i) for i in error_dict['loc'][1:])} {error_dict['msg']}",
                            'responseCode': 'fail',
                }
            })

        if len(error_dict['loc']) == 1 and error_dict['type'] == 'type_error.dict':
            return JSONResponse(status_code=400, content={
                "error": {
                            'name': "Invalid Request",
                            'status': '400',
                            'msg': "Request JSON must be of type Object",
                            'responseCode': 'fail',
                }
            })

        if error_dict['type'] == 'value_error.jsondecode':
            return JSONResponse(status_code=400, content={
                "error": {
                            'name': "Invalid Request JSON Syntax",
                            'status': '400',
                            'msg': error_dict['msg'],
                            'responseCode': 'fail',
                }
            })

        if len(error_dict['loc']) > 1 and error_dict['type'] in ['value_error.missing' , 'missing']:
            missing_fields.append('.'.join(str(i) for i in error_dict['loc'][1:]))

        if len(error_dict['loc']) == 1 and error_dict['type'] == 'value_error.missing':
            return JSONResponse(status_code=400, content={
                "error": {
                            'name': "Invalid Request",
                            'status': '400',
                            'msg': "Request must be a JSON Object",
                            'responseCode': 'fail',
                }
            })
        if len(error_dict['loc']) > 1 and error_dict['type'] == 'json_invalid':
            return JSONResponse(status_code=400, content={
                "error": {
                            'name': "Invalid Request",
                            'status': '400',
                            'msg': "Request must be a JSON Object",
                            'responseCode': 'fail',
                }
            })
        if len(error_dict['loc']) > 1 and error_dict['msg'] == 'List should have at most 1 item after validation, not 2':
            return JSONResponse(status_code=400, content={
                "error": {
                            'name': "Invalid Request",
                            'status': '400',
                            'msg': "Request must contain only one image url",
                            'responseCode': 'fail',
                }
            })

        if error_dict['type'] == 'request_entity_too_large':
            return JSONResponse(status_code=413, content={
                "error": {
                            'name': "Payload Too Large",
                            'status': '413',
                            'msg': error_dict['msg'],
                            'responseCode': 'fail',
                }
            })

    if len(missing_fields):
        return JSONResponse(status_code=422, content={
            "error": {
                        'name': "JSON Key-Value Missing",
                        'status': '422',
                        'msg': f"{', '.join(missing_fields)} field(s) required",
                        'responseCode': 'fail',
                    }
            })

    error_dict = exc.errors()[0]
    error_dict['name'] = error_dict
    error_dict["status"] = "422"
    error_dict["msg"] = error_dict.pop("msg")
    error_dict.pop("loc")

    return JSONResponse(
        status_code=422,
        content=jsonable_encoder({"error": error_dict}),
    )

# @app.on_startup
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """
    The above function is a middleware in a Python web application that adds a unique request ID to the
    request state for access in route handlers.

    :param request: The `request` parameter represents the incoming HTTP request received by the
    application. It contains information such as the request method, headers, URL, and body
    :type request: Request
    :param call_next: The `call_next` parameter is a callable that represents the next middleware or
    route handler in the chain. It is responsible for handling the current request and returning a
    response. In the case of this middleware, `call_next` is used to pass the request to the next
    middleware or route handler in the
    :return: The response object is being returned.
    """
    # Generate or obtain a request ID
    request_id = str(uuid.uuid4())  # Replace with your custom logic

    # Store the request ID in the request state for access in route handlers
    request.state.request_id = request_id
    # img_request = ImgRequest(**request.query_params, request_id=request_id)
    logger.debug(f'REQUEST_ID : {request_id} | request --- {request}')
    # # Replace the original request with the modified ImgRequest object
    # request = Request(img_request)
    # Proceed with the request handling
    response = await call_next(request)

    return response

@app.post(f"{ENDPOINT1}",
          tags=["Serve"], responses={200: {"model": ResponseSchema},
                                     400: {"model": ErrorResponse400},
                                     422: {"model": ErrorResponse422},
                                     413: {"model": ErrorResponse413},
                                     415: {"model": ErrorResponse415}})
@async_timed()
async def serve_image(
    Imgrequest: ImgRequest, req :Request
    ):
    request_dict = Imgrequest.dict()
    request_id = req.state.request_id
    try:
        logger.debug(f"REQUEST_ID : {request_id} | input request -- {request_dict}")
        ie = InferenceEngine(request_id)
        response = await ie.execute_image(request_dict)
    except Exception as e:
        logger.error(f'REQUEST_ID : {request_id} |  error -- {e}')
        logger.error(f'REQUEST_ID : {request_id} |  traceback --- {traceback.format_exc()}')
        raise e

    # response = ResponseSchema(**response)
    return response

