from rpi_ws281x import Adafruit_NeoPixel, Color
import rpi_ws281x

print("rpi_ws281x version:", rpi_ws281x.__version__)

LED_COUNT = 16  # Number of LED pixels
LED_PIN = 12    # GPIO pin connected to the pixels (must support PWM)

strip = Adafruit_NeoPixel(LED_COUNT, LED_PIN)
strip.begin()
for i in range(strip.numPixels()):
    strip.setPixelColor(i, Color(255, 0, 0))  # Red color
strip.show()
