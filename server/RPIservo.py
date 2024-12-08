#!/usr/bin/env python3
# File name   : servo.py
# Description : Control Servos
# Author      : William
# Date        : 2019/02/23

from __future__ import division
import time
import sys
import threading
import random

# ======================================================================
# IMPORTANT UPDATE NOTES:
#
# This code was originally written using the legacy 'Adafruit_PCA9685' library
# and 'pwm.set_pwm(...)' calls to control servo position with raw PWM values.
# We are now using the newer Adafruit CircuitPython libraries:
#   - adafruit_pca9685
#   - adafruit_motor.servo
#
# The original code controlled servo positions by sending values like 100 to 520
# to pwm.set_pwm(...). Those values corresponded to a certain pulse width that mapped
# linearly to angles from 0 to 180 degrees. We must preserve the exact same functionality,
# behavior, speed, and range to avoid damaging the devices and maintain external script compatibility.
#
# Original key parameters:
#   ctrlRangeMin = 100 steps
#   ctrlRangeMax = 520 steps
#   angleRange   = 180 degrees
#
# This means:
#   100 steps -> 0 degrees
#   520 steps -> 180 degrees
#
# We will keep all internal arrays (initPos, goalPos, etc.) and computations in terms of these "PWM step" values.
# Only at the point of actually commanding the servo, we will convert these step values to an angle for the servo library.
#
# Conversion from steps to angle:
#   angle = ((PWM_steps - ctrlRangeMin) / (ctrlRangeMax - ctrlRangeMin)) * angleRange
#   angle = ((steps - 100) / (420)) * 180
#
# Since we are using adafruit_motor.servo, we specify min_pulse and max_pulse so that:
#   angle=0° -> ~488us
#   angle=180° -> ~2538us
# This matches original scaling. Each "step" approx. 4.88us, so 100 steps ~488us and 520 steps ~2538us.
#
# We keep all function names, comments, logic, arrays, threading, and behavior as they are critical to maintain backward compatibility.
# Just the underlying method of setting servo position changes.
#
# Please read added comments for detailed explanation.
# ======================================================================

import busio
from board import SCL, SDA
import adafruit_pca9685
from adafruit_motor import servo

# We do not need RPi.GPIO or the legacy Adafruit_PCA9685 Python library anymore.
# They are replaced by the Adafruit CircuitPython PCA9685 and servo libraries.

# The original code did:
# pwm = Adafruit_PCA9685.PCA9685()
# pwm.set_pwm_freq(50)
#
# We now do:
i2c = busio.I2C(SCL, SDA)
pca = adafruit_pca9685.PCA9685(i2c)
pca.frequency = 50

# Initialize servo objects for each channel:
# Calculating pulse widths:
# minPos=100 steps => ~488us
# maxPos=520 steps => ~2538us
# We'll set servo min_pulse=488, max_pulse=2538 to maintain the exact same range.
min_pulse_us = 488
max_pulse_us = 2538

servos = {}
for i in range(16):
    servos[i] = servo.Servo(pca.channels[i], min_pulse=min_pulse_us, max_pulse=max_pulse_us)

# Original initial positions and arrays
init_pwm0 = 300
init_pwm1 = 300
init_pwm2 = 300
init_pwm3 = 300

init_pwm4 = 300
init_pwm5 = 300
init_pwm6 = 300
init_pwm7 = 300

init_pwm8 = 300
init_pwm9 = 300
init_pwm10 = 300
init_pwm11 = 300

init_pwm12 = 300
init_pwm13 = 300
init_pwm14 = 300
init_pwm15 = 300

