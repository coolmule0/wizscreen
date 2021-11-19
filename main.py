import time
import asyncio
import json
import os
import io

from mss import mss
import numpy as np
import cv2
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

def dominat_color(sct_img, quality=1):
	"""
	Returns the dominant colour in an image
	"""
	img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")

	with io.BytesIO() as file_object:
		img.save(file_object, "PNG")
		cf = ColorThief(file_object)
		col = cf.get_color()

	return col
	 

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
				# Turn off all available bulbs
				# await bulb.turn_off()

			# Set up a standard light - use first found
			# bulb_ip = bulbs[0].ip
			# self.light = wizlight(bulbs[0].ip)

			#save ip for ease of future use
			# ...
			self.settings["bulb_ip"] = bulbs[0].ip
			with open(self.setfile, 'w', encoding="utf-8") as f:
				json.dump(self.settings, f)

		self.light = wizlight(self.settings["bulb_ip"])
		print(f"Using light with IP: {self.settings['bulb_ip']}")

	def grab_color(self):
		"""
		return float rgb average of screen 
		"""
		with mss() as sct:
			monitor = sct.monitors[self.monitor_number]
			sct_img = sct.grab(monitor)
			

			return dominat_color(sct_img, self.quality)
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
		if not self.light:
			raise 
		while "Screen capturing":

			col = self.grab_color()

			# r = tuple([ int(c.item()) for c in rgb])

			b, r = self.bulb_scale(col)

			print(f"rgb: {r} \t b: {b}")
			# Set bulb to screen color
			await self.light.turn_on(PilotBuilder(rgb = r, brightness=b))

			time.sleep(1/self.rate)
			# # Press "q" to quit
			# if cv2.waitKey(250) & 0xFF == ord("q"):
			#     cv2.destroyAllWindows()
			#     break



sl = ScreenLight()

loop = asyncio.get_event_loop()
loop.run_until_complete(sl.init_bulb())
loop.run_until_complete(sl.exec())
