# ======================================================================
# IMPORTANT UPDATE NOTES FOR COMPATIBILITY WITH NEW LIBRARIES:
#
# This script uses base.py, which was refactored
# to use the new Adafruit CircuitPython libraries (adafruit_pca9685 and adafruit_motor.servo) instead
# of the old RPi.GPIO and Adafruit_PCA9685 Python libraries. The underlying servo control logic in
# base.py has been preserved to ensure the exact same functionality, ranges, and movement logic.
# All function names, behavior, and variable usage remain unchanged, so other external scripts depending
# on these functions will still work.
#
# Key points:
# - Internally, servo logic now converts the old "PWM steps" to servo angles and sets them using the new
#   libraries. We have ensured that the min/max ranges, angles, and speed profiles are exactly the same,
#   so the servos will move as before and not be damaged.
# - This webServer.py script does not directly control the PWM or import old servo libraries anymore; it
#   solely relies on base.py for servo actions. Therefore, we do not have to change logic here, only
#   confirm that we are now using the updated base.py module.
# ======================================================================

# System libs
# import time
import sys
import atexit
import signal
import threading
# import os
import socket
import logging
import asyncio
import websockets
import json

# Custom modules
import config
import functions
import servo
from system import info
from light import strip
# import switch  # The 3 single LEDs switches, we don't need them for now
from app import WebApp

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
# logging.getLogger('websockets').setLevel(logging.INFO)

shutdown_called = False

def graceful_shutdown(*args):
	global shutdown_called
	if shutdown_called:
		return
	shutdown_called = True

	logger.info("Gracefully shutting down...")
	try:
		if RL:
			RL.pause()
		scGear.shutdown()
		P_sc.shutdown()
		T_sc.shutdown()
	except Exception as e:
		logger.error(f"Error during shutdown: {e}")
	finally:
		logger.info("Shutdown complete.")
		sys.exit(0)


logger.info('Starting..')

speed_set = 100
rad = 0.5
turnWiggle = 60

# Initialize servo controllers
scGear = servo.base.ServoCtrl()
scGear.move_init()

P_sc = servo.base.ServoCtrl()
P_sc.start()

T_sc = servo.base.ServoCtrl()
T_sc.start()

# Register graceful shutdown
atexit.register(graceful_shutdown)
signal.signal(signal.SIGINT, graceful_shutdown)
signal.signal(signal.SIGTERM, graceful_shutdown)

# modeSelect = 'none'
modeSelect = 'PT'

init_pwms = scGear.init_positions.copy()

logger.info('Initializing functions')
functions.Functions().start()

# def servoPosInit():  # Unused
# 	# This function sets initial servo positions using init_position,
# 	# which internally now uses the new servo library.
# 	scGear.set_init_position(2, init_pwms[2], True)
# 	P_sc.set_init_position(1, init_pwms[1], True)
# 	T_sc.set_init_position(0, init_pwms[0], True)


def function_select(command_input, response):
	global direction_command, turn_command, SmoothMode, steadyMode

	# The logic remains unchanged.
	# No direct servo control here, only mode switching.
	if 'scan' == command_input:
		pass

	elif 'findColor' == command_input:
		flask_app.mode_select('findColor')

	elif 'motionGet' == command_input:
		flask_app.mode_select('watchDog')

	elif 'stopCV' == command_input:
		flask_app.mode_select('none')
		# Single LEDs off (not used for now)
		# switch.switch(1,0)
		# switch.switch(2,0)
		# switch.switch(3,0)

	elif 'KD' == command_input:
		servo.move.command(command_input)

	elif 'automaticOff' == command_input:
		servo.move.command(command_input)

	elif 'automatic' == command_input:
		servo.move.command(command_input)

	elif 'trackLine' == command_input:
		flask_app.mode_select('findlineCV')

	elif 'trackLineOff' == command_input:
		flask_app.mode_select('none')

	elif 'police' == command_input:
		RL.police()

	elif 'policeOff' == command_input:
		RL.pause()


# def switch_ctrl(command_input, response):
# 	# Single LEDs management (not used for now)
# 	pass
	# # Control switches, no servo changes here.
	# if 'Switch_1_on' in command_input:
	# 	switch.switch(1,1)
	#
	# elif 'Switch_1_off' in command_input:
	# 	switch.switch(1,0)
	#
	# elif 'Switch_2_on' in command_input:
	# 	switch.switch(2,1)
	#
	# elif 'Switch_2_off' in command_input:
	# 	switch.switch(2,0)
	#
	# elif 'Switch_3_on' in command_input:
	# 	switch.switch(3,1)
	#
	# elif 'Switch_3_off' in command_input:
	# 	switch.switch(3,0)


