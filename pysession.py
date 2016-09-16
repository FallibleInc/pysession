"""A Python history_startup script that persists your work in a Python shell like IDLE or IPython.

This script saves your work to a secret Gist on Github or to a local file.
"""

import atexit
import codecs
import datetime
import io
import json
import os
import pickle
import readline
import sys
import webbrowser

from os.path import expanduser, isfile, join
from sys import stdout

try:
    import urllib2 as urllib
except ImportError:
    import urllib.request as urllib


DO_NOTHING = '\033[95mNothing to save in this session. Exiting. \n\033[0m'
SAVING_GIST = "\033[95mSaving your session to a secret Gist as '{filename}'. \n\033[0m"
SAVING_FILE = "\033[95mSaving your session to local file '{filename}'.\n\033[0m"
SUCCESS = '\033[95mSaved your session successfully!\n\033[0m'
FAILED = '\033[95mCould not save to Gist. Saving to local file.\n\033[0m'
GIST_DESCRIPTION = 'Exported from a Python Shell using pysession at '
GIST_API_URL = 'https://api.github.com/gists'
SESSIONS_STORAGE = join(expanduser('~'), '.pysession.pickle')
LAST_GISTS = '\033[95m    LAST 5 EXPORTED GISTS: \n\033[0m'
BANNER_GIST = "This interpreter session will be saved to a secret Gist.\n"
BANNER_LOCAL = "This interpreter session will be saved to a local file.\n"
BANNER_OFF = "This interpreter session will not be saved.\n"
BANNER_DISABLE = "You can disable saving this session by typing \033[1mPySession.off()\033[0m\033[95m.\n"
BANNER_ENABLE = "You can enable saving this session type \033[1mPySession.on()\033[0m\033[95m.\n"
BANNER_SWITCH = """\
To switch between saving the session locally on your disk or
as a secret Gist type \033[1mPySession.local()\033[0m\033[95m resp. \033[1mPySession.gist()\033[0m\033[95m.
"""


class PySession(object):
    save = True
    save_locally = False
    is_ipython = False
    ipython_history = None
    start_index = 0
    wrong_code_lines = []
    previous_sessions = []

    @classmethod
    def on(cls):
        """Turn on saving for this particular shell session."""
        cls.save = True

    @classmethod
    def off(cls):
        """Turn off saving for this particular shell session."""
        cls.save = False

    @classmethod
    def local(cls):
        """Switch to saving the current session to a local file."""
        cls.save = True
        cls.save_locally = True

    @classmethod
    def gist(cls):
        """Switch to saving the current session to a secret gist."""
        cls.save = True
        cls.save_locally = False

    @classmethod
    def save_to_file(cls, data, filename):
        """Saves the session code to a local file in current directory."""
        file_p = io.open(filename, 'wb')
        file_p.write(data)
        file_p.close()

    @classmethod
    def save_to_gist(cls, data, filename):
        """Create a secret GitHub Gist with the provided data and filename."""
        date = datetime.datetime.now().strftime("%I:%M%p on %B %d, %Y")
        gist = {
            'description': GIST_DESCRIPTION + date,
            'public': False,
            'files': {filename: {'content': data}}
        }

        headers = {'Content-Type': 'application/json'}
        req = urllib.Request(GIST_API_URL,
                             json.dumps(gist).encode(),
                             headers)
        response = urllib.urlopen(req)
        reader = codecs.getreader("utf-8")
        json_response = json.load(reader(response))
        return json_response

    @classmethod
    def load_history_urls(cls):
        """Loads Gist URLs of past sessions from a pickle file."""
        if isfile(SESSIONS_STORAGE):
            PySession.previous_sessions = pickle.load(
                io.open(SESSIONS_STORAGE, 'rb'))

        if PySession.previous_sessions:
            stdout.write(LAST_GISTS)
            for session_url in PySession.previous_sessions:
                stdout.write('\t' + session_url + '\n')

    @classmethod
    def save_gist_url(cls, url):
        PySession.previous_sessions.append(url)
        PySession.previous_sessions = PySession.previous_sessions[-5:]
        with io.open(SESSIONS_STORAGE, 'wb') as pickle_file:
            pickle.dump(PySession.previous_sessions, pickle_file, protocol=2)


