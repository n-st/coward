#!/usr/bin/env python

import sys
import os
import re
import subprocess
import argparse
import yaml
from time import strftime
import textwrap


VALID_COMMANDS = ['all', 'snapshot', 'prune', 'push']
DEFAULT_CONFIG_FILE = '/etc/coward.yaml'


def btrfs_subvolume_list(mountpoint):
    # 'btrfs su li <path>' outputs something like
    # ID 305 gen 18482 top level 5 path @rootfs

    exec_cmd = ['btrfs', 'subvolume', 'list', mountpoint]
    output = subprocess.check_output(exec_cmd, stderr=subprocess.STDOUT)
    subvolumes = [x.split(' ')[8] for x in output.splitlines()]

    return subvolumes


def command_all(params):
    global config
    global simulate

    if params:
        raise Exception('The command \'all\' does not expect any parameters, but got \'%s\'.' % str(params))


def command_prune(params):
    global config
    global simulate

    if not 'prune' in config:
        raise Exception('The config file doesn\'t contain any prune targets.')

    prunings = config['prune']

    if params:
        targets = params.split(',')
    else:
        targets = prunings.keys()

    for target in targets:
        if target not in prunings.keys():
            raise Exception('The prune target \'%s\' does not exist.' % target)

        mountpoint = prunings[target]['mountpoint']
        directory = prunings[target]['dir']

        subvolumes = btrfs_subvolume_list(mountpoint)
        subvolumes = [x for x in subvolumes if x.startswith(directory)]
        subvolumes.sort(reverse=True)

        keep = []
        regexes = prunings[target]['keep']

        for regex in regexes.keys():
            keepcount = regexes[regex]

            # search for subvolumes that match the regex, then keep the first <keepcount> of them
            matches = [x for x in subvolumes if re.search(regex, x)][:keepcount]

            keep += matches

        subvolumes_to_delete = set(subvolumes) - set(keep)

        # sort set so oldest subvolumes are deleted first
        # -> more time to press Ctrl+C ;)
        for subvolume in sorted(subvolumes_to_delete):
            exec_cmd = 'btrfs subvolume delete ' + os.path.join(mountpoint, subvolume)

            if simulate:
                print(exec_cmd)
            else:
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

    parser = argparse.ArgumentParser(
            prog='coward',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            description='coward: automate btrfs backups',
            epilog=textwrap.dedent('''\
                Supported commands:
                    all:        Run 'snapshot', 'push' and 'prune' for all respective
                                targets (in this order).
                    snapshot:   Create btrfs snapshots for the specified targets.
                    push:       Copy snapshots using 'btrfs send/receive'.
                    prune:      Delete snapshots according to the target's 'keep'
                                configuration ("keep the last n snapshots matching
                                this regex").

                Targets are always specified in the form 'command:target1,target2'.
                If no targets are specified, all targets for the selected command are
                processed.''')
            )
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
