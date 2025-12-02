#!/usr/bin/env python3
"""
Unified Sunrise Alarm Clock System
Combines alarm checking, button handling, and setup into one process
to eliminate GPIO conflicts.
"""

import time
import json
import os
from datetime import datetime
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

# Settings
ALARM_FILE = '/home/cade/alarm_settings.json'
SHORT_PRESS_TIME = 1.0   # 1 second to enter setup
DISABLE_PRESS_TIME = 5.0 # 5 seconds to disable alarm

# State machine states
STATE_IDLE = "idle"
STATE_BUTTON_HELD = "button_held"
STATE_SETUP = "setup"
STATE_ALARM = "alarm"

# Setup GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Create LED strip
strip = PixelStrip(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
strip.begin()

# Global state
current_state = STATE_IDLE
alarm_active = False

def clear_leds():
    """Turn all LEDs off"""
    for i in range(strip.numPixels()):
        strip.setPixelColor(i, Color(0, 0, 0))
    strip.show()


def load_alarm():
    """Load alarm settings from file"""
    try:
        if os.path.exists(ALARM_FILE):
            with open(ALARM_FILE, 'r') as f:
                return json.load(f)
    except:
        pass
    return {'enabled': False, 'time': None}

def save_alarm(hour, minute):
    """Save alarm to file"""
    alarm_time = f"{hour:02d}:{minute:02d} AM"
    settings = {'enabled': True, 'time': alarm_time}
    with open(ALARM_FILE, 'w') as f:
        json.dump(settings, f)
    print(f"✓ Alarm saved: {alarm_time}")

def disable_alarm():
    """Disable the alarm (keeps the time saved)"""
    settings = load_alarm()
    settings['enabled'] = False
    with open(ALARM_FILE, 'w') as f:
        json.dump(settings, f)
    print("✓ Alarm DISABLED")

    # Flash red to indicate disabled (153, 0, 0 at 10% brightness)
    for _ in range(3):
        for i in range(LED_COUNT):
            strip.setPixelColor(i, Color(int(153*0.1), 0, 0))
        strip.show()
        time.sleep(0.15)
        clear_leds()
        time.sleep(0.15)

def sunrise_animation():
    """20-minute sunrise animation: 15 min (1→8 red), 5 min (rest of sequence)"""
    global alarm_active
    alarm_active = True

    print("Starting sunrise animation...")

    # Phase 1: 15 minutes - RGB(1, 0, 0) → RGB(8, 0, 0)
    phase1_duration = 900  # 15 minutes in seconds
    phase1_steps = 150
    phase1_delay = phase1_duration / phase1_steps

    for step in range(phase1_steps):
        if not alarm_active:
            print("Alarm stopped by button")
            return

        # Progress from 0 to 1 for phase 1
        progress = step / phase1_steps

        # Red ramps from 1 to 8
        r = int(1 + (7 * progress))

        # Set all LEDs to current color
        for i in range(LED_COUNT):
            strip.setPixelColor(i, Color(r, 0, 0))
        strip.show()

        time.sleep(phase1_delay)

    # Phase 2: 5 minutes - Complete the rest of the light sequence
    # RGB(8, 0, 0) → RGB(50, 15, 6)
    phase2_duration = 300  # 5 minutes in seconds
    phase2_steps = 50
    phase2_delay = phase2_duration / phase2_steps

    for step in range(phase2_steps):
        if not alarm_active:
            print("Alarm stopped by button")
            return

        # Progress from 0 to 1 for phase 2
        progress = step / phase2_steps

        # Ramp from RGB(8, 0, 0) to RGB(50, 15, 6)
        r = int(8 + (50 - 8) * progress)
        g = int(0 + (15 - 0) * progress)
        b = int(0 + (6 - 0) * progress)

        # Set all LEDs to current color
        for i in range(LED_COUNT):
            strip.setPixelColor(i, Color(r, g, b))
        strip.show()

        time.sleep(phase2_delay)

    # Hold final color: RGB(50, 15, 6)
    for i in range(LED_COUNT):
        strip.setPixelColor(i, Color(50, 15, 6))
    strip.show()

    alarm_active = False
    print("Sunrise complete")

def show_hour(hour):
    """Show hour by lighting up LEDs from start (1-12)"""
    clear_leds()
    # White (254, 255, 236 at 10% brightness)
    for i in range(hour):
        strip.setPixelColor(i, Color(int(254*0.1), int(255*0.1), int(236*0.1)))
    strip.show()

def show_minute(minute):
    """Show minute on LED strip (each LED = 5 minutes)"""
    clear_leds()
    led_count = minute // 5
    # White (254, 255, 236 at 10% brightness)
    for i in range(led_count):
        strip.setPixelColor(i, Color(int(254*0.1), int(255*0.1), int(236*0.1)))
    strip.show()

def flash_confirm():
    """Flash LEDs to confirm action"""
    # Green (3, 160, 87 at 10% brightness)
    for _ in range(2):
        for i in range(LED_COUNT):
            strip.setPixelColor(i, Color(int(3*0.1), int(160*0.1), int(87*0.1)))
        strip.show()
        time.sleep(0.1)
        clear_leds()
        time.sleep(0.1)

def select_hour():
    """Let user select hour using button"""
    # Load current alarm time if set
    settings = load_alarm()
    hour = 7  # Default
    if settings.get('time'):
        try:
            parts = settings['time'].replace(' AM', '').split(':')
            hour = int(parts[0])
        except:
            pass

    show_hour(hour)
    print("SELECT HOUR: Short press = cycle, Long press = confirm")

    while True:
        # Wait for button press
        while GPIO.input(BUTTON_PIN) == GPIO.HIGH:
            time.sleep(0.01)

        press_start = time.time()

        # Wait for release
        while GPIO.input(BUTTON_PIN) == GPIO.LOW:
            if time.time() - press_start > SHORT_PRESS_TIME:
                # Long press - confirm
                flash_confirm()
                while GPIO.input(BUTTON_PIN) == GPIO.LOW:
                    time.sleep(0.01)
                time.sleep(0.2)
                print(f"Hour confirmed: {hour}")
                return hour
            time.sleep(0.01)

        # Short press - cycle
        hour = (hour % 12) + 1
        show_hour(hour)
        print(f"Hour: {hour}")
        time.sleep(0.2)

def select_minute():
    """Let user select minute using button"""
    # Load current alarm time if set, round down to nearest 5
    settings = load_alarm()
    minute = 0  # Default
    if settings.get('time'):
        try:
            parts = settings['time'].replace(' AM', '').split(':')
            exact_minute = int(parts[1])
            # Round down to nearest 5
            minute = (exact_minute // 5) * 5
        except:
            pass

    show_minute(minute)
    print("SELECT MINUTE: Short press = +5 min, Long press = confirm")

    while True:
        # Wait for button press
        while GPIO.input(BUTTON_PIN) == GPIO.HIGH:
            time.sleep(0.01)

        press_start = time.time()

        # Wait for release
        while GPIO.input(BUTTON_PIN) == GPIO.LOW:
            if time.time() - press_start > SHORT_PRESS_TIME:
                # Long press - confirm
                flash_confirm()
                while GPIO.input(BUTTON_PIN) == GPIO.LOW:
                    time.sleep(0.01)
                time.sleep(0.2)
                print(f"Minute confirmed: {minute}")
                return minute
            time.sleep(0.01)

        # Short press - add 5 minutes
        minute = (minute + 5) % 60
        show_minute(minute)
        print(f"Minute: {minute}")
        time.sleep(0.2)

def setup_alarm():
    """Run alarm setup mode"""
    global current_state
    current_state = STATE_SETUP

    print("=== ALARM SETUP MODE ===")
    hour = select_hour()
    time.sleep(0.5)
    minute = select_minute()
    time.sleep(0.5)

    save_alarm(hour, minute)
    flash_confirm()
    clear_leds()

    current_state = STATE_IDLE
    print("Setup complete, returning to idle")

def check_alarm():
    """Check if alarm should trigger (20 minutes before set time)"""
    settings = load_alarm()

    if not settings['enabled'] or not settings['time']:
        return False

    alarm_time = settings['time']
    now = datetime.now()

    # Parse alarm time
    try:
        alarm_hour, alarm_minute = alarm_time.replace(' AM', '').split(':')
        alarm_hour = int(alarm_hour)
        alarm_minute = int(alarm_minute)

        # Calculate 20 minutes before alarm time
        trigger_minute = alarm_minute - 20
        trigger_hour = alarm_hour

        if trigger_minute < 0:
            trigger_minute += 60
            trigger_hour -= 1
            if trigger_hour < 1:
                trigger_hour = 12

        # Get current hour and minute
        current_hour = now.hour
        if current_hour == 0:
            current_hour = 12
        elif current_hour > 12:
            current_hour -= 12
        current_minute = now.minute

        # Check if current time matches trigger time (only check AM hours)
        if now.hour < 12:  # AM only
            return current_hour == trigger_hour and current_minute == trigger_minute
        return False
    except:
        return False

def handle_idle_button():
    """Handle button press when idle - Apple style interface"""
    global current_state

    if GPIO.input(BUTTON_PIN) == GPIO.LOW:
        # Button pressed - show white immediately (254, 255, 236 at 10% brightness)
        for i in range(LED_COUNT):
            strip.setPixelColor(i, Color(int(254*0.1), int(255*0.1), int(236*0.1)))
        strip.show()
        current_state = STATE_BUTTON_HELD

        press_start = time.time()

        while GPIO.input(BUTTON_PIN) == GPIO.LOW:
            press_duration = time.time() - press_start

            if press_duration >= DISABLE_PRESS_TIME:
                # Held for 5 seconds - disable alarm
                disable_alarm()
                while GPIO.input(BUTTON_PIN) == GPIO.LOW:
                    time.sleep(0.01)
                clear_leds()
                current_state = STATE_IDLE
                return

            time.sleep(0.01)

        # Button released - any press goes to setup
        clear_leds()
        setup_alarm()

def handle_alarm_button():
    """Handle button during alarm - any press stops"""
    global alarm_active

    if GPIO.input(BUTTON_PIN) == GPIO.LOW:
        print("Button pressed - stopping alarm")
        alarm_active = False
        clear_leds()
        time.sleep(0.5)  # Debounce
        while GPIO.input(BUTTON_PIN) == GPIO.LOW:
            time.sleep(0.01)

def main():
    global current_state, alarm_active

    print("🌅 Unified Alarm System Started")
    print(f"Button: GPIO {BUTTON_PIN}")
    print(f"LEDs: {LED_COUNT} on GPIO {LED_PIN}")
    print()

    try:
        while True:
            if current_state == STATE_IDLE:
                # Check for alarm trigger
                if check_alarm() and not alarm_active:
                    print("⏰ ALARM TRIGGERED!")
                    current_state = STATE_ALARM
                    sunrise_animation()
                    # Don't clear LEDs - keep them on until button pressed
                    # Wait for button press to turn off
                    while current_state == STATE_ALARM:
                        handle_alarm_button()
                        if not alarm_active:
                            clear_leds()
                            current_state = STATE_IDLE
                            break
                        time.sleep(0.05)
                    continue

                # Handle button press (setup or disable)
                handle_idle_button()

            elif current_state == STATE_ALARM:
                # Handle button during alarm
                handle_alarm_button()
                if not alarm_active:
                    clear_leds()
                    current_state = STATE_IDLE

            time.sleep(0.05)

    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        clear_leds()
        GPIO.cleanup()

if __name__ == '__main__':
    main()
