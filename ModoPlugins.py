#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Sublime Text Plugin for generating Modo Commands inside of Sublime.

Installation:
Install through Package Control by searching for "Modo Plugin Builder"
Or download the ZIP and go to Preferences > Browse Packages and put the
ModoPluginBuilder folder in there. Then restart Sublime.

Usage:
You will have a new submenu at the bottom of Tools which will allow you to
create a Modo command or create a new kit.

Both of these go to the USER Scripts folder. Part of the reason I chose to
make this is that on OS X, the new function that is currently inside of Modo
will install to the root directory and cause permission errors. The other
reason I made this is because it's a nice idea but it's only available to
people who purchased 901.

Plus, I prefer Sublime.

You can also directly open the Modo documentation forums as well as
search the TDSDK and SDK pages from within Sublime.
Simple go to Tools > Modo Plugins > Search TDSDK Docs / Search PyAPI Docs and
the input will appear at the bottom of the Sublime Text window for what you
want to search for.
"""

__author__ = "Alex Widener"
__email__ = "alexwidener#google"
__website__ = "http://www.github.com/alexwidener"
__date__ = "June 20, 2015"
__copyright__ = "MIT "

import os
import webbrowser
import subprocess

import sublime
import sublime_plugin

commandName = "command.name"
USER_DIR = os.path.expanduser('~')
IS_WIN = (os.name == 'nt')
ILLEGALCHARS = ' !@#$%^&*(){}[]|\\:;"\'<,>?/`~'
ILLEGALCHARMSG = 'You have an illegal character in your commandName.'
FOLDEREXISTSMSG = 'This folder already exists. Try a new command name.'

TDSDKsearchURL = 'http://sdk.luxology.com/td-sdk/search.html?q=%s&check_keywords=yes&area=default'
TDSDKURL = 'http://sdk.luxology.com/td-sdk/'
PYAPIURL = 'http://sdk.luxology.com/wiki/Category:Python_API'
PYAPIsearchURL = 'http://sdk.luxology.com/index.php?search=%s&button=&title=Special%3ASearch'
SDKURL = 'http://sdk.luxology.com/wiki/SDK'
HEADER = '#!/usr/bin/python\n# -*- coding: utf-8 -*-\n' \
         '"""\nDocstring here\n"""\n__author__ = "Your Name"\n' \
         '__copyright__ = "Your License"\n__version__ = "0.1"\n' \
         '__email__ = "Your Email"\n__status__ = "Development"\n' \
         '__date__ = "Last Edited Date"\n\n'


if IS_WIN:
    SCRIPTSPATH = os.path.join(USER_DIR, "AppData", "Roaming", "Luxology",
                                                               "Scripts")
else:
    # Look up this path when you turn on your MacBook
    SCRIPTSPATH = os.path.join(USER_DIR, "Library", "Application Support",
                                                    "Luxology",
                                                    "Scripts")


def checkName(commandName):
    for char in commandName:
        if char in ILLEGALCHARS:
            return False
    return True


def generateCommand(folder, commandName):
    # Work on Cookie Cutter once this is done.

    cleanCommand = ''.join([l for l in commandName if l not in '.'])

    lxifc = True
    select = True

    cmdclassName = 'CMD' + cleanCommand
    command = HEADER
    command += '\nimport lx\nimport lxu.command\n'
    if lxifc:
        command += 'import lxifc\n'
    if select:
        command += 'import lxu.select\n'

    command += '\n\n' \
        'class {0}(lxu.command.BasicCommand):\n' \
        '    def __init__(self):\n' \
        '        lxu.command.BasicCommand.__init__(self)\n' \
        '        self.dyna_Add("argumentName", lx.symbol.sTYPE_STRING)\n' \
        '        self.basic_SetFlags(0, lx.symbol.fCMDARG_OPTIONAL)\n\n' \
        '    def cmd_Flags(self):\n' \
        '        return lx.symbol.fCMD_MODEL | lx.symbol.fCMD_UNDO\n\n' \
        '    def cmd_Query(self, index, vaQuery):\n' \
        '        lx.notimpl()\n\n' \
        '    def basic_Execute(self, msg, flags):\n' \
        '        print("Hello, World")\n\n' \
        '    def basic_Enable(self, msg):\n' \
        '        return True\n\n' \
        '    def cmd_Interact(self):\n' \
        '        pass\n\nlx.bless({0}, "{1}")\n'.format(cmdclassName,
                                                        commandName)

    commandFile = os.path.join(folder, 'CMD' + cleanCommand + '.py')
    with open(commandFile, 'w') as f:
        f.write(command)

    return commandFile


class ModoMakeComm(sublime_plugin.TextCommand):
    def run(self, edit, text='command.name'):
        self.view.window().show_input_panel("Command Name:", text,
                                            self.commandCheck, None, None)
        self.lxservFolder = os.path.join(SCRIPTSPATH, 'lxserv')

    def commandCheck(self, commandName):
        if checkName(commandName):
            if not os.path.isdir(self.lxservFolder):
                os.makedirs(self.lxservFolder)
            commandPath = generateCommand(self.lxservFolder, commandName)
            self.view.window().open_file(commandPath)
        else:
            sublime.error_message(ILLEGALCHARMSG)
            self.view.window().show_input_panel("Command Name:", commandName,
                                                self.commandCheck, None, None)


class ModoMakeKit(sublime_plugin.TextCommand):
    def run(self, edit, commandName="command.name"):
        self.view.window().show_input_panel("Command Name:", commandName,
                                            self.commandCheck, None, None)

    def commandCheck(self, commandName):
        if checkName(commandName):
            self.makeFolder(commandName)
        else:
            sublime.error_message(ILLEGALCHARMSG)
            self.view.window().show_input_panel("Command Name:", commandName,
                                                self.commandCheck, None, None)

    def makeFolder(self, commandName):
        # Have to remove the . from the commandName
        folderName = ''.join([l for l in commandName if l not in '.'])
        kitFolder = os.path.join(SCRIPTSPATH, folderName)
        kitScriptsFolder = os.path.join(kitFolder, 'Scripts')
        lxservFolder = os.path.join(kitScriptsFolder, 'lxserv')
        if not os.path.isdir(kitFolder):
            os.makedirs(lxservFolder)
            commandPath = generateCommand(lxservFolder, commandName)
            self.generateInitialize(kitScriptsFolder)
            self.generateIndex(kitFolder, folderName)
            self.view.window().open_file(commandPath)
        else:
            sublime.error_message(FOLDEREXISTSMSG)
            self.view.window().show_input_panel('Command Name:', commandName,
                                                self.checkName, None, None)

    def generateInitialize(self, kitScriptsFolder):
        filePath = os.path.join(kitScriptsFolder, '__init__.py')
        with open(filePath, 'w') as f:
            f.write('')

    def generateIndex(self, kitFolder, folderName):
        # Could have done this with an xml generator but I didn't see the point
        xml = '<?xml version="1.0"?>\n' \
              '  <configuration kit="{0}">\n' \
              '    <import>Scripts</import>\n' \
              '      <atom type="ScriptSystem">\n' \
              '        <hash type="ScriptAlias" key="">\n' \
              '          </hash>\n' \
              '       </atom>\n</configuration>'.format(folderName)

        filePath = os.path.join(kitFolder, 'index.CFG')
        with open(filePath, 'w') as f:
            f.write(xml)


class ShowScriptsFolder(sublime_plugin.TextCommand):
    """ Open the default User Scripts folder. """
    def run(self, edit):
        self.view.window().run_command("open_dir", {"dir": SCRIPTSPATH})


class ModoTdsdkDocs(sublime_plugin.TextCommand):
    def run(self, edit):
        webbrowser.open_new_tab(TDSDKURL)


class ModoPythonDocs(sublime_plugin.TextCommand):
    def run(self, edit):
        webbrowser.open_new_tab(PYAPIURL)


class SearchPythonDocs(sublime_plugin.TextCommand):
    def run(self, edit):
        self.view.window().show_input_panel('PyAPI Search:', '',
                                            self.openSearch, None, None)

    def openSearch(self, input):
        if not isinstance(input, str):
            input = str(input)
        webbrowser.open(PYAPIsearchURL.replace('%s', input))


class SearchTdsdkDocs(sublime_plugin.TextCommand):
    def run(self, edit):
        self.view.window().show_input_panel('TDSDK Search:', '',
                                            self.openSearch, None, None)

    def openSearch(self, input):
        if not isinstance(input, str):
            input = str(input)
        webbrowser.open(TDSDKsearchURL.replace('%s', input))


class ModoSdkDocs(sublime_plugin.TextCommand):
    def run(self, edit):
        webbrowser.open_new_tab(SDKURL)


class ModoMakeScript(sublime_plugin.TextCommand):
    def run(self, edit):
        import datetime
        currentTime = str(datetime.datetime.now()).split('.')[0]
        currentTime = currentTime.replace(':', '_').replace(' ', '_')
        tempScript = os.path.join(SCRIPTSPATH, 'temp_' + currentTime + '.py')
        if not os.path.isfile(tempScript):
            script = HEADER
            script += '\nimport traceback\n\n\ndef main():\n' \
                      '    print("Hello, World")\n\n' \
                      'if __name__ == "__main__":\n' \
                      '    try:\n        main()\n' \
                      '    except:\n        print(traceback.format_exc())\n'

            with open(tempScript, 'w') as f:
                f.write(script)

        self.view.window().open_file(tempScript)
