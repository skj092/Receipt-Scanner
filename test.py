from imutils.perspective import four_point_transform
import pytesseract
import argparse
import cv2
import re 

orig = cv2.imread("images/0a0ebd53.jpeg')
image = orig.copy() 
image = imutils.resize(image, width=500)
ratio = orig.shape[1]/ float(image.shape[1])


# convert the image to grayscale, blur it slightly and then apply edge detection 
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
blurred = cv2.GaussianBlur(gray, (5, 5), 0)
edged = cv2.Canny(blurred, 75, 200)


cv2.imshow("Image", image)
cv2.imshow("gray", gray)
cv2.imshow("blurred", blurred)
cv2.imshow("edged", edged)
cv2.waitKey(0)
cv2.destroyAllWindows()