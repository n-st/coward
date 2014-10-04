#!/usr/bin/env python

import sys
import os
import argparse
import yaml
from time import strftime


VALID_COMMANDS = ['all', 'snapshot', 'prune', 'push']
DEFAULT_CONFIG_FILE = '/etc/coward.yaml'


def command_all(params):
    global config
    global simulate

    if params:
        raise Exception('The command \'all\' does not expect any parameters, but got \'%s\'.' % str(params))


def command_prune(params):
    global config
    global simulate

    if params:
        pass
    pass


def command_push(params):
    global config
    global simulate

    if params:
        pass
    print config
    pass


def command_snapshot(params):
    global config
    global simulate

    if not 'snapshot' in config:
        raise Exception('The config file doesn\'t contain any snapshot targets.')

    snapshots = config['snapshot']

    if params:
        targets = params.split(',')
    else:
        targets = snapshots.keys()

    for target in targets:
        if target not in snapshots.keys():
            raise Exception('The snapshot target \'%s\' does not exist.' % target)

        src = snapshots[target]['src']
        dest = snapshots[target]['dest']
        if 'readonly' in snapshots[target]:
            readonly = snapshots[target]['readonly']
        else:
            readonly = False

        exec_cmd = \
                'btrfs subvolume snapshot ' + \
                ('-r ' if readonly else '') + \
                src + ' ' + \
                strftime(dest)

        if simulate:
            print(exec_cmd)
        else:
            pass


def main():
    global config
    global simulate

    parser = argparse.ArgumentParser()
    parser.add_argument("--config", "-c", help="Specify the path to an alternate config file. By default, /etc/coward.yaml is used.")
    parser.add_argument("--simulate", "-s", "--dry-run", action="store_true", help="Show the commands that would be executed, but don\'t actually run them.")
    parser.add_argument('commands', nargs='+')

    args = parser.parse_args()
    commands = [x.split(':') for x in args.commands]

    # terminate on invalid parameters
    for command in commands:
        if command[0] not in VALID_COMMANDS:
            raise Exception('\'%s\' is not a valid command (or not supported by this version of coward)' % command[0])

    config_file = args.config or DEFAULT_CONFIG_FILE
    if not os.path.isfile(config_file):
        raise Exception('Config file \'%s\' does not exist or is not a file.' % config_file)
    f = open(config_file)
    config = yaml.safe_load(f)
    f.close()

    simulate = args.simulate
    if simulate:
        print('Simulation mode. These are the commands that would have been run (if any):')

    # begin actual work
    for command in commands:
        # Directly call the handler function for the current command.
        # This is safe because we validated command[0] against VALID_COMMANDS earlier.

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