def robot_ctrl(command_input, response):
	"""
	Robot movements and servo adjustments.
	:param command_input:
	:param response:
	:return:
	"""

	global direction_command, turn_command
	if 'forward' == command_input:
		direction_command = 'forward'
		servo.move.command(direction_command)

	elif 'backward' == command_input:
		direction_command = 'backward'
		servo.move.command(direction_command)

	elif 'DS' in command_input:
		direction_command = 'stand'
		servo.move.command(direction_command)


	elif 'left' == command_input:
		turn_command = 'left'
		servo.move.command(turn_command)

	elif 'right' == command_input:
		turn_command = 'right'
		servo.move.command(turn_command)

	elif 'TS' in command_input:
		turn_command = 'no'
		servo.move.command(turn_command)


	elif 'lookleft' == command_input:
		# P_sc.single_servo(...) now uses new servo code internally, but interface is unchanged.
		P_sc.single_servo(12, 1, 7)

	elif 'lookright' == command_input:
		P_sc.single_servo(12,-1, 7)

	elif 'LRstop' in command_input:
		P_sc.stop_wiggle()

	elif 'up' == command_input:
		T_sc.single_servo(13, 1, 7)

	elif 'down' in command_input:
		T_sc.single_servo(13, -1, 7)

	elif 'UDstop' in command_input:
		T_sc.stop_wiggle()


def config_pwm(command_input, response):
	# Servo calibration
	if 'SiLeft' in command_input:
		servo_num = int(command_input[7:])
		init_pwms[servo_num] = init_pwms[servo_num] - 1
		scGear.set_init_position(servo_num, init_pwms[servo_num], True)

	if 'SiRight' in command_input:
		servo_num = int(command_input[7:])
		init_pwms[servo_num] = init_pwms[servo_num] + 1
		scGear.set_init_position(servo_num, init_pwms[servo_num], True)

	if 'PWMMS' in command_input:
		num_servo = int(command_input[6:])
		config.write("pwm", f"init_pwm{num_servo}", init_pwms[num_servo])

	if 'PWMINIT' == command_input:
		for i in range(0,16):
			scGear.set_init_position(i, init_pwms[i], True)

	if 'PWMD' in command_input:
		reset_pwm = {}
		for i in range(0, 16):
			reset_pwm[f"init_pwm{i}"] = 300
		config.write("pwm", None, reset_pwm)

def wifi_check():
	logger.info('Checking wifi')
	try:
		s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		s.connect(("1.1.1.1",80))
		ipaddr_check = s.getsockname()[0]
		s.close()
		logger.info(f'IP: {ipaddr_check}')
	except:
		logger.error('No wifi')
		# Hotspot use create_ap, deprecated, must re-factor!
		# logger.warning('No wifi, starting AP..')
		# ap_threading=threading.Thread(target=ap_thread)
		# ap_threading.daemon = True
		# ap_threading.start()
		# for intensity in range(50, 256, 50):
		# 	RL.setColor(0, 16, intensity)
		# 	time.sleep(1)
		# RL.setColor(35, 255, 35)
		# logger.info('AP started')


async def check_permit(websocket):
	# User authentication over websocket
	while True:
		recv_str = await websocket.recv()
		cred_dict = recv_str.split(":")
		if cred_dict[0] == "admin" and cred_dict[1] == "123456":
			response_str = "congratulation, you have connect with server\r\nnow, you can do something else"
			await websocket.send(response_str)
			return True
		else:
			response_str = "sorry, the username or password is wrong, please submit again"
			await websocket.send(response_str)

