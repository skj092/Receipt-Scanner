import os
import requests
import filetype
from loguru import logger
from src.schemas import ErrorObject
import sys
import traceback
from src.utils import *
import fitz
import cv2
import pytesseract
import re
import numpy as np

if os.getenv("LOG_ENV" ,"production") == "production":
    # logger.disable("DEBUG")
    logger.remove()
    logger.add(sys.stderr, level="INFO")

@timed_methods
class InferenceEngine:
    def __init__(self , request_id):
        self.request_id = request_id
        self.supported_formats = ["tif" , "tiff" , 'jpeg','png','jpg']

    def download_and_validate(self, url):
        """
        The function `download_and_validate_file` downloads a file from a given URL, validates its size and
        file type, and returns the path of the downloaded file.

        :param url: The `url` parameter is the URL of the file that needs to be downloaded and validated
        :return: The function `download_and_validate_file` returns the temporary file path where the
        downloaded file is saved.
        """
        # tmp_file_pref = "/tmp"
        try:
            img_data = requests.get(url)
            if img_data.status_code != 200:
                logger.error(f"REQUEST_ID : {self.request_id} | request failed unable to download , got {img_data.status_code} error | returning 422")
                raise ErrorObject({"error":{"status":"422"}})
            file_bytes  =  img_data.content
            if (sys.getsizeof(file_bytes) /10485676) > 10:
                logger.error(f"REQUEST_ID : {self.request_id} | payload too large | returning 413")
                raise ErrorObject({"error":{"status":"413"}})
            ext = filetype.guess_extension(file_bytes)
            if ext == "pdf":
                pdf_reader = fitz.open(stream=file_bytes)
                if len(pdf_reader) > 2:
                    logger.error(f"REQUEST_ID: {self.request_id} | PDF file with more than 2 pages detected | returning 422")
                    raise ErrorObject({"error": {"status": "422"}})
            if ext not in self.supported_formats:
                logger.error(f"REQUEST_ID : {self.request_id} | invalid filetype ,got {ext} file | returning 413")
                raise ErrorObject({"error":{"status":"415"}})
            return file_bytes , ext
        except Exception as e:
            if isinstance(e, ErrorObject):
                raise e
            else:
                logger.error(f"REQUEST_ID : {self.request_id} | other exception ")
                logger.error(f"REQUEST_ID : {self.request_id} | execption trace back --- {traceback.format_exc()}")
                raise ErrorObject({"error":{"status":"500"}})

    def img_preprocessing(self, img):
        """preprocess the image before callling pytesseract"""
        image = np.frombuffer(img, np.uint8)
        img = cv2.imdecode(image, cv2.IMREAD_COLOR)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        img = cv2.medianBlur(img, 5)
        img = cv2.adaptiveThreshold(img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11,2)
        return img

    def get_ocr(self, image):
        text = pytesseract.image_to_string(image)
        return text

    def get_bill(self,ocr_text):
        k=[]
        k.append(ocr_text.split('\n'))
        for i in k:
          j=0
          while j<len(i):
              result1=re.search(r"subtotal", i[j].lower())
              result2=re.search(r"total", i[j].lower())
              result3=re.search(r"amount", i[j].lower())
              result4=re.search(r"cash", i[j].lower())
              if result1==None and result2==None and result3==None:
                i.pop(j)
              else:
                j=j+1
        final=[]
        for i in range(len(k)):
          for_this=[]
          for j in range(len(k[i])):
            result=re.findall("\d+\.\d+",k[i][j])     #This searches all the floating values in the string containg total,subtotal and amount
            if len(result)>0:
              for_this.append(float(result[0]))
          if len(for_this)==0:
            final.append(0)
          else:
            final.append(max(for_this))               #Appending the maximum float value present for each image since total amount is the sum of prices of all the items
        for i in range(len(final)):
          if final[i]==0:
            final[i]=sum(final)/len(final)
        return final[0]

    async def execute_image(self, request):
        try:
            file_bytes, ext = self.download_and_validate(request["img_url"][0])
            img_preprocessed = self.img_preprocessing(file_bytes)
            text = self.get_ocr(img_preprocessed)
            result = self.get_bill(text)
            logger.info(f"REQUEST_ID : {self.request_id} | result --- {result}")
            return result
        except Exception as e:
            if isinstance(e, ErrorObject):
                raise e
            else:
                logger.error(f"REQUEST_ID : {self.request_id} | other exception ")
                logger.error(f"REQUEST_ID : {self.request_id} | execption trace back --- {traceback.format_exc()}")
                raise ErrorObject({"error":{"status":"500"}})
