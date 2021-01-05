###############################################################################
# Copyright (c) 2019, Lawrence Livermore National Security, LLC.
# Produced at the Lawrence Livermore National Laboratory
# Written by the Merlin dev team, listed in the CONTRIBUTORS file.
# <merlin@llnl.gov>
#
# LLNL-CODE-797170
# All rights reserved.
# This file is part of Merlin, Version: 1.7.6.
#
# For details, see https://github.com/LLNL/merlin.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
###############################################################################

from __future__ import print_function

import click
import logging
import os
from contextlib import suppress

from merlin import VERSION, router
from merlin.spec.expansion import RESERVED, get_spec_with_expansion


LOG = logging.getLogger("merlin")
DEFAULT_LOG_LEVEL = "INFO"


def verify_filepath(filepath):
    """
    Verify that the filepath argument is a valid
    file.

    :param `filepath`: the path of a file
    """
    filepath = os.path.abspath(os.path.expandvars(os.path.expanduser(filepath)))
    if not os.path.isfile(filepath):
        raise ValueError(f"'{filepath}' is not a valid filepath")
    return filepath


def verify_dirpath(dirpath):
    """
    Verify that the dirpath argument is a valid
    directory.

    :param `dirpath`: the path of a directory
    """
    dirpath = os.path.abspath(os.path.expandvars(os.path.expanduser(dirpath)))
    if not os.path.isdir(dirpath):
        raise ValueError(f"'{dirpath}' is not a valid directory path")
    return dirpath


def parse_override_vars(variables_list):
    """
    Parse a list of variables from command line syntax
    into a valid dictionary of variable keys and values.

    :param `variables_list`: a list of strings, e.g. ["KEY=val",...]
    """
    if variables_list is None:
        return None
    LOG.debug(f"Command line override variables = {variables_list}")
    result = {}
    for arg in variables_list:
        try:
            if "=" not in arg:
                raise ValueError(
                    "--vars requires '=' operator. See 'merlin run --help' for an example."
                )
            entry = arg.split("=")
            if len(entry) != 2:
                raise ValueError(
                    "--vars requires ONE '=' operator (without spaces) per variable assignment."
                )
            key = entry[0]
            if key is None or key == "" or "$" in key:
                raise ValueError(
                    "--vars requires valid variable names comprised of alphanumeric characters and underscores."
                )
            if key in RESERVED:
                raise ValueError(
                    f"Cannot override reserved word '{key}'! Reserved words are: {RESERVED}."
                )

            val = entry[1]
            with suppress(ValueError):
                int(val)
                val = int(val)
            result[key] = val

        except BaseException as e:
            raise ValueError(
                f"{e} Bad '--vars' formatting on command line. See 'merlin run --help' for an example."
            )
    return result


def get_merlin_spec_with_override(args):
    """
    Shared command to return the spec object.

    :param 'args': parsed CLI arguments
    """
    filepath = verify_filepath(args.specification)
    variables_dict = parse_override_vars(args.variables)
    spec = get_spec_with_expansion(filepath, override_vars=variables_dict)
    return spec, filepath


class OptionEatAll(click.Option):
    def __init__(self, *args, **kwargs):
        self.save_other_options = kwargs.pop("save_other_options", True)
        nargs = kwargs.pop("nargs", -1)
        if nargs != -1:
            raise ValueError("nargs, if set, must be -1, not {}")
        super(OptionEatAll, self).__init__(*args, **kwargs)
        self._previous_parser_process = None
        self._eat_all_parser = None

    def add_to_parser(self, parser, ctx):
        def parser_process(value, state):
            # method to hook to the parser.process
            done = False
            value = [value]
            if self.save_other_options:
                # grab everything up to the next option
                while state.rargs and not done:
                    for prefix in self._eat_all_parser.prefixes:
                        if state.rargs[0].startswith(prefix):
                            done = True
                    if not done:
                        value.append(state.rargs.pop(0))
            else:
                # grab everything remaining
                value += state.rargs
                state.rargs[:] = []
            value = tuple(value)

            # call the actual process
            self._previous_parser_process(value, state)

        retval = super(OptionEatAll, self).add_to_parser(parser, ctx)
        for name in self.opts:
            our_parser = parser._long_opt.get(name) or parser._short_opt.get(name)
            if our_parser:
                self._eat_all_parser = our_parser
                self._previous_parser_process = our_parser.process
                our_parser.process = parser_process
                break
        return retval
