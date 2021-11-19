import time
import asyncio
import json
import os
import io
from functools import reduce
from typing import Any, Callable, ClassVar, Dict, Optional
import argparse
import math

import mss
import mss.tools
import numpy as np
from pywizlight import wizlight, PilotBuilder, discovery
from colorthief import ColorThief
from PIL import Image

from timer import Timer

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
	# which screen monitor to use
	monitor_number = 1

	# file to store settings
	setfile = 'settings.json'
	# The settings
	settings = {}

	# never go below this brightness (0-255)
	min_brightness = 70
	
	# dominant color quality (1-best, 10-worst)
	quality = 1

	# refresh rate (hz)
	rate = 5

	# percentage of screen to examine (from center) (0-100)
	screen_per = 60

	# Reduce screencapture width to this (pixels). Maintains aspect ratio
	redu_width = 600 

	async def init_bulb(self):
		"""
		Find and use relevant bulb
		"""
		if getattr(self, "bulb_ip", None):
			self.light = wizlight(self.settings.bulb_ip)
		elif os.path.isfile(self.setfile):
			with open(self.setfile, 'r') as myfile:
				data=myfile.read()
				self.settings = json.loads(data)
		else:
			bulbs = await discovery.discover_lights(broadcast_space="192.168.1.255")
			# Print the IP address of the bulb on index 0
			print(f"Bulb IP address: {bulbs[0].ip}")

			# Iterate over all returned bulbs
			for bulb in bulbs:
				print(bulb.__dict__)

			# Set up a standard light - use first found
			#save ip for ease of future use
			self.settings["bulb_ip"] = bulbs[0].ip
			with open(self.setfile, 'w', encoding="utf-8") as f:
				json.dump(self.settings, f)

		self.light = wizlight(self.settings["bulb_ip"])
		print(f"Using light with IP: {self.settings['bulb_ip']}")

	def grab_color(self):
		"""
		return float rgb average of screen 
		"""
		with mss.mss() as sct:
			monitor = sct.monitors[self.monitor_number]

			# Capture a bbox using percent values
			len_factor = math.sqrt(self.screen_per)
			border = int((100 - len_factor)/2)
			left = monitor["left"] + monitor["width"] * border // 100
			top = monitor["top"] + monitor["height"] * border // 100  
			right = monitor["width"] * 1-(border // 100)
			lower = monitor["height"] * 1-(border // 100)
			bbox = (left, top, right, lower)
			
			sct_img = sct.grab(bbox)
			# mss.tools.to_png(sct_img.rgb, sct_img.size, output="screenshot.png")

			return dominat_color(sct_img, self.rate, self.redu_width)
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
		brightness = max(color) if max(color) > self.min_brightness else self.min_brightness

		sf = 255/(max(color))
		c = [int(sf * c) for c in color]
		return (brightness, c)


	async def exec(self):
		"""
		Continually run the program
		"""
		prev_time = 0
		i = 0

		if not self.light:
			raise 
		# while "Screen capturing":
		while i == 0:

			col = self.grab_color()

			if not 'prev_col' in locals():
				# some clearly distinct color
				prev_col = (-1000,-1000,-1000)

			# Only ask  to update bulb when color is different
			if not similar(col, prev_col):

				b, r = self.bulb_scale(col)

				print(f"rgb: {r} \t b: {b}")
				# Set bulb to screen color
				await self.light.turn_on(PilotBuilder(rgb = r, brightness=b))

				prev_col = col

			else:
				print("Skip!")

			# waiting　if necessary. Dont run loop that often
			cur_time = time.time()
			if (cur_time - prev_time) < (1/self.rate):
				print(f"sleeping {1/self.rate - (cur_time - prev_time)}")
				time.sleep(1/self.rate - (cur_time - prev_time))

			prev_time = time.time()
			i=i+1

def parse_args():
	parser = argparse.ArgumentParser(description='Match a Wiz Bulb color to that on screen',
									formatter_class=argparse.ArgumentDefaultsHelpFormatter)

	# Add the arguments
	parser.add_argument('-s',
						'--search',
						action='store_true',
						help='Search for available bulbs, print IP addresses, and exit')
	parser.add_argument('-ip',
						type=str,
						help='known IP of bulb to use')
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
	parser.add_argument('--screen_percesnt',
						type=int,
						default=600,
						help='Reduce screencapture width to this amount (pixels). Maintains aspect ratio')
	# Execute the parse_args() method
	args = parser.parse_args()

parse_args()
sl = ScreenLight()

loop = asyncio.get_event_loop()
loop.run_until_complete(sl.init_bulb())
loop.run_until_complete(sl.exec())




	# # percentage of screen to examine (from center) (0-100)
	# screen_per = 60

	# # Reduce screencapture width to this (pixels). Maintains aspect ratio
	# redu_width = 600 
