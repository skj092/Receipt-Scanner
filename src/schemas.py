from pydantic import BaseModel , conlist , confloat , AnyHttpUrl, conint
from typing import Dict , Optional , List ,Any, Callable, Generator, Type, TypeVar
from enum import Enum
from fastapi import Query , Request




class ErrorObject400(BaseModel):
    # name: str = "Invalid Request"
    status: str = "400"
    msg: str = "Request must be a JSON Object"
    responseCode: str = "fail"

class ErrorObject422(BaseModel):
    # name: str = "JSON Key-Value Missing"
    status: str = "422"
    msg: str = "var field(s) required"
    responseCode: str = "fail"

class ErrorObject413(BaseModel):
    # name: str = "JSON Key-Value Missing"
    status: str = "413"
    msg: str = "payload too large  , Maximum allowed size for document is 10MB."
    responseCode: str = "fail"

class ErrorObject415(BaseModel):
    # name: str = "JSON Key-Value Missing"
    status: str = "415"
    msg: str = "Media type not supported  , Please send the document in one of the following formats: PNG/JPEG/JPG/TIFF/TIF/PDF."
    responseCode: str = "fail"

class ErrorObject500(BaseModel):
    # name: str = "JSON Key-Value Missing"
    status: str = "500"
    msg: str = "unable to process - internal server error"
    responseCode: str = "fail"

class ErrorResponse422(BaseModel):
    error: ErrorObject422

class ErrorResponse400(BaseModel):
    error: ErrorObject400

class ErrorResponse413(BaseModel):
    error: ErrorObject413

class ErrorResponse415(BaseModel):
    error: ErrorObject415
class ErrorResponse500(BaseModel):
    error: ErrorObject500
class BaseRequest(BaseModel):
    requestId: str = None

class ImageRequest(BaseRequest):
    img_url: conlist(AnyHttpUrl , min_length=1 , max_length=1) = Query(
        ..., description="List of image(s) [JPEG/TIFF/PNG/PDF] urls."
    )


class ImgRequest(ImageRequest):
    pass

class ResultObject(BaseModel):
    pass

class ResponseSchema(ResultObject):
    pass


# The class `ErrorObject` is used to handle different types of error responses based on their status
# code.
class ErrorObject(Exception):
    def __init__(self, response):
        if response['error']['status'] == '422':
            self.error_obj = ErrorResponse422(**response)
        elif response['error']['status'] == '400':
            self.error_obj = ErrorResponse400(**response)
        elif response['error']['status'] == '413':
            self.error_obj = ErrorResponse413(**response)
        elif response['error']['status'] == '415':
            self.error_obj = ErrorResponse415(**response)
        else:
            self.error_obj = ErrorResponse500(**response)