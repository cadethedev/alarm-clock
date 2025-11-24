#!/usr/bin/env python3
"""
Test script that replicates the alarm sunrise animation
Press button to start/stop the animation
"""
import time
from rpi_ws281x import PixelStrip, Color
import RPi.GPIO as GPIO

# LED strip configuration
LED_COUNT = 30
LED_PIN = 18        # GPIO 18 (Pin 12)
LED_FREQ_HZ = 800000
LED_DMA = 10
LED_BRIGHTNESS = 255
LED_INVERT = False
LED_CHANNEL = 0

# Button configuration
BUTTON_PIN = 12     # GPIO 12 (Pin 32)

# Setup GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Create LED strip
strip = PixelStrip(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
strip.begin()

def clear_leds():
    """Turn all LEDs off"""
    for i in range(strip.numPixels()):
        strip.setPixelColor(i, Color(0, 0, 0))
    strip.show()

def sunrise_animation():
    """20-minute sunrise animation: 15min dark orange → 5min ramp to warm light"""
    print("🌅 Starting sunrise animation...")

    # 20 minutes = 1200 seconds
    duration = 1200
    steps = 200
    delay = duration / steps

    for step in range(steps):
        # Check for button press to stop
        if GPIO.input(BUTTON_PIN) == GPIO.LOW:
            print("Animation stopped by button")
            clear_leds()
            time.sleep(0.5)  # Debounce
            return

        # Progress from 0 to 1
        progress = step / steps

        if progress < 0.75:
            # First 15 minutes: Very dim dark orange (constant)
            # Previous value: int(20 * 0.1) = 2 - good starting point
            r = int(30 * 0.1)  # Slightly brighter orange
            g = int(8 * 0.1)
            b = 0
        else:
            # Last 5 minutes: Smooth ramp to warm light at 40% brightness
            ramp_progress = (progress - 0.75) / 0.25
            # Target: warm white at 40% (254, 255, 236 at 40%)
            # Previous starting value: (2, 0, 0) - good dim start
            r = int(3 + (254 * 0.4 - 3) * ramp_progress)
            g = int(0 + (255 * 0.4 - 0) * ramp_progress)
            b = int(0 + (236 * 0.4) * ramp_progress)

        # Set all LEDs to current color
        for i in range(LED_COUNT):
            strip.setPixelColor(i, Color(r, g, b))
        strip.show()

        # Show progress every minute
        if step % 10 == 0:
            minutes = (step / steps) * 20
            print(f"Progress: {minutes:.1f} minutes / 20 minutes")

        time.sleep(delay)

    # Hold final warm light at 40%
    for i in range(LED_COUNT):
        strip.setPixelColor(i, Color(int(254*0.4), int(255*0.4), int(236*0.4)))
    strip.show()

    print("Sunrise complete!")

try:
    print("Press button to start sunrise animation (20 minutes)")
    print("Press button again during animation to stop")
    print("Ctrl+C to exit")
    clear_leds()

    while True:
        if GPIO.input(BUTTON_PIN) == GPIO.LOW:  # Button pressed
            print("Button pressed - starting animation...")
            time.sleep(0.3)  # Debounce
            sunrise_animation()
            clear_leds()
            print("Ready for next test. Press button to start again.")
        time.sleep(0.1)

except KeyboardInterrupt:
    print("\nExiting...")
finally:
    clear_leds()
    GPIO.cleanup()