def init():
    stdout.write("\033[95m----------------------------------------------------------------\n")
    if os.getenv('PYSESSION_SAVE_OFF'):
        PySession.off()
        stdout.write(BANNER_OFF)
    elif os.getenv('PYSESSION_SAVE_LOCALLY'):
        PySession.local()
        stdout.write(BANNER_LOCAL)
    else:
        stdout.write(BANNER_GIST)

    if os.getenv('PYSESSION_SAVE_OFF'):
        stdout.write(BANNER_ENABLE)
    else:
        stdout.write(BANNER_DISABLE)

    stdout.write(BANNER_SWITCH)
    stdout.write("----------------------------------------------------------------\033[0m\n")


    PySession.load_history_urls()
    try:
        from IPython import get_ipython
        PySession.ipython_history = get_ipython().pt_cli.application.buffer.history
        PySession.is_ipython = True
    except (ImportError, AttributeError):
        pass

    if PySession.is_ipython:
        PySession.start_index = len(PySession.ipython_history)

        def custom_hook(shell, etype, evalue, traceback, tb_offset=None):
            PySession.wrong_code_lines.append(
                len(PySession.ipython_history) - 1)
            shell.showtraceback((etype, evalue, traceback),
                                tb_offset=tb_offset)

        get_ipython().set_custom_exc((Exception,), custom_hook)
    else:
        readline.add_history('')  # A hack for a strange bug in 3 < Py <3.5.2
        PySession.start_index = readline.get_current_history_length() + 1

        default_hook = sys.excepthook

        def custom_hook(etype, evalue, traceback):
            PySession.wrong_code_lines.append(
                readline.get_current_history_length())
            default_hook(etype, evalue, traceback)

        sys.excepthook = custom_hook


def process_history():
    """Processes python shell history to an array of code lines"""
    end_index = len(PySession.ipython_history) - 1 if PySession.is_ipython \
        else readline.get_current_history_length()

    lines_of_code = []
    for i in range(PySession.start_index, end_index):
        if i in PySession.wrong_code_lines:
            continue
        if PySession.is_ipython:
            line = PySession.ipython_history[i]
        else:
            line = readline.get_history_item(i)

        # remove 'exit' and PySession keywords from code
        if line.strip() in ['PySession.local()',
                            'PySession.gist()',
                            'PySession.off()',
                            'exit',
                            'exit()']:
            continue
        lines_of_code.append(line)

    if len(
            lines_of_code) > 0 and lines_of_code[-1] != '\n':  # adding extra last newline
        lines_of_code.append('\n')

    return lines_of_code


def before_exit():
    lines_of_code = process_history()

    if not PySession.save or len(lines_of_code) == 0:
        stdout.write(DO_NOTHING)
        return

    filename = expanduser(os.getenv('PYSESSION_FILENAME', 'session.py'))

    if PySession.save_locally:
        stdout.write(SAVING_FILE.format(filename=filename))
        PySession.save_to_file('\n'.join(lines_of_code), filename)
        stdout.write(SUCCESS)
        return

    try:
        stdout.write(SAVING_GIST.format(filename=filename))
        gist_response = PySession.save_to_gist('\n'.join(lines_of_code), filename)
        gist_url = gist_response['html_url']
        PySession.save_gist_url(gist_url)
        webbrowser.open_new_tab(gist_url)
        stdout.write(SUCCESS)
    except:
        stdout.write(FAILED)
        PySession.save_to_file('\n'.join(lines_of_code), filename)


init()
atexit.register(before_exit)
