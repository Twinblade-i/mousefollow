# MouseFollow

A simple script that displays a laser pointer on the screen based on the mouse cursor position.

- forked from: https://github.com/doakey3/impress_mousefollow

## changes

- Add a feature to adjust the size of the pointer within the dialog box.
- Add a feature to allow it running in the background.
- Adjust the direction of `settings.ini` to `~/.config/mousefollow/settings.ini` .

## Build

1. Create python venv environment: `python -m venv venv`
2. Install essential packages: `pip install -r requirements.txt`
3.  Run the Python file directly or use PyInstaller to package it into an executable file.
   - run directly: `python3 MouseFollow.py`
   - package: `pyinstaller MouseFollow.spec`/`pyinstaller --onefile --windowed MouseFollow.py`

## Usage

- Set the monitor dropdown option to the audience-view monitor.
- Press "F9", then click and drag to draw a box around the preview area, or press "Esc" to cancel.
- Press "R Alt" to display laser pointer, and press "R Alt" again to hide.
- The laser pointer size can be adjusted within the dialog box, with a precision of 0.1 and a range 0.5 ~ 5.
- It can be minimized to sidebar and continue running in the background. Or use the "Exit" button to stop running.
- A customized pointer icon can be achieved by placing an `.ico` or `.png` file in the directory where the program or Python script is located. Recommended size is 46×46 pixels.