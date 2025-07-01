#!/usr/bin/python3
from signal import pause
from threading import Timer
from gpiozero import Button, MotionSensor
import os
import subprocess
import logging

# ─── Setup Logging ───────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# ─── GPIO Pin Configuration ──────────────────────────────────────────────────
BUTTON_PIN = 3   # Pin for the shutdown/reboot button
PIR = MotionSensor(4)  # Motion sensor for detecting movement
SCREEN_ON_PINS = [5, 6, 7, 8]  # Pins for buttons that immediately turn the screen on

# ─── Global Variables ───────────────────────────────────────────────────────
_off_timer: Timer | None = None  # Timer for managing screen off delay
_inactivity_timer: Timer | None = None  # Timer for inactivity (2 minutes)

# ─── Action Functions ────────────────────────────────────────────────────────

def screen_off():
    """
    Turns off the screen by using xset DPMS command.
    """
    logging.info("Screen turned off due to inactivity.")
    subprocess.run(
        ['xset', 'dpms', 'force', 'off'],
        env={**os.environ, 'DISPLAY': ':0'}
    )

def screen_on():
    """
    Turns on the screen by using xset DPMS command.
    """
    logging.info("Screen turned on.")
    subprocess.run(
        ['xset', 'dpms', 'force', 'on'],
        env={**os.environ, 'DISPLAY': ':0'}
    )

def reboot():
    """
    Initiates a system reboot.
    """
    logging.warning("Reboot triggered by double press.")
    subprocess.run(['sudo', 'reboot'])

def shutdown():
    """
    Initiates a system shutdown.
    """
    logging.warning("Shutdown triggered by long press.")
    subprocess.run(['sudo', 'shutdown', 'now'])

def reset_inactivity_timer():
    """
    Resets the inactivity timer and starts it again.
    This function is called whenever there is an action (button press or motion detected).
    """
    global _inactivity_timer

    # Wenn der Timer bereits läuft, abbrechen und neu starten
    if _inactivity_timer and _inactivity_timer.is_alive():
        _inactivity_timer.cancel()

    # Starte den Timer für die Inaktivität (2 Minuten)
    logging.info("Inactivity timer reset → Screen will turn off in 2 minutes if no activity.")
    _inactivity_timer = Timer(120.0, screen_off)  # 120 Sekunden (2 Minuten) Inaktivität
    _inactivity_timer.start()

# ─── Button Press Handler ────────────────────────────────────────────────────

def pressed():
    """
    Handles button press events for initiating screen off or reboot.
    - Single press schedules screen off after a 2-second delay.
    - Double press triggers a reboot immediately.
    """
    global _off_timer

    # Wenn ein Timer für einen einzelnen Tastendruck läuft, handelt es sich um einen Doppeldruck
    if _off_timer and _off_timer.is_alive():
        _off_timer.cancel()
        _off_timer = None
        reboot()
        return

    # Ansonsten plane, den Bildschirm in 2 Sekunden auszuschalten
    logging.info("First press detected → scheduling screen off in 2 seconds.")
    _off_timer = Timer(2.0, screen_off)
    _off_timer.start()

    # Zurücksetzen des Inaktivität-Timers
    reset_inactivity_timer()

# ─── GPIO Setup ──────────────────────────────────────────────────────────────

# Configure button for shutdown/reboot
button3 = Button(BUTTON_PIN, bounce_time=0.05, hold_time=1.0, hold_repeat=False)
button3.when_pressed = pressed
button3.when_held = shutdown

# Motion sensor triggers screen on when movement is detected
PIR.when_motion = screen_on

# Configure screen-on buttons that immediately turn the screen on
for pin in SCREEN_ON_PINS:
    btn = Button(pin, bounce_time=0.05)
    btn.when_pressed = screen_on

# Reset the inactivity timer whenever motion is detected
PIR.when_motion = lambda: [screen_on(), reset_inactivity_timer()]

# ─── Main Event Loop ─────────────────────────────────────────────────────────
# This keeps the script running, waiting for events (button presses or motion)
pause()
