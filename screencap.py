import time

from mss import mss
import numpy as np
import cv2

monitor_number = 1

def average_color(image):
	"""
	Returns the average colour of an image
	"""
	return np.array(image).mean(axis=(0,1))

def dominat_color(image):
	"""
	Returns the dominant colour in an image
	"""
	return 

# The simplest use, save a screen shot of the 1st monitor
with mss() as sct:

	monitor = sct.monitors[monitor_number]

	while "Screen capturing":
		last_time = time.time()


		img = np.array(sct.grab(monitor))
		# cv2.imshow("OpenCV/Numpy normal", img)

		print("fps: {} \t rgb: {}".format(1 / (time.time() - last_time), average_color(img)))

		# Press "q" to quit
		if cv2.waitKey(25) & 0xFF == ord("q"):
			cv2.destroyAllWindows()
			break


