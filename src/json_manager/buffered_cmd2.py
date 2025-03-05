#!/usr/bin/env python3
# coding=utf-8
import os
import platform
import argparse
from datetime import datetime
from collections import namedtuple

# import requests

# https://cmd2.readthedocs.io/en/latest/features/initialization.html?highlight=category#cmd-instance-attributes
"""A simple example cmd2 application demonstrating the following:
     1) Colorizing/stylizing output
     2) Using multiline commands
     3) Persistent history
     4) How to run an initialization script at startup
     5) How to group and categorize commands when displaying them in help
     6) Opting-in to using the ipy command to run an IPython shell
     7) Allowing access to your application in py and ipy
     8) Displaying an intro banner upon starting your application
     9) Using a custom prompt
    10) How to make custom attributes settable at runtime
"""
import cmd2
from cmd2 import (
    Bg,
    Fg,
    style,
)

# Message = namedtuple("Message", ["type", "content"])
Result = namedtuple("Result", ["result", "output"])
class BufferedCmd(cmd2.Cmd):
    CUSTOM_CATEGORY = 'My Custom Commands'
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # super().__init__(
        #     multiline_commands=['echo'],
        #     persistent_history_file='cmd2_history.dat',
        #     startup_script='scripts/startup.txt',
        #     include_ipy=True,
        # )
        self.multiline_commands=['echo']
        self.persistent_history_file='cmd2_history.dat'
        self.startup_script='scripts/startup.txt'
        # self.include_ipy=True

        # Prints an intro banner once upon application startup
        # self.intro = style('Welcome to cmd2!', fg=Fg.RED, bg=Bg.WHITE, bold=True)
        self.intro = style('Welcome to CLI', fg=Fg.GREEN, bold=True)

        # Show this as the prompt when asking for input
        self.prompt = '>>> '

        # Used as prompt for multiline commands after the first line
        self.continuation_prompt = '... '

        # Allow access to your application in py and ipy via self
        # self.self_in_py = True

        # Set the default category name
        self.default_category = 'cmd2 Built-in Commands'

        # Color to output text in with echo command
        self.foreground_color = Fg.CYAN.name.lower()

        # Make echo_fg settable at runtime
        fg_colors = [c.name.lower() for c in Fg]
        self.add_settable(
            cmd2.Settable('foreground_color', str, 'Foreground color to use with echo command', self, choices=fg_colors)
        )

        # https://cmd2.readthedocs.io/en/latest/features/builtin_commands.html
        self.builtin_cmds = [
            "do_alias", 
            "do_edit", 
            "do_help", 
            "do_history", 
            "do_ipy", 
            "do_macro", 
            "do_py", 
            "do_quit", 
            "do_run_pyscript", 
            "do_run_script", 
            "do__relative_run_script", 
            "do_set", 
            "do_shell", 
            "do_shortcuts"
        ]

        self.timing = True
        # self.hidden_commands.append('py')
        self.hidden_commands.append('switch_user')

        # self.output_msg = ""
        # self.error_msg = ""
        # self.warning_msg = ""
        # self.except_msg = ""
        # self.feedback_msg = ""
        # self.paged_msg = ""
        # self.cached_messages = []
        self.cached_messages = {
            "error": [],
            "except": [],
            "feedback": [],
            "output": [],
            "paged": [],
            "warning": [],
        }
        self.final_messages = self.cached_messages
        self.register_precmd_hook(self.clear_cached_messages)
        # self.register_cmdfinalization_hook(self.concatenate_cached_messages)
        self.result = None
        
        # load_dotenv()?
        # self.user_id = "wxid"
        # self.is_admin = False

    # https://cmd2.readthedocs.io/en/latest/features/hooks.html#precommand-hooks
    def clear_cached_messages(self, data: cmd2.plugin.PrecommandData=None) -> cmd2.plugin.PrecommandData:
        # self.poutput("before the cmd begins")
        # self.cached_messages = []
        for msg_type, msgs in self.cached_messages.items():
            self.cached_messages[msg_type] = []
        self.result = None
        return data

    # https://cmd2.readthedocs.io/en/latest/features/hooks.html#command-finalization-hooks
    def concatenate_cached_messages(self, data: cmd2.plugin.CommandFinalizationData=None) -> cmd2.plugin.CommandFinalizationData:
        self.final_messages = {}
        for msg_type, msgs in self.cached_messages.items():
            self.final_messages[msg_type] = "\n".join(msgs)
        return data

    def extract_msg(self, *args, **kwargs):
        msg = ""
        if len(args) > 0:
            msg = args[0]
        elif "msg" in kwargs:
            msg = kwargs["msg"]
        return msg

    # https://cmd2.readthedocs.io/en/latest/features/generating_output.html#colored-output
    # https://cmd2.readthedocs.io/en/latest/api/cmd.html#cmd2.Cmd.perror
    def perror(self, *args, **kwargs) -> None:
        error_msg = self.extract_msg(*args, **kwargs)
        if (len(self.cached_messages["error"]) > 0) and (self.cached_messages["error"][-1] == error_msg):
            return
        if error_msg and not error_msg.startswith("Elapsed:"):
            # self.cached_messages.append(Message("error", error_msg))
            self.cached_messages["error"].append(error_msg)
        super().perror(*args, **kwargs)
    # https://cmd2.readthedocs.io/en/latest/api/cmd.html#cmd2.Cmd.pexcept
    def pexcept(self, *args, **kwargs) -> None:
        except_msg = self.extract_msg(*args, **kwargs)
        if (len(self.cached_messages["except"]) > 0) and (self.cached_messages["except"][-1] == except_msg):
            return
        # self.cached_messages.append(Message("except", except_msg))
        self.cached_messages["except"].append(except_msg)
        super().pexcept(*args, **kwargs)
    # https://cmd2.readthedocs.io/en/latest/api/cmd.html#cmd2.Cmd.pfailure
    # def pfailure(self, msg: Any = '', *, end: str = '\n', paged: bool = False, chop: bool = False) -> None
    # https://cmd2.readthedocs.io/en/latest/api/cmd.html#cmd2.Cmd.pfeedback
    def pfeedback(self, *args, **kwargs) -> None:
        feedback_msg = self.extract_msg(*args, **kwargs)
        if (len(self.cached_messages["feedback"]) > 0) and (self.cached_messages["feedback"][-1] == feedback_msg):
            return
        # self.cached_messages.append(Message("feedback", feedback_msg))
        self.cached_messages["feedback"].append(feedback_msg)
        super().pfeedback(*args, **kwargs)
    # https://cmd2.readthedocs.io/en/latest/api/cmd.html#cmd2.Cmd.poutput
    def poutput(self, *args, **kwargs) -> None:
        output_msg = self.extract_msg(*args, **kwargs)
        if (len(self.cached_messages["output"]) > 0) and (self.cached_messages["output"][-1] == output_msg):
            return
        # self.cached_messages.append(Message("output", output_msg))
        self.cached_messages["output"].append(output_msg)
        super().poutput(*args, **kwargs)
    # https://cmd2.readthedocs.io/en/latest/api/cmd.html#cmd2.Cmd.ppaged
    def ppaged(self, *args, **kwargs) -> None:
        paged_msg = self.extract_msg(*args, **kwargs)
        if (len(self.cached_messages["paged"]) > 0) and (self.cached_messages["paged"][-1] == paged_msg):
            return
        # self.cached_messages.append(Message("paged", paged_msg))
        self.cached_messages["paged"].append(paged_msg)
        super().ppaged(*args, **kwargs)
    # https://cmd2.readthedocs.io/en/latest/api/cmd.html#cmd2.Cmd.psuccess
    # def psuccess(self, msg: Any = '', *, end: str = '\n', paged: bool = False, chop: bool = False) -> None
    # https://cmd2.readthedocs.io/en/latest/api/cmd.html#cmd2.Cmd.pwarning
    def pwarning(self, *args, **kwargs) -> None:
        warning_msg = self.extract_msg(*args, **kwargs)
        if (len(self.cached_messages["warning"]) > 0) and (self.cached_messages["warning"][-1] == warning_msg):
            return
        # self.cached_messages.append(Message("warning", warning_msg))
        self.cached_messages["warning"].append(warning_msg)
        super().pwarning(*args, **kwargs)

    def execute_commands(self, commands: list) -> Result:
        self.preloop()
        # Do this within whatever event loop mechanism you wish to run a single command
        result = self.runcmds_plus_hooks(commands)
        # print(result)
        self.postloop()
        # return Result(result=self.result, output=self.final_messages)
        return Result(result=self.result, output=self.cached_messages)

    def execute_command(self, command: str) -> Result:
        result = self.execute_commands([command])
        return result

    def run_function(self, function, *args, **kwargs) -> Result:
        # self.preloop()
        self.clear_cached_messages()
        function(*args, **kwargs)
        # self.postloop()
        # self.concatenate_cached_messages()
        # print(self.final_messages)
        # return Result(result=self.result, output=self.final_messages)
        return Result(result=self.result, output=self.cached_messages)
    """
    def init(self, mode: str="user") -> None:
        if (mode == "admin"):
            self.is_admin = True
        elif (mode == "user"):
            self.is_admin = False
            # https://cmd2.readthedocs.io/en/latest/features/disable_commands.html?highlight=hidden#remove-a-command
            # del cmd2.Cmd.do_py
            # https://cmd2.readthedocs.io/en/latest/features/builtin_commands.html#remove-builtin-commands
            # delattr(cmd2.Cmd, 'do_shell')
            # https://cmd2.readthedocs.io/en/latest/features/disable_commands.html?highlight=hidden#disable-a-command
            self.disable_command('switch_user', "Access denied")
            # https://cmd2.readthedocs.io/en/latest/features/disable_commands.html?highlight=hidden#disable-a-category-of-commands
            disable_msg = 'Access denied'
            self.disable_category(self.default_category, disable_msg)

    def do_switch_user(self, args) -> None:
        if not self.is_admin:
            self.perror("Access denied")
            return
        self.user_id = args.user_id
    #"""
    """
    @cmd2.with_category(CUSTOM_CATEGORY)
    def do_intro(self, _):
        # Display the intro banner
        self.poutput(self.intro)
    @cmd2.with_category(CUSTOM_CATEGORY)
    def do_echo(self, arg):
        # Example of a multiline command
        fg_color = Fg[self.foreground_color.upper()]
        self.poutput(style(arg, fg=fg_color))
    @cmd2.with_category(CUSTOM_CATEGORY)
    def do_print(self, line):
        print(line)

    # @cmd2.with_category(CUSTOM_CATEGORY)
    def do_clear(self, args):
        os.system("clear")
    # @cmd2.with_category(CUSTOM_CATEGORY)
    def do_cls(self, args):
        os.system("cls")

    # @cmd2.with_category(CUSTOM_CATEGORY)
    def do_exit(self, args):
        print("exiting...")
        self.set_exit_code()
        # exit()
    # def do_quit(self, args):
    #     self.set_exit_code()
    # https://cmd2.readthedocs.io/en/latest/features/commands.html?highlight=exit#exit-codes
    # https://cmd2.readthedocs.io/en/latest/features/os.html?highlight=exit#exit-codes
    def set_exit_code(self, code: int=-1):
        self.exit_code = code

    def remove_buildin_command(command: str):
        if command not in self.builin_cmds:
            print(f"{command} is not a built-in command")
            return
        delattr(cmd2.Cmd, command)
    #"""

    def do_clear(self, args):
        if (platform.system() == "Windows"):
            cmd = "cls"
        else:
            cmd = "clear"
        os.system(cmd)

def main():
    import sys
    c = ConsoleInterface()
    # c.init(mode="admin")
    sys.exit(c.cmdloop())

if __name__ == "__main__":
    main()