async def recv_msg(websocket):
	global speed_set, modeSelect
	# direction_command = 'no'
	# turn_command = 'no'

	# Communication loop with client
	while True:
		response = {
			'status' : 'ok',
			'title' : '',
			'data' : None
		}

		data = await websocket.recv()
		try:
			data = json.loads(data)
		except Exception as e:
			logger.error(f'Not a JSON: {data}')

		if not data:
			continue

		# Depending on the received data, call the respective functions as before
		if isinstance(data, str):
			robot_ctrl(data, response)
			# Single LEDs management (not used for now)
			# switch_ctrl(data, response)
			function_select(data, response)
			config_pwm(data, response)

			if 'get_info' == data:
				response['title'] = 'get_info'
				response['data'] = [info.get_cpu_temp(), info.get_cpu_use(), info.get_ram_info()]

			if 'wsB' in data:
				try:
					set_b = data.split()
					speed_set = int(set_b[1])
				except:
					pass

			elif 'AR' == data:
				modeSelect = 'AR'
				# What is this for?
				# screen.screen_show(4, 'ARM MODE ON')

			elif 'PT' == data:
				modeSelect = 'PT'
				# What is this for?
				# screen.screen_show(4, 'PT MODE ON')

			#CVFL
			elif 'CVFL' == data:
				flask_app.mode_select('findlineCV')

			elif 'CVFLColorSet' in data:
				color = int(data.split()[1])
				flask_app.camera.colorSet(color)

			elif 'CVFLL1' in data:
				pos = int(data.split()[1])
				flask_app.camera.linePosSet_1(pos)

			elif 'CVFLL2' in data:
				pos = int(data.split()[1])
				flask_app.camera.linePosSet_2(pos)

			elif 'CVFLSP' in data:
				err = int(data.split()[1])
				flask_app.camera.errorSet(err)

			# elif 'defEC' in data:
			# 	fpv.defaultExpCom()

		elif isinstance(data, dict):
			if data['title'] == "findColorSet":
				color = data['data']
				flask_app.color_find_set(color[0],color[1],color[2])

		logger.info(f'Received data: {data}')
		response = json.dumps(response)
		await websocket.send(response)

async def main_logic(websocket):
	logger.info('main_logic')
	await check_permit(websocket)
	await recv_msg(websocket)

def start_websocket_server():
	async def run_server():
		async with websockets.serve(main_logic, '0.0.0.0', 8888):
			logger.info('WebSocket server started on port 8888')
			await asyncio.Future()  # Run forever

	# Create a new event loop for this thread and run the server
	loop = asyncio.new_event_loop()
	asyncio.set_event_loop(loop)
	loop.run_until_complete(run_server())


if __name__ == '__main__':
	logger.info('Starting main loop')

	# LED switch setup (not used for now)
	# switch.switchSetup()
	# switch.set_all_switch_off()

	# ??? What is this for?
	# HOST = ''
	# PORT = 10223
	# BUFSIZ = 1024
	# ADDR = (HOST, PORT)

	try:
		logger.info('Starting RobotLight')
		RL = robotLight.RobotLight()
		RL.start()
		# RL.breath(70,70,255)
		# RL.rainbow()
		RL.stars()
	except Exception as e:
		logger.error(f'Failed to start RobotLight with exception: {e}')
		RL = None

	# global flask_app
	# flask_app = app.webapp()
	logger.info('Starting WebApp')
	flask_app = WebApp()
	flask_app.start_thread()

	# loop = asyncio.get_event_loop()

	# while 1:
	# 	wifi_check()
	# 	try:
	# 		# Start websocket server
	# 		logger.info('Starting websocket server')
	# 		start_server = websockets.serve(main_logic, '0.0.0.0', 8888)
	# 		loop.run_until_complete(start_server)
	# 		logger.info('Server started, waiting for connection...')
	# 		break
	# 	except Exception as e:
	# 		logger.error(f'Loop Exception: {e}')
	# 		if RL:
	# 			RL.setColor(0,0,0)

	# 	try:
	# 		if RL:
	# 			RL.setColor(0,80,255)
	# 	except:
	# 		pass

	# # try:
	# # 	asyncio.get_event_loop().run_forever()
	# # except Exception as e:
	# # 	logger.error(f'Asyncio Exception: {e}')
	# # 	if RL:
	# # 		RL.setColor(0,0,0)
	# # 	move.destroy()
	# # Run the event loop
	# try:
	# 	loop.run_forever()
	# except Exception as e:
	# 	logger.error(f'Asyncio Exception: {e}')
	# 	if RL:
	# 		RL.setColor(0, 0, 0)
	# 	move.destroy()

	# Start the WebSocket server in a new thread
	websocket_thread = threading.Thread(target=start_websocket_server)
	websocket_thread.start()
