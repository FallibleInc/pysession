"""
A python history_startup script that persists your work in a Python shell like IDLE
or PySession.is_ipython.
This script saves your work to a secret Gist on Github or to a local file.
"""

import io
from os.path import expanduser, isfile
from sys import stdout
import sys
import atexit
import readline
import webbrowser
import datetime
import json
import codecs
import time
import pickle

try:
    import urllib2 as urllib
except ImportError:
    import urllib.request as urllib


stdout.write('''
    \033[95m
    -----------------------------------------------\n
    This interpreter session will be saved to a secret Gist.\n
    You can stop saving this session by typing \033[1mPySession.off()\033[0m\033[95m\n
    To save locally on your disk instead of Gist type \033[1mPySession.local()\033[0m\033[95m\n
    ------------------------------------------------\n\033[0m''')


DO_NOTHING = '\033[95m Nothing to export to Gist. Exiting. \n\033[0m'
SAVING_GIST = '\033[95m Saving your session to a secret Gist.. \n\033[0m'
SAVING_FILE = '\033[95m Saving your session to a local file in current directory. \n\033[0m'
SUCCESS = '\033[95m Saved your session successfully! \n\033[0m'
FAILED = '\033[95m Could not save to Gist. Saving to local file. \n\033[0m'
GIST_DESCRIPTION = 'Exported from a Python REPL at '
GIST_API_URL = 'https://api.github.com/gists'
SESSIONS_STORAGE = expanduser('~') + '/.pysession.pickle'
LAST_GISTS = '\033[95m    LAST 5 EXPORTED GISTS: \n\033[0m'


class PySession(object):
    save = True
    save_locally = False
    is_ipython = False
    ipython_history = None
    start_index = 0
    wrong_code_lines = []
    previous_sessions = []

    @classmethod
    def off(cls):
        cls.save = False

    @classmethod
    def local(cls):
        cls.save_locally = True

    @classmethod
    def save_to_file(cls, data, filename=None):
        """Saves the session code to a local file in current directory"""
        filename = filename or str(time.time()) + '.py'
        file_p = io.open(filename, 'wb')
        file_p.write(data)
        file_p.close()

    @classmethod
    def save_to_gist(cls, data, filename=None):
        """Creates a secret GitHub Gist with the provided data and filename"""
        filename = filename or str(time.time())
        date = datetime.datetime.now().strftime("%I:%M%p on %B %d, %Y")
        gist = {
            'description': GIST_DESCRIPTION + date,
            'public': False,
            'files': {'gist_' + filename + '.py': {'content': data}}
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
        if isfile(SESSIONS_STORAGE):
            PySession.previous_sessions = pickle.load(
                io.open(SESSIONS_STORAGE, 'rb'))
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
    """Processes python sheell history to an array of code lines"""
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
        if line.strip() in ['exit' or 'exit()']:  # remove 'exit' from code
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

    if PySession.save_locally:
        stdout.write(SAVING_FILE)
        PySession.save_to_file('\n'.join(lines_of_code))
        stdout.write(SUCCESS)
        return

    try:
        stdout.write(SAVING_GIST)
        gist_response = PySession.save_to_gist('\n'.join(lines_of_code))
        gist_url = gist_response['html_url']
        PySession.save_gist_url(gist_url)
        webbrowser.open_new_tab(gist_url)
        stdout.write(SUCCESS)
    except:
        stdout.write(FAILED)
        PySession.save_to_file('\n'.join(lines_of_code))


init()
atexit.register(before_exit)
