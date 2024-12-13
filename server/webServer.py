# ======================================================================
# IMPORTANT UPDATE NOTES FOR COMPATIBILITY WITH NEW LIBRARIES:
#
# This script uses RPIservo.py, which was refactored
# to use the new Adafruit CircuitPython libraries (adafruit_pca9685 and adafruit_motor.servo) instead
# of the old RPi.GPIO and Adafruit_PCA9685 Python libraries. The underlying servo control logic in
# RPIservo.py has been preserved to ensure the exact same functionality, ranges, and movement logic.
# All function names, behavior, and variable usage remain unchanged, so other external scripts depending
# on these functions will still work.
#
# Key points:
# - We still call RPIservo.ServoCtrl() and related methods in exactly the same way.
# - Internally, RPIservo.py now converts the old "PWM steps" to servo angles and sets them using the new
#   libraries. We have ensured that the min/max ranges, angles, and speed profiles are exactly the same,
#   so the servos will move as before and not be damaged.
# - This webServer.py script does not directly control the PWM or import old servo libraries anymore; it
#   solely relies on RPIservo.py for servo actions. Therefore, we do not have to change logic here, only
#   confirm that we are now using the updated RPIservo.py module.
# ======================================================================

# System libs
import time
import threading
import os
import socket
import logging
import asyncio
import websockets
import json

# Custom modules
import config
import move
import info
import RPIservo
import functions
import robotLight
import switch
from app import WebApp

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

logger.info('Starting..')

speed_set = 100
rad = 0.5
turnWiggle = 60

# Initialize servo controllers using the new RPIservo code.
# The interface remains the same as before.
scGear = RPIservo.ServoCtrl()
scGear.moveInit()

P_sc = RPIservo.ServoCtrl()
P_sc.start()

T_sc = RPIservo.ServoCtrl()
T_sc.start()

# modeSelect = 'none'
modeSelect = 'PT'

init_pwms = scGear.initPos.copy()

logger.info('Initializing functions')
functions.Functions().start()


def servoPosInit():
	# This function sets initial servo positions using initConfig,
	# which internally now uses the new servo library.
	scGear.initConfig(2, init_pwms[2], 1)
	P_sc.initConfig(1, init_pwms[1], 1)
	T_sc.initConfig(0, init_pwms[0], 1)


def ap_thread():
	os.system("sudo create_ap wlan0 eth0 Adeept_Robot 12345678")


def functionSelect(command_input, response):
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
		switch.switch(1,0)
		switch.switch(2,0)
		switch.switch(3,0)

	elif 'KD' == command_input:
		move.commandInput(command_input)

	elif 'automaticOff' == command_input:
		move.commandInput(command_input)

	elif 'automatic' == command_input:
		move.commandInput(command_input)

	elif 'trackLine' == command_input:
		flask_app.mode_select('findlineCV')

	elif 'trackLineOff' == command_input:
		flask_app.mode_select('none')

	elif 'police' == command_input:
		RL.police()

	elif 'policeOff' == command_input:
		RL.pause()


def switchCtrl(command_input, response):
	# Control switches, no servo changes here.
	if 'Switch_1_on' in command_input:
		switch.switch(1,1)

	elif 'Switch_1_off' in command_input:
		switch.switch(1,0)

	elif 'Switch_2_on' in command_input:
		switch.switch(2,1)

	elif 'Switch_2_off' in command_input:
		switch.switch(2,0)

	elif 'Switch_3_on' in command_input:
		switch.switch(3,1)

	elif 'Switch_3_off' in command_input:
		switch.switch(3,0)


def robotCtrl(command_input, response):
	# Robot movements and servo adjustments through RPIservo methods.
	# Same logic, now handled internally by the updated RPIservo code.

	global direction_command, turn_command
	if 'forward' == command_input:
		direction_command = 'forward'
		move.commandInput(direction_command)

	elif 'backward' == command_input:
		direction_command = 'backward'
		move.commandInput(direction_command)

	elif 'DS' in command_input:
		direction_command = 'stand'
		move.commandInput(direction_command)


	elif 'left' == command_input:
		turn_command = 'left'
		move.commandInput(turn_command)

	elif 'right' == command_input:
		turn_command = 'right'
		move.commandInput(turn_command)

	elif 'TS' in command_input:
		turn_command = 'no'
		move.commandInput(turn_command)


	elif 'lookleft' == command_input:
		# P_sc.singleServo(...) now uses new servo code internally, but interface is unchanged.
		P_sc.singleServo(12, 1, 7)

	elif 'lookright' == command_input:
		P_sc.singleServo(12,-1, 7)

	elif 'LRstop' in command_input:
		P_sc.stopWiggle()


	elif 'up' == command_input:
		T_sc.singleServo(13, -1, 7)

	elif 'down' in command_input:
		T_sc.singleServo(13, 1, 7)

	elif 'UDstop' in command_input:
		T_sc.stopWiggle()


def configPWM(command_input, response):
	# Servo calibration through initConfig, still unchanged.
	if 'SiLeft' in command_input:
		numServo = int(command_input[7:])
		init_pwms[numServo] = init_pwms[numServo] - 1
		scGear.initConfig(numServo, init_pwms[numServo], 1)

	if 'SiRight' in command_input:
		numServo = int(command_input[7:])
		init_pwms[numServo] = init_pwms[numServo] + 1
		scGear.initConfig(numServo, init_pwms[numServo], 1)

	if 'PWMMS' in command_input:
		num_servo = int(command_input[6:])
		config.write("pwm", f"init_pwm{num_servo}", init_pwms[num_servo])

	if 'PWMINIT' == command_input:
		for i in range(0,16):
			scGear.initConfig(i, init_pwms[i], 1)

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
		logger.warning('No wifi, starting AP..')
		ap_threading=threading.Thread(target=ap_thread)
		ap_threading.daemon = True
		ap_threading.start()
		for intensity in range(50, 256, 50):
			RL.setColor(0, 16, intensity)
			time.sleep(1)
		RL.setColor(35, 255, 35)
		logger.info('AP started')


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
			robotCtrl(data, response)
			switchCtrl(data, response)
			functionSelect(data, response)
			configPWM(data, response)

			if 'get_info' == data:
				response['title'] = 'get_info'
				response['data'] = [info.get_cpu_temp(), info.get_cpu_use(), info.get_ram_info()]

			if 'wsB' in data:
				try:
					set_B=data.split()
					speed_set = int(set_B[1])
				except:
					pass

			elif 'AR' == data:
				modeSelect = 'AR'
				screen.screen_show(4, 'ARM MODE ON')

			elif 'PT' == data:
				modeSelect = 'PT'
				screen.screen_show(4, 'PT MODE ON')

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

async def main_logic(websocket, path):
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
	switch.switchSetup()
	switch.set_all_switch_off()

	HOST = ''
	PORT = 10223
	BUFSIZ = 1024
	ADDR = (HOST, PORT)

	try:
		logger.info('Starting RobotLight')
		RL = robotLight.RobotLight()
		RL.start()
		RL.breath(70,70,255)
	except Exception as e:
		logger.error('Failed to start RobotLight with exception: {e}')
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


