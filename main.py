import time
import asyncio

from mss import mss
import numpy as np
import cv2
from pywizlight import wizlight, PilotBuilder, discovery

def average_color(image):
	"""
	Returns the average colour of an image. 
	Input image should be in cv2 BGR format
	Output in RGB format
	"""
	bgr = np.array(image).mean(axis=(0,1))
	rgb = [bgr[2], bgr[1], bgr[0]]
	return rgb

def dominat_color(image):
	"""
	Returns the dominant colour in an image
	"""
	return 

class ScreenLight():
	# which screen monitor to use
	monitor_number = 1

	async def init_bulb(self):
		"""
		Find and use relevant bulb
		"""
		bulbs = await discovery.discover_lights(broadcast_space="192.168.1.255")
		# Print the IP address of the bulb on index 0
		print(f"Bulb IP address: {bulbs[0].ip}")

		# Iterate over all returned bulbs
		for bulb in bulbs:
			print(bulb.__dict__)
			# Turn off all available bulbs
			# await bulb.turn_off()

		# Set up a standard light - use first found
		self.light = wizlight(bulbs[0].ip)
		print(f"Using light with IP: {bulbs[0].ip}")

	def grab_color(self):
		"""
		
		"""
		with mss() as sct:
			monitor = sct.monitors[self.monitor_number]
			img = np.array(sct.grab(monitor))
			return average_color(img)

	async def exec(self):
		if not self.light:
			raise 
		while "Screen capturing":

			rgb =self.grab_color()
			# rgb_t = self.grab_color().astype(int)
			# print(rgb_t)
			# print(type(rgb_t))
			# print(type(rgb_t[0]))

			r = tuple([ int(c.item()) for c in rgb])

			print(f"rgb: {r}")
			# Set bulb to screen color
			await self.light.turn_on(PilotBuilder(rgb = r))

			time.sleep(2)
			# # Press "q" to quit
			# if cv2.waitKey(250) & 0xFF == ord("q"):
			#     cv2.destroyAllWindows()
			#     break



sl = ScreenLight()

loop = asyncio.get_event_loop()
loop.run_until_complete(sl.init_bulb())
loop.run_until_complete(sl.exec())
