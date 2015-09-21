# ducky-scripts

Scripts I've written for the rubberducky.

For now the only script is `bootstrap_raspberry.py`, which enables headless initialization of Raspberry Pis. This makes the Raspberry forward local ssh through a ssh tunnel to an existing host that you can use to drop right into fun mode, without needing a keyboard or monitor for configuration.Automatically expands the root partition for you. Note: The Raspberry will re-boot when it's done expanding the partition, at this time the Rubber Ducky will shutdown for a little moment (the light will turn off), pull it out now to not spiral into a reboot loop. The RPi will appear on your ssh target host at port 2223. Only tested with raspbian.
