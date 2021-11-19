import time
import asyncio
import io
from functools import reduce
from typing import Any, Callable, ClassVar, Dict, Optional
import argparse
import math
import logging
import sys

import mss
import mss.tools
import numpy as np
from pywizlight import wizlight, PilotBuilder, discovery
from colorthief import ColorThief
from PIL import Image

def bgr2rgb(bgr):
	"""
	Converts bgr arrays (such as opencv) to rgb
	"""
	return bgr[::-1]

def average_color(sct_img):
	"""
	Returns the average colour of an image. 
	Input image should be a mss screep capture
	Output in RGB tuple
	"""
	img = np.array(sct_img)
	bgr = np.array(img).mean(axis=(0,1))
	rgb = bgr2rgb(bgr[:3])
	return tuple([ int(c.item()) for c in rgb])

def dominant_color(sct_img, quality=3, redu_width=600):
	"""
	Returns the dominant colour in an image
	Quality: time spent calculating the dominant color
	Redu_width: reduce the width of the screenshot to this. 0 or less means no reduction
	"""
	img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")

	sf = redu_width / img.width
	img_rez = img.resize((redu_width,int(img.height*sf)), Image.ANTIALIAS)

	with io.BytesIO() as file_object:
		img_rez.save(file_object, "PNG")
		cf = ColorThief(file_object)
		col = cf.get_color(quality=quality)

	return col
	 
def similar(col1, col2):
	"""
	Are two colors similar?
	"""
	# 0-255
	threshold = 10

	res = tuple(map(lambda i, j: abs(i - j)<threshold, col1, col2))

	def truth(a, b):
		return a == b == True
	res2 = reduce(truth, res)
	return res2

class ScreenLight():
	"""
	Find screen colors and communicate with wiz bulb
	"""
	def __init__(self, *args, **kwargs):
		self.__dict__.update(kwargs)


	async def search_bulbs(self):
		"""
		Find any bulbs on the broadcast space
		"""
		bulbs = await discovery.discover_lights(broadcast_space=self.broadcast_space)

		# Iterate over all returned bulbs
		for bulb in bulbs:
			print(bulb.__dict__)


	async def init_bulb(self):
		"""
		Find and use relevant bulb
		"""
		if not getattr(self, "ip", None):
			bulbs = await discovery.discover_lights(broadcast_space=self.broadcast_space)

			# Iterate over all returned bulbs
			for bulb in bulbs:
				print(bulb.__dict__)

			# Set up a standard light - use first found
			self.ip = bulbs[0].ip
			print(f"Using first light found. Light with IP: {self.ip}")

		self.light = wizlight(self.ip)

	def grab_color(self):
		"""
		return float rgb average of screen 
		"""
		with mss.mss() as sct:
			monitor = sct.monitors[self.monitor]

			# Capture a bbox using percent values
			len_factor = math.sqrt(self.screen_percent)
			border = int((100 - len_factor)/2)
			left = monitor["left"] + monitor["width"] * border // 100
			top = monitor["top"] + monitor["height"] * border // 100  
			right = monitor["width"] * 1-(border // 100)
			lower = monitor["height"] * 1-(border // 100)
			bbox = (left, top, right, lower)
			
			sct_img = sct.grab(bbox)
			# mss.tools.to_png(sct_img.rgb, sct_img.size, output="screenshot.png")

			return dominant_color(sct_img, self.rate, self.reduced_width)
			# print(dominat_color(sct_img, 3, redu_width=1080))
			# return average_color(sct_img)


	def bulb_scale(self, color):
		"""
		Map colour to brightness and colour
		Input of tuple-integer rgb
		Returns (brightness, color)

		Details: The rgb=(50,50,50) is the same bulb appearance as (255,255,255),
		so also consider brightness and scaling colour values
		"""
		mx = max(color) if max(color) > 0 else 1
		brightness = max(color) if max(color) > self.brightness else self.brightness

		sf = 255/(max(color))
		c = [int(sf * c) for c in color]
		return (brightness, c)

	async def exec(self):
		"""
		Continually run the program
		"""
		
		if self.search:
			await self.search_bulbs()
			return

		if not getattr(self, "light", None):
			await self.init_bulb()

		prev_time = 0

		print("Press Ctrl+C to quit out the program")
		while "Screen capturing":

			col = self.grab_color()

			if not 'prev_col' in locals():
				# some clearly distinct color
				prev_col = (-1000,-1000,-1000)

			# Only ask  to update bulb when color is different
			if not similar(col, prev_col):

				b, r = self.bulb_scale(col)

				logging.info(f"rgb: {r} \t b: {b}")
				# Set bulb to screen color
				await self.light.turn_on(PilotBuilder(rgb = r, brightness=b))

				prev_col = col

			else:
				logging.info("Skipping this iteration")

			# waiting　if necessary. Dont run loop that often
			cur_time = time.time()
			if (cur_time - prev_time) < (1/self.rate):
				logging.info(f"sleeping {1/self.rate - (cur_time - prev_time)}")
				time.sleep(1/self.rate - (cur_time - prev_time))

			prev_time = time.time()

def parse_args():
	parser = argparse.ArgumentParser(description='Match a Wiz Bulb color to that on screen',
									formatter_class=argparse.ArgumentDefaultsHelpFormatter)

	# Add the arguments
	parser.add_argument('-d',
						'--debug',
						action='store_true',
						help='Prints more verbose messages. Sets to INFO level')
	parser.add_argument('-s',
						'--search',
						action='store_true',
						help='Search for available bulbs, print IP addresses, and exit')
	parser.add_argument('-ip',
						type=str,
						help='known IP of bulb to use')
	parser.add_argument('--broadcast_space',
						type=str,
						default="192.168.1.255",
						help='Search over this space of IP for possible bulbs')
	parser.add_argument('-b',
						'--brightness',
						type=int,
						default=70,
						metavar="[0-255]",
						help='minimum desired brightness of bulb')
	parser.add_argument('-r',
						'--rate',
						type=int,
						default=2,
						help='refresh rate of color change (hz)')
	parser.add_argument('-m',
						'--monitor',
						type=int,
						default=1,
						help='Monitor number to use')
	parser.add_argument('-q',
						'--quality',
						type=int,
						metavar="[1-10]",
						default=3,
						help='Quality of dominant color calculation. 1: highest, 10: lowest')
	parser.add_argument('--screen_percent',
						type=int,
						metavar="[1-100]",
						default=60,
						help='Amount of screen to consider, in percentage. Chances are that things around the edge of the screen do not need consideration')
	parser.add_argument('--reduced_width',
						type=int,
						default=600,
						help='Reduce screencapture width to this amount (pixels). Maintains aspect ratio')
	return parser.parse_args()

if __name__ == "__main__":
	args = parse_args()
	if args.debug:
		root = logging.getLogger()
		root.setLevel(logging.INFO)
	sl = ScreenLight(**vars(args))

	loop = asyncio.get_event_loop()
	loop.run_until_complete(sl.exec())