class ServoCtrl(threading.Thread):
    def __init__(self, *args, **kwargs):
        # Keeping all original arrays and logic unchanged
        self.sc_direction = [1,1,1,1, 1,1,1,1, 1,1,1,1, 1,1,1,1]
        self.initPos = [init_pwm0,init_pwm1,init_pwm2,init_pwm3,
                        init_pwm4,init_pwm5,init_pwm6,init_pwm7,
                        init_pwm8,init_pwm9,init_pwm10,init_pwm11,
                        init_pwm12,init_pwm13,init_pwm14,init_pwm15]
        self.goalPos = [300,300,300,300, 300,300,300,300 ,300,300,300,300 ,300,300,300,300]
        self.nowPos  = [300,300,300,300, 300,300,300,300 ,300,300,300,300 ,300,300,300,300]
        self.bufferPos  = [300.0,300.0,300.0,300.0, 300.0,300.0,300.0,300.0 ,300.0,300.0,300.0,300.0 ,300.0,300.0,300.0,300.0]
        self.lastPos = [300,300,300,300, 300,300,300,300 ,300,300,300,300 ,300,300,300,300]
        self.ingGoal = [300,300,300,300, 300,300,300,300 ,300,300,300,300 ,300,300,300,300]

        # NOTE: The original code changed maxPos to 520 from 560.
        # We must keep it exactly the same to maintain correct angle mapping.
        self.maxPos  = [520,520,520,520, 520,520,520,520 ,520,520,520,520 ,520,520,520,520]
        self.minPos  = [100,100,100,100, 100,100,100,100 ,100,100,100,100 ,100,100,100,100]
        self.scSpeed = [0,0,0,0, 0,0,0,0 ,0,0,0,0 ,0,0,0,0]

        self.ctrlRangeMax = 520
        self.ctrlRangeMin = 100
        self.angleRange = 180

        '''
        scMode: 'init' 'auto' 'certain' 'quick' 'wiggle'
        '''
        self.scMode = 'auto'
        self.scTime = 2.0
        self.scSteps = 30
        
        self.scDelay = 0.037
        self.scMoveTime = 0.037

        self.goalUpdate = 0
        self.wiggleID = 0
        self.wiggleDirection = 1

        super(ServoCtrl, self).__init__(*args, **kwargs)
        self.__flag = threading.Event()
        self.__flag.clear()

    def pause(self):
        # Keep original function and comment
        print('......................pause..........................')
        self.__flag.clear()

    def resume(self):
        # Keep original function and comment
        print('resume')
        self.__flag.set()


    def pwm_to_angle(self, steps):
        # Convert the internal PWM steps (100 to 520) to a servo angle (0 to 180)
        # angle = ((steps - ctrlRangeMin) / (ctrlRangeMax - ctrlRangeMin)) * angleRange
        angle = (steps - self.ctrlRangeMin) / float(self.ctrlRangeMax - self.ctrlRangeMin) * self.angleRange
        if angle < 0: angle = 0
        if angle > 180: angle = 180
        return angle

    def set_servo_pwm(self, ID, PWM_input):
        # This function replaces the original pwm.set_pwm(ID, 0, PWM_input) calls.
        # We do not change the logic, just the underlying method.
        # We keep the same PWM_input values, and convert them to angle.
        angle = self.pwm_to_angle(PWM_input)
        servos[ID].angle = angle

    def moveInit(self):
        # scMode = 'init', move all servos to initPos
        self.scMode = 'init'
        for i in range(0,16):
            # replaced: pwm.set_pwm(i,0,self.initPos[i])
            self.set_servo_pwm(i, self.initPos[i])
            self.lastPos[i] = self.initPos[i]
            self.nowPos[i] = self.initPos[i]
            self.bufferPos[i] = float(self.initPos[i])
            self.goalPos[i] = self.initPos[i]
        self.pause()

    def initConfig(self, ID, initInput, moveTo):
        # Sets initial position config if within allowed range
        if initInput > self.minPos[ID] and initInput < self.maxPos[ID]:
            self.initPos[ID] = initInput
            if moveTo:
                # replaced: pwm.set_pwm(ID,0,self.initPos[ID])
                self.set_servo_pwm(ID, self.initPos[ID])
        else:
            print('initPos Value Error.')

    def moveServoInit(self, ID):
        # Move selected servos to their initPos
        self.scMode = 'init'
        for i in range(0,len(ID)):
            # replaced: pwm.set_pwm(ID[i], 0, self.initPos[ID[i]])
            self.set_servo_pwm(ID[i], self.initPos[ID[i]])
            self.lastPos[ID[i]] = self.initPos[ID[i]]
            self.nowPos[ID[i]] = self.initPos[ID[i]]
            self.bufferPos[ID[i]] = float(self.initPos[ID[i]])
            self.goalPos[ID[i]] = self.initPos[ID[i]]
        self.pause()

    def posUpdate(self):
        # Update lastPos to nowPos
        self.goalUpdate = 1
        for i in range(0,16):
            self.lastPos[i] = self.nowPos[i]
        self.goalUpdate = 0

    def speedUpdate(self, IDinput, speedInput):
        # Update speeds
        for i in range(0,len(IDinput)):
            self.scSpeed[IDinput[i]] = speedInput[i]

    def moveAuto(self):
        # Auto mode: moves from lastPos to goalPos in scTime with scSteps
        for i in range(0,16):
            self.ingGoal[i] = self.goalPos[i]

        for i in range(0, self.scSteps):
            for dc in range(0,16):
                if not self.goalUpdate:
                    self.nowPos[dc] = int(round((self.lastPos[dc] + (((self.goalPos[dc] - self.lastPos[dc])/self.scSteps)*(i+1))),0))
                    # replaced: pwm.set_pwm(dc, 0, self.nowPos[dc])
                    self.set_servo_pwm(dc, self.nowPos[dc])

                if self.ingGoal != self.goalPos:
                    self.posUpdate()
                    time.sleep(self.scTime/self.scSteps)
                    return 1
            time.sleep((self.scTime/self.scSteps - self.scMoveTime))

        self.posUpdate()
        self.pause()
        return 0

    def moveCert(self):
        # Certain mode: move at certain speed until goal is reached
        for i in range(0,16):
            self.ingGoal[i] = self.goalPos[i]
            self.bufferPos[i] = self.lastPos[i]

        while self.nowPos != self.goalPos:
            for i in range(0,16):
                if self.lastPos[i] < self.goalPos[i]:
                    self.bufferPos[i] += self.pwmGenOut(self.scSpeed[i])/(1/self.scDelay)
                    newNow = int(round(self.bufferPos[i], 0))
                    if newNow > self.goalPos[i]:newNow = self.goalPos[i]
                    self.nowPos[i] = newNow
                elif self.lastPos[i] > self.goalPos[i]:
                    self.bufferPos[i] -= self.pwmGenOut(self.scSpeed[i])/(1/self.scDelay)
                    newNow = int(round(self.bufferPos[i], 0))
                    if newNow < self.goalPos[i]:newNow = self.goalPos[i]
                    self.nowPos[i] = newNow

                if not self.goalUpdate:
                    # replaced: pwm.set_pwm(i, 0, self.nowPos[i])
                    self.set_servo_pwm(i, self.nowPos[i])

                if self.ingGoal != self.goalPos:
                    self.posUpdate()
                    return 1
            self.posUpdate()
            time.sleep(self.scDelay-self.scMoveTime)
        else:
            self.pause()
            return 0

    def pwmGenOut(self, angleInput):
        # Convert angle difference to PWM step difference
        # same logic as original code
        return int(round(((self.ctrlRangeMax-self.ctrlRangeMin)/self.angleRange*angleInput),0))

    def setAutoTime(self, autoSpeedSet):
        self.scTime = autoSpeedSet

    def setDelay(self, delaySet):
        self.scDelay = delaySet

    def autoSpeed(self, ID, angleInput):
        # Auto mode with given angles
        self.scMode = 'auto'
        self.goalUpdate = 1
        for i in range(0,len(ID)):
            newGoal = self.initPos[ID[i]] + self.pwmGenOut(angleInput[i])*self.sc_direction[ID[i]]
            if newGoal>self.maxPos[ID[i]]:newGoal=self.maxPos[ID[i]]
            elif newGoal<self.minPos[ID[i]]:newGoal=self.minPos[ID[i]]
            self.goalPos[ID[i]] = newGoal
        self.goalUpdate = 0
        self.resume()

    def certSpeed(self, ID, angleInput, speedSet):
        # Certain speed mode with given angle input
        self.scMode = 'certain'
        self.goalUpdate = 1
        for i in range(0,len(ID)):
            newGoal = self.initPos[ID[i]] + self.pwmGenOut(angleInput[i])*self.sc_direction[ID[i]]
            if newGoal>self.maxPos[ID[i]]:newGoal=self.maxPos[ID[i]]
            elif newGoal<self.minPos[ID[i]]:newGoal=self.minPos[ID[i]]
            self.goalPos[ID[i]] = newGoal
        self.speedUpdate(ID, speedSet)
        self.goalUpdate = 0
        self.resume()

    def moveWiggle(self):
        # Wiggle mode
        self.bufferPos[self.wiggleID] += self.wiggleDirection*self.sc_direction[self.wiggleID]*self.pwmGenOut(self.scSpeed[self.wiggleID])/(1/self.scDelay)
        newNow = int(round(self.bufferPos[self.wiggleID], 0))
        if self.bufferPos[self.wiggleID] > self.maxPos[self.wiggleID]:
            self.bufferPos[self.wiggleID] = self.maxPos[self.wiggleID]
        elif self.bufferPos[self.wiggleID] < self.minPos[self.wiggleID]:
            self.bufferPos[self.wiggleID] = self.minPos[self.wiggleID]
        self.nowPos[self.wiggleID] = newNow
        self.lastPos[self.wiggleID] = newNow
        if self.bufferPos[self.wiggleID] < self.maxPos[self.wiggleID] and self.bufferPos[self.wiggleID] > self.minPos[self.wiggleID]:
            # replaced: pwm.set_pwm(self.wiggleID, 0, self.nowPos[self.wiggleID])
            self.set_servo_pwm(self.wiggleID, self.nowPos[self.wiggleID])
        else:
            self.stopWiggle()
        time.sleep(self.scDelay-self.scMoveTime)

    def stopWiggle(self):
        self.pause()
        self.posUpdate()

    def singleServo(self, ID, direcInput, speedSet):
        # Single servo wiggle mode
        self.wiggleID = ID
        self.wiggleDirection = direcInput
        self.scSpeed[ID] = speedSet
        self.scMode = 'wiggle'
        self.posUpdate()
        self.resume()

    def moveAngle(self, ID, angleInput):
        # Move servo by angleInput from initPos, keep same logic
        self.nowPos[ID] = int(self.initPos[ID] + self.sc_direction[ID]*self.pwmGenOut(angleInput))
        if self.nowPos[ID] > self.maxPos[ID]:self.nowPos[ID] = self.maxPos[ID]
        elif self.nowPos[ID] < self.minPos[ID]:self.nowPos[ID] = self.minPos[ID]
        self.lastPos[ID] = self.nowPos[ID]
        # replaced: pwm.set_pwm(ID, 0, self.nowPos[ID])
        self.set_servo_pwm(ID, self.nowPos[ID])

    def scMove(self):
        # Execute movements based on scMode
        if self.scMode == 'init':
            self.moveInit()
        elif self.scMode == 'auto':
            self.moveAuto()
        elif self.scMode == 'certain':
            self.moveCert()
        elif self.scMode == 'wiggle':
            self.moveWiggle()

    def setPWM(self, ID, PWM_input):
        # Set raw PWM steps directly
        self.lastPos[ID] = PWM_input
        self.nowPos[ID] = PWM_input
        self.bufferPos[ID] = float(PWM_input)
        self.goalPos[ID] = PWM_input
        # replaced: pwm.set_pwm(ID, 0, PWM_input)
        self.set_servo_pwm(ID, PWM_input)
        self.pause()

    def run(self):
        # Thread run loop
        while 1:
            self.__flag.wait()
            self.scMove()
            pass


if __name__ == '__main__':
    sc = ServoCtrl()
    sc.start()
    while 1:
        sc.moveAngle(0,(random.random()*100-50))
        time.sleep(1)
        sc.moveAngle(1,(random.random()*100-50))
        time.sleep(1)
        '''
        sc.singleServo(0, 1, 5)
        time.sleep(6)
        sc.singleServo(0, -1, 30)
        time.sleep(1)
        '''
        '''
        delaytime = 5
        sc.certSpeed([0,7], [60,0], [40,60])
        print('xx1xx')
        time.sleep(delaytime)

        sc.certSpeed([0,7], [0,60], [40,60])
        print('xx2xx')
        time.sleep(delaytime+2)

        # sc.moveServoInit([0])
        # time.sleep(delaytime)
        '''
        '''
        pwm.set_pwm(0,0,560)
        time.sleep(1)
        pwm.set_pwm(0,0,100)
        time.sleep(2)
        '''
        pass
    pass
