from setuptools import setup

APP = ['app_ui.py']
DATA_FILES = []  # You can add static assets here if needed
OPTIONS = {
    'argv_emulation': True,
    'packages': ['customtkinter', 'emoji', 'ollama'],
    'includes': ['tkinter'],
    'semi_standalone': False,  # Make sure this is False
    'plist': {
        'CFBundleName': 'GainzBot',
        'CFBundleDisplayName': 'GainzBot',
        'CFBundleIdentifier': 'com.ifryed.gainzbot',
        'CFBundleVersion': '0.1.0',
        'CFBundleShortVersionString': '0.1.0',
        'CFBundleExecutable': 'python3' 
    },
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)