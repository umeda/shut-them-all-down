### Shutdown Setup Instructions (Running at Boot with *systemd*)
These instruction provided by Gemini.

<div>

*systemd* is the init system used by modern Raspberry Pi OS. It\'s
robust and the recommended way to run background services.

Step 1: Save the Python Script

1.  Open a terminal on your Raspberry Pi.

2.  Create a directory for your script:

    Bash

    *mkdir -p \~/scripts*

3.  Open a new file using *nano* (or your preferred editor):

    Bash

    *nano \~/scripts/shutdown_button.py*

4.  Paste the Python code provided above into the file.

5.  Save and exit *nano* (Ctrl+X, Y, Enter).

Step 2: Make the Script Executable

Bash

*chmod +x \~/scripts/shutdown_button.py*

Step 3: Test the Script (Optional but Recommended)

Run the script manually to ensure it works as expected:

Bash

*python3 \~/scripts/shutdown_button.py*

-   The green LED should turn on.
-   Press your button. The blue LED should turn on, and you should see
    \"Shutdown scheduled\...\" in the terminal.
-   Within 5 seconds, press the button again. The green LED should
    return, and you should see \"Shutdown aborted!\".
-   If you let the 5 seconds pass after the first press, the red LED
    should turn on, and your Pi should begin shutting down.

**Step 4: Create a *****systemd***** Service File**

This file tells *systemd* how to run your script.

1.  Open a new service file for editing:

    Bash

    *sudo nano /etc/systemd/system/shutdown_button.service*

2.  Paste the following content into the file:

    Ini, TOML

    *\[Unit\]*

    *Description=Raspberry Pi Shutdown Button Service*

    *After=network.target*

    *\[Service\]*

    *ExecStart=/usr/bin/python3 /home/pi/scripts/shutdown_button.py*

    *Restart=always*

    *User=pi*

    *Group=pi*

    *WorkingDirectory=/home/pi/scripts/*

    *StandardOutput=journal*

    *StandardError=journal*

    *\[Install\]*

    *WantedBy=multi-user.target*

    Explanation of the Service File:

    -   *\[Unit\]*

        -   *Description*: A human-readable description.
        -   *After=network.target*: Ensures this service starts after
            the network is up (though not strictly necessary for this
            script, it\'s good practice for network-dependent services).

    -   *\[Service\]*

        -   *ExecStart*: The command to execute when the service starts.
            **Important:** Use the full path to *python3*
            (*/usr/bin/python3*) and your script
            (*/home/pi/scripts/shutdown_button.py*).
        -   *Restart=always*: If the script crashes for any reason,
            *systemd* will try to restart it.
        -   *User=pi* and *Group=pi*: Runs the script as the *pi* user,
            which is generally safer than *root* for user scripts.
            *Note: GPIO access usually requires the *pi* user to be in
            the *gpio* group, which it typically is by default on
            Raspberry Pi OS.*
        -   *WorkingDirectory*: Sets the working directory for the
            script.
        -   *StandardOutput=journal* and *StandardError=journal*:
            Redirects standard output and error to the *systemd*
            journal, so you can easily view logs later using
            *journalctl*.

    -   *\[Install\]*

        -   *WantedBy=multi-user.target*: Ensures the service starts
            when the system enters the multi-user runlevel (normal
            boot).

3.  Save and exit *nano* (Ctrl+X, Y, Enter).

Step 5: Enable and Start the Service

1.  Reload *systemd* to recognize the new service file:

    Bash

    *sudo systemctl daemon-reload*

2.  Enable the service to start automatically at boot:

    Bash

    *sudo systemctl enable shutdown_button.service*

3.  Start the service immediately (without rebooting):

    Bash

    *sudo systemctl start shutdown_button.service*

Step 6: Check Service Status and Logs

-   To check if the service is running:

    Bash

    *sudo systemctl status shutdown_button.service*

    You should see \"Active: active (running)\".

-   To view the logs from your script (helpful for debugging):

    Bash

    *journalctl -u shutdown_button.service -f*

    Press Ctrl+C to exit *journalctl*.

Step 7: Reboot and Test

Reboot your Raspberry Pi:

Bash

*sudo reboot*

After rebooting, the green LED should turn on automatically. Then, test
the button press, abort, and final shutdown functionality.

This setup will ensure your script runs reliably in the background from
the moment your Raspberry Pi boots up, providing a safe and
user-friendly shutdown mechanism.

</div>
