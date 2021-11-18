import time
import asyncio
import json
import os

from mss import mss
import numpy as np
import cv2
from pywizlight import wizlight, PilotBuilder, discovery

def bgr2rgb(bgr):
	"""
	Converts bgr arrays (such as opencv) to rgb
	"""
	rgb = [bgr[2], bgr[1], bgr[0]]
	return rgb

def average_color(image):
	"""
	Returns the average colour of an image. 
	Input image should be in cv2 BGR format
	Output in RGB format
	"""
	bgr = np.array(image).mean(axis=(0,1))
	return bgr2rgb(bgr)

def dominat_color(image):
	"""
	Returns the dominant colour in an image
	"""
	return 

class ScreenLight():
	# which screen monitor to use
	monitor_number = 1

	# file to store settings
	setfile = 'settings.json'
	# The settings
	settings = {}

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
			img = np.array(sct.grab(monitor))

			return average_color(img)

	def bulb_scale(self, color):
		"""
		Map colour to brightness and colour
		Input of tuple-integer rgb
		Returns (brightness, color)

		Details: The rgb=(50,50,50) is the same bulb appearance as (255,255,255),
		so also consider brightness and scaling colour values
		"""
		brightness = max(color)

		sf = 255/max(color)
		c = [int(sf * c) for c in color]
		return (brightness, c)


	async def exec(self):
		if not self.light:
			raise 
		while "Screen capturing":

			rgb =self.grab_color()

			r = tuple([ int(c.item()) for c in rgb])

			b, r = self.bulb_scale(r)

			print(f"rgb: {r}")
			# Set bulb to screen color
			await self.light.turn_on(PilotBuilder(rgb = r, brightness=b))

			time.sleep(2)
			# # Press "q" to quit
			# if cv2.waitKey(250) & 0xFF == ord("q"):
			#     cv2.destroyAllWindows()
			#     break



sl = ScreenLight()

loop = asyncio.get_event_loop()
loop.run_until_complete(sl.init_bulb())
loop.run_until_complete(sl.exec())
