'''
Copyright 2025 Nezumi Workbench

Permission is hereby granted, free of charge, to any person obtaining a copy 
of this software and associated documentation files (the “Software”), to deal 
in the Software without restriction, including without limitation the rights 
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell 
copies of the Software, and to permit persons to whom the Software is 
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all 
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR 
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, 
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE 
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER 
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, 
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE 
SOFTWARE.
'''
import RPi.GPIO as GPIO
import time
import subprocess
import os
import threading # For managing the countdown in a separate thread

# --- GPIO Pin Definitions ---
RED_LED_PIN = 23
GREEN_LED_PIN = 24  # Changed from 25
BLUE_LED_PIN = 25   # Changed from 24
BUTTON_PIN = 26

# --- Shutdown Configuration ---
SHUTDOWN_INTERNAL_DELAY_SECONDS = 10 # Changed from 5 to 10 seconds
FINAL_SHUTDOWN_COMMAND = "sudo shutdown -h now" # This will execute after our delay

# --- Global variables for state management ---
shutdown_scheduled = False
shutdown_abort_event = threading.Event() # Event to signal abort to the countdown thread
countdown_thread = None # To hold the countdown thread object

def setup_gpio():
    GPIO.setmode(GPIO.BCM) # Use Broadcom pin-numbering scheme
    GPIO.setwarnings(False) # Disable warnings for cleaner output

    # Set up LED pins as outputs and ensure they are off initially
    GPIO.setup(RED_LED_PIN, GPIO.OUT)
    GPIO.setup(BLUE_LED_PIN, GPIO.OUT)
    GPIO.setup(GREEN_LED_PIN, GPIO.OUT)
    all_leds_off()

    # Set up button pin as input with internal pull-up resistor
    # Button is active low: PUD_UP ensures it reads HIGH when not pressed, LOW when pressed.
    GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP) # Changed PUD_DOWN to PUD_UP

def all_leds_off():
    GPIO.output(RED_LED_PIN, GPIO.LOW)
    GPIO.output(BLUE_LED_PIN, GPIO.LOW)
    GPIO.output(GREEN_LED_PIN, GPIO.LOW)

def set_led(color):
    all_leds_off()
    if color == "green":
        GPIO.output(GREEN_LED_PIN, GPIO.HIGH)
    elif color == "blue":
        GPIO.output(BLUE_LED_PIN, GPIO.HIGH)
    elif color == "red":
        GPIO.output(RED_LED_PIN, GPIO.HIGH)

def execute_shutdown():
    """
    Function to actually execute the shutdown command.
    """
    print("Executing final shutdown command...")
    set_led("red") # Indicate imminent shutdown
    try:
        # We need to run this in a way that doesn't block and detaches
        # from our script, so it can complete the shutdown.
        os.system(FINAL_SHUTDOWN_COMMAND)
    except Exception as e:
        print(f"Error executing final shutdown: {e}")
        # If shutdown fails, revert to green and reset state
        set_led("green")
        global shutdown_scheduled
        shutdown_scheduled = False

def countdown_and_shutdown():
    """
    Manages the 10-second countdown and triggers shutdown.
    Runs in a separate thread.
    """
    global shutdown_scheduled

    set_led("blue") # Blue LED for countdown
    print(f"Shutdown countdown started for {SHUTDOWN_INTERNAL_DELAY_SECONDS} seconds...")

    # Wait for the delay or until an abort event is set
    aborted = shutdown_abort_event.wait(timeout=SHUTDOWN_INTERNAL_DELAY_SECONDS)

    if not aborted:
        print("Countdown finished. Initiating system shutdown.")
        execute_shutdown()
    else:
        print("Shutdown countdown aborted.")
        # The main thread will handle resetting shutdown_scheduled and LED to green
        # in the button_callback after the abort event is set.
        pass # The button_callback already handled the state reset

def button_callback(channel):
    global shutdown_scheduled
    global countdown_thread

    # Debounce the button press
    time.sleep(0.05) # Small debounce time

    # Logic change: Check for GPIO.LOW for active-low button press
    if GPIO.input(BUTTON_PIN) == GPIO.LOW:
        print("Button pressed!")
        if not shutdown_scheduled:
            # First press: Initiate countdown
            shutdown_scheduled = True
            shutdown_abort_event.clear() # Clear any previous abort signal
            countdown_thread = threading.Thread(target=countdown_and_shutdown)
            countdown_thread.start()
        else:
            # Second press: Abort shutdown
            print("Shutdown aborted!")
            shutdown_abort_event.set() # Signal the countdown thread to abort
            set_led("green") # Return to green LED
            shutdown_scheduled = False # Reset state
            if countdown_thread and countdown_thread.is_alive():
                # Give a moment for the thread to recognize the abort signal
                countdown_thread.join(timeout=1) # Wait for it to finish gracefully
                if countdown_thread.is_alive():
                    print("Warning: Countdown thread did not terminate quickly after abort.")


def main():
    setup_gpio()
    set_led("green") # Indicate the system is on and ready

    # Add event detection for the button
    # Changed from GPIO.RISING to GPIO.FALLING for active-low button
    GPIO.add_event_detect(BUTTON_PIN, GPIO.FALLING, callback=button_callback, bouncetime=200)

    print("Shutdown button script running. Green LED is on.")
    print(f"Press the button to schedule shutdown in {SHUTDOWN_INTERNAL_DELAY_SECONDS} seconds.")
    print("Press again during the blue LED display to abort.")

    try:
        # Keep the script running indefinitely
        while True:
            # The actual shutdown will be handled by the countdown_thread.
            # This main loop just keeps the script alive for event detection.
            # We can add a check here if shutdown has fully completed to exit.
            if shutdown_scheduled and not countdown_thread.is_alive() and GPIO.input(RED_LED_PIN) == GPIO.HIGH:
                 print("System is going down. Exiting script.")
                 break
            time.sleep(1) # Keep main loop alive, check every second
    except KeyboardInterrupt:
        print("\nScript terminated by user.")
    finally:
        # Ensure any active countdown thread is signaled to abort if the script is killed manually
        if shutdown_scheduled:
            shutdown_abort_event.set()
            if countdown_thread and countdown_thread.is_alive():
                countdown_thread.join(timeout=2) # Give it a moment to clean up

        all_leds_off()
        GPIO.cleanup() # Clean up GPIO settings on exit
        print("GPIO cleaned up.")

if __name__ == "__main__":
    main()
