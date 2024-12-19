import time
import threading
import logging
import random
import rpi_ws281x
# import RPi.GPIO as GPIO

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RobotLight(threading.Thread):
    def __init__(self, *args, **kwargs):
        self.LED_COUNT	  	= 16	  # Number of LED pixels.
        self.LED_PIN		= 12	  # GPIO pin connected to the pixels (18 uses PWM!).
        self.LED_FREQ_HZ	= 800000  # LED signal frequency in hertz (usually 800khz)
        self.LED_DMA		= 10	  # DMA channel to use for generating signal (try 10)
        self.LED_BRIGHTNESS = 255	 # Set to 0 for darkest and 255 for brightest
        self.LED_INVERT	 = False   # True to invert the signal (when using NPN transistor level shift)
        self.LED_CHANNEL	= 0	   # set to '1' for GPIOs 13, 19, 41, 45 or 53

        self.colorBreathR = 0
        self.colorBreathG = 0
        self.colorBreathB = 0
        self.breathSteps = 10

        self.left_R = 22
        self.left_G = 23
        self.left_B = 24

        self.right_R = 10
        self.right_G = 9
        self.right_B = 25

        # self.on  = GPIO.LOW
        # self.off = GPIO.HIGH

        self.lightMode = 'none'		#'none' 'police' 'breath'

        # Single LED switches, not used for now
        # GPIO.setwarnings(False)
        # GPIO.setmode(GPIO.BCM)
        # GPIO.setup(5, GPIO.OUT)
        # GPIO.setup(6, GPIO.OUT)
        # GPIO.setup(13, GPIO.OUT)

        # GPIO.setup(self.left_R, GPIO.OUT)
        # GPIO.setup(self.left_G, GPIO.OUT)
        # GPIO.setup(self.left_B, GPIO.OUT)
        # GPIO.setup(self.right_R, GPIO.OUT)
        # GPIO.setup(self.right_G, GPIO.OUT)
        # GPIO.setup(self.right_B, GPIO.OUT)

        # Create NeoPixel object with appropriate configuration.
        self.strip = rpi_ws281x.Adafruit_NeoPixel(self.LED_COUNT, self.LED_PIN, self.LED_FREQ_HZ, self.LED_DMA, self.LED_INVERT, self.LED_BRIGHTNESS, self.LED_CHANNEL)
        # Initialize the library (must be called once before other functions).
        self.strip.begin()

        super(RobotLight, self).__init__(*args, **kwargs)
        self.__flag = threading.Event()
        self.__flag.clear()


    # def both_off(self):
    #     GPIO.output(self.left_R, self.off)
    #     GPIO.output(self.left_G, self.off)
    #     GPIO.output(self.left_B, self.off)
    #
    #     GPIO.output(self.right_R, self.off)
    #     GPIO.output(self.right_G, self.off)
    #     GPIO.output(self.right_B, self.off)


    # def both_on(self):
    #     GPIO.output(self.left_R, self.on)
    #     GPIO.output(self.left_G, self.on)
    #     GPIO.output(self.left_B, self.on)
    #
    #     GPIO.output(self.right_R, self.on)
    #     GPIO.output(self.right_G, self.on)
    #     GPIO.output(self.right_B, self.on)


    # def side_on(self, side_X):
    #     GPIO.output(side_X, self.on)


    # def side_off(self, side_X):
    #     GPIO.output(side_X, self.off)


    # def red(self):
    #     self.side_on(self.right_R)
    #     self.side_on(self.left_R)


    # def green(self):
    #     self.side_on(self.right_G)
    #     self.side_on(self.left_G)


    # def blue(self):
    #     self.side_on(self.right_B)
    #     self.side_on(self.left_B)


    # def yellow(self):
    #     self.red()
    #     self.green()


    # def pink(self):
    #     self.red()
    #     self.blue()


    # def cyan(self):
    #     self.blue()
    #     self.green()


    # def turnLeft(self):
    #     GPIO.output(self.left_G, self.on)
    #     GPIO.output(self.left_R, self.on)
    #
    # def turnRight(self):
    #     GPIO.output(self.right_G, self.on)
    #     GPIO.output(self.right_R, self.on)

    # Define functions which animate LEDs in various ways.
    def set_color(self, r, g, b):
        """Wipe color across display a pixel at a time."""
        color = rpi_ws281x.Color(int(r),int(g),int(b))
        for i in range(self.strip.numPixels()):
            self.strip.setPixelColor(i, color)
            self.strip.show()


    def set_some_color(self, r, g, b, ids):
        color = rpi_ws281x.Color(int(r),int(g),int(b))
        # logger.info(int(R),'  ',int(G),'  ',int(B))
        for i in ids:
            self.strip.setPixelColor(i, color)
            self.strip.show()


    def pause(self):
        self.lightMode = 'none'
        self.set_color(0,0,0)
        self.__flag.clear()


    def resume(self):
        self.__flag.set()


    def police(self):
        self.lightMode = 'police'
        self.resume()


    def police_processing(self):
        while self.lightMode == 'police':
            for i in range(0,3):
                self.set_some_color(0,0,255,[0,1,2,3,4,5,6,7,8,9,10,11])
                # self.blue()
                time.sleep(0.05)
                self.set_some_color(0,0,0,[0,1,2,3,4,5,6,7,8,9,10,11])
                # self.both_off()
                time.sleep(0.05)
            if self.lightMode != 'police':
                break
            time.sleep(0.1)
            for i in range(0,3):
                self.set_some_color(255,0,0,[0,1,2,3,4,5,6,7,8,9,10,11])
                # self.red()
                time.sleep(0.05)
                self.set_some_color(0,0,0,[0,1,2,3,4,5,6,7,8,9,10,11])
                # self.both_off()
                time.sleep(0.05)
            time.sleep(0.1)


    def breath(self, r_input, g_input, b_input):
        self.lightMode = 'breath'
        self.colorBreathR = r_input
        self.colorBreathG = g_input
        self.colorBreathB = b_input
        self.resume()


    def breath_processing(self):
        while self.lightMode == 'breath':
            for i in range(0,self.breathSteps):
                if self.lightMode != 'breath':
                    break
                self.set_color(self.colorBreathR*i/self.breathSteps, self.colorBreathG*i/self.breathSteps, self.colorBreathB*i/self.breathSteps)
                time.sleep(0.03)
            for i in range(0,self.breathSteps):
                if self.lightMode != 'breath':
                    break
                self.set_color(self.colorBreathR-(self.colorBreathR*i/self.breathSteps), self.colorBreathG-(self.colorBreathG*i/self.breathSteps), self.colorBreathB-(self.colorBreathB*i/self.breathSteps))
                time.sleep(0.03)

    def rainbow(self):
        self.lightMode = 'rainbow'
        self.resume()

    def rainbow_processing(self):
        while self.lightMode == 'rainbow':
            for j in range(256):
                if self.lightMode != 'rainbow':
                    break
                for i in range(self.LED_COUNT):
                    pixel_index = (i * 256 // self.LED_COUNT) + j
                    self.strip.setPixelColor(i, self.wheel(pixel_index & 255))
                self.strip.show()
                time.sleep(0.02)
        self.pause()

    def wheel(self, pos):
        """Generate rainbow colors across 0-255 positions."""
        if pos < 85:
            return rpi_ws281x.Color(pos * 3, 255 - pos * 3, 0)
        elif pos < 170:
            pos -= 85
            return rpi_ws281x.Color(255 - pos * 3, 0, pos * 3)
        else:
            pos -= 170
            return rpi_ws281x.Color(0, pos * 3, 255 - pos * 3)

    def firefly(self):
        self.lightMode = 'firefly'
        self.resume()

    def firefly_processing(self):
        # Adjustable settings
        MAX_BRIGHTNESS = 128  # Maximum brightness (0-255), limited to 50% of LED capabilities
        MIN_BRIGHTNESS = 10  # Minimum brightness for LEDs
        FADE_STEP = 5  # Brightness change step for gradual fade
        FADE_INTERVAL = 0.05  # Time interval between brightness changes during fade (in seconds)
        ON_TIME_MIN = 0.5  # Minimum duration for LED to stay at max brightness (in seconds)
        ON_TIME_MAX = 2.0  # Maximum duration for LED to stay at max brightness (in seconds)
        CHAOTIC_BLINK_PROBABILITY = 0.1  # Probability (0-1) that an LED will perform a chaotic blink
        CHAOTIC_BRIGHTNESS_INCREASE_MIN = 0.1  # Minimum percentage increase for chaotic blink
        CHAOTIC_BRIGHTNESS_INCREASE_MAX = 0.3  # Maximum percentage increase for chaotic blink
        CHAOTIC_BLINK_DURATION_MIN = 0.1  # Minimum duration of chaotic blink (in seconds)
        CHAOTIC_BLINK_DURATION_MAX = 0.6  # Maximum duration of chaotic blink (in seconds)

        # Initialize per-LED states
        leds = []
        for i in range(self.LED_COUNT):
            # Schedule random initial delay for each LED
            next_change_time = time.time() + random.uniform(0, 2)
            leds.append({
                'state': 'rising',  # 'rising' or 'falling'
                'brightness': MIN_BRIGHTNESS,
                'next_change_time': next_change_time,
                'on_duration': random.uniform(ON_TIME_MIN, ON_TIME_MAX)
            })

        while self.lightMode == 'firefly':
            current_time = time.time()
            for i in range(self.LED_COUNT):
                led = leds[i]
                if current_time >= led['next_change_time']:
                    if led['state'] == 'rising':
                        # Increase brightness gradually
                        led['brightness'] += FADE_STEP
                        if led['brightness'] >= MAX_BRIGHTNESS:
                            led['brightness'] = MAX_BRIGHTNESS
                            led['state'] = 'falling'
                            # Schedule time to start decreasing brightness
                            led['next_change_time'] = current_time + led['on_duration']
                        else:
                            # Continue rising
                            led['next_change_time'] = current_time + FADE_INTERVAL
                    elif led['state'] == 'falling':
                        # Decrease brightness gradually
                        led['brightness'] -= FADE_STEP
                        if led['brightness'] <= MIN_BRIGHTNESS:
                            led['brightness'] = MIN_BRIGHTNESS
                            led['state'] = 'rising'
                            # Schedule next rise after a random delay
                            led['next_change_time'] = current_time + random.uniform(ON_TIME_MIN, ON_TIME_MAX)
                            led['on_duration'] = random.uniform(ON_TIME_MIN, ON_TIME_MAX)
                        else:
                            # Continue falling
                            led['next_change_time'] = current_time + FADE_INTERVAL

                    # Set LED color based on current brightness
                    brightness = int(led['brightness'])
                    self.strip.setPixelColor(i, rpi_ws281x.Color(brightness, brightness, brightness))

                    # Handle chaotic blink
                    if random.random() < CHAOTIC_BLINK_PROBABILITY:
                        # Apply chaotic blink
                        original_brightness = brightness
                        blink_increase = original_brightness * random.uniform(
                            CHAOTIC_BRIGHTNESS_INCREASE_MIN,
                            CHAOTIC_BRIGHTNESS_INCREASE_MAX
                        )
                        blink_brightness = min(int(original_brightness + blink_increase), MAX_BRIGHTNESS)
                        blink_duration = random.uniform(CHAOTIC_BLINK_DURATION_MIN, CHAOTIC_BLINK_DURATION_MAX)

                        # Temporarily set increased brightness
                        self.strip.setPixelColor(i,
                                                 rpi_ws281x.Color(blink_brightness, blink_brightness, blink_brightness))
                        self.strip.show()
                        time.sleep(blink_duration)

                        # Revert to original brightness
                        self.strip.setPixelColor(i, rpi_ws281x.Color(original_brightness, original_brightness,
                                                                     original_brightness))

                else:
                    # Handle chaotic blink even if not time to change state
                    if random.random() < CHAOTIC_BLINK_PROBABILITY:
                        brightness = int(led['brightness'])
                        blink_increase = brightness * random.uniform(
                            CHAOTIC_BRIGHTNESS_INCREASE_MIN,
                            CHAOTIC_BRIGHTNESS_INCREASE_MAX
                        )
                        blink_brightness = min(int(brightness + blink_increase), MAX_BRIGHTNESS)
                        blink_duration = random.uniform(CHAOTIC_BLINK_DURATION_MIN, CHAOTIC_BLINK_DURATION_MAX)

                        # Temporarily set increased brightness
                        self.strip.setPixelColor(i,
                                                 rpi_ws281x.Color(blink_brightness, blink_brightness, blink_brightness))
                        self.strip.show()
                        time.sleep(blink_duration)

                        # Revert to original brightness
                        self.strip.setPixelColor(i, rpi_ws281x.Color(brightness, brightness, brightness))

            self.strip.show()
            time.sleep(0.02)  # Sleep briefly to allow smooth updates
        self.pause()


    # def frontLight(self, switch):
    #     if switch == 'on':
    #         GPIO.output(6, GPIO.HIGH)
    #         GPIO.output(13, GPIO.HIGH)
    #     elif switch == 'off':
    #         GPIO.output(5,GPIO.LOW)
    #         GPIO.output(13,GPIO.LOW)


    # def switch(self, port, status):
    #     if port == 1:
    #         if status == 1:
    #             GPIO.output(5, GPIO.HIGH)
    #         elif status == 0:
    #             GPIO.output(5,GPIO.LOW)
    #         else:
    #             pass
    #     elif port == 2:
    #         if status == 1:
    #             GPIO.output(6, GPIO.HIGH)
    #         elif status == 0:
    #             GPIO.output(6,GPIO.LOW)
    #         else:
    #             pass
    #     elif port == 3:
    #         if status == 1:
    #             GPIO.output(13, GPIO.HIGH)
    #         elif status == 0:
    #             GPIO.output(13,GPIO.LOW)
    #         else:
    #             pass
    #     else:
    #         logger.info('Wrong Command: Example--switch(3, 1)->to switch on port3')


    # def set_all_switch_off(self):
    #     self.switch(1,0)
    #     self.switch(2,0)
    #     self.switch(3,0)


    # def headLight(self, switch):
    #     if switch == 'on':
    #         GPIO.output(5, GPIO.HIGH)
    #     elif switch == 'off':
    #         GPIO.output(5,GPIO.LOW)


    def light_change(self):
        if self.lightMode == 'none':
            self.pause()
        elif self.lightMode == 'police':
            self.police_processing()
        elif self.lightMode == 'breath':
            self.breath_processing()
        elif self.lightMode == 'rainbow':
            self.rainbow_processing()
        elif self.lightMode == 'firefly':
            self.firefly_processing()


    def run(self):
        while 1:
            self.__flag.wait()
            self.light_change()
            pass
