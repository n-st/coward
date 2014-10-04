#!/usr/bin/env python

import sys
import argparse
import yaml

VALID_COMMANDS = ['all', 'snapshot', 'prune', 'push']


def command_all(params):
    if params:
        raise Exception('The command \'all\' does not expect any parameters, but got \'%s\'.' % str(params))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", "-c", help="Specify the path to an alternate config file. By default, /etc/coward.yaml is used.")
    parser.add_argument('commands', nargs='+')

    args = parser.parse_args()
    commands = [x.split(':') for x in args.commands]

    # terminate on invalid parameters
    for command in commands:
        if command[0] not in VALID_COMMANDS:
            raise Exception('\'%s\' is not a valid command (or not supported by this version of coward)' % command[0])

    # begin actual work
    for command in commands:
        # Directly call the handler function for the current command.
        # This is safe because we validated param[0] against VALID_COMMANDS earlier.

        handler_function_name = 'command_' + command[0]

        if not handler_function_name in globals():
            raise Exception('The function \'%s\' could not be found. This is definitely a bug.' % handler_function_name)

        handler_function = globals()[handler_function_name]
        if len(command) > 1:
            handler_function_params = command[1]
        else:
            handler_function_params = None
        handler_function(handler_function_params)


if __name__ == "__main__":
    main()
