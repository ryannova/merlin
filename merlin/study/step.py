###############################################################################
# Copyright (c) 2019, Lawrence Livermore National Security, LLC.
# Produced at the Lawrence Livermore National Laboratory
# Written by the Merlin dev team, listed in the CONTRIBUTORS file.
# <merlin@llnl.gov>
#
# LLNL-CODE-797170
# All rights reserved.
# This file is part of Merlin, Version: 1.7.3.
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

import logging
import re
from contextlib import suppress
from copy import deepcopy
from datetime import datetime

from maestrowf.abstracts.enums import State
from maestrowf.datastructures.core.executiongraph import _StepRecord

from merlin.common.abstracts.enums import ReturnCode
from merlin.study.script_adapter import MerlinScriptAdapter
from merlin.utils import create_dirs
from merlin.study.localscriptadapter import LocalScriptAdapter


LOG = logging.getLogger(__name__)

def round_datetime_seconds(input_datetime):
    new_datetime = input_datetime

    if new_datetime.microsecond >= 500000:
        new_datetime = new_datetime + datetime.timedelta(seconds=1)

    return new_datetime.replace(microsecond=0)

class MerlinStepRecord:
    """
    This classs is a wrapper for the Maestro _StepRecord to remove 
    a re-submit message.
    """

    def __init__(self, workspace_value, step, **kwargs):
        # _StepRecord.__init__(self, workspace, step, **kwargs)
        self.workspace_value = workspace_value
        self.step = step
        self.param_index = -1
        self.orig_name = self.step["name"]

        self.jobid = kwargs.get("jobid", [])
        self.script = kwargs.get("script", "")
        self.restart_script = kwargs.get("restart", "")
        self.to_be_scheduled = False
        self.restart_limit = kwargs.get("restart_limit", 3)

        # Status Information
        self._num_restarts = 0
        self._submit_time = None
        self._start_time = None
        self._end_time = None
        self.status = kwargs.get("status", State.INITIALIZED)

    def __getitem__(self, key):
        return self.step[key]

    def mark_submitted(self):
        """Mark the submission time of the record."""
        #LOG.debug(
        #    "Marking %s as submitted (PENDING) -- previously %s", self.name, self.status
        #)
        self.status = State.PENDING
        if not self._submit_time:
            self._submit_time = datetime.now()
        else:
            #LOG.debug(
            #    "Merlin: Cannot set the submission time of '%s' because it has "
            #    "already been set.",
            #    self.name,
            #)
            pass

    def setup_workspace(self):
        create_dirs(self.workspace_value)

    def execute(self, adapter):
        self.mark_submitted()
        retcode, jobid = self._execute(adapter, self.script)

        if retcode == SubmissionCode.OK:
            self.jobid.append(jobid)

        return retcode

    def restart(self, adapter):
        retcode, jobid = self._execute(adapter, self.restart_script)

        if retcode == SubmissionCode.OK:
            self.jobid.append(jobid)

        return retcode

    def _execute(self, adapter, script):
        if self.to_be_scheduled:
            srecord = adapter.submit(
                self.step, script, self.workspace.value)
        else:
            self.mark_running()
            ladapter = LocalScriptAdapter()
            srecord = ladapter.submit(
                self.step, script, self.workspace.value)

        retcode = srecord.submission_code
        jobid = srecord.job_identifier
        return retcode, jobid

    def mark_submitted(self):
        """Mark the submission time of the record."""
        #LOGGER.debug(
        #    "Marking %s as submitted (PENDING) -- previously %s",
        #    self.name,
        #    self.status)
        self.status = State.PENDING
        if not self._submit_time:
            self._submit_time = round_datetime_seconds(datetime.now())
        else:
            pass
            #LOGGER.warning(
            #    "Cannot set the submission time of '%s' because it has "
            #    "already been set.", self.name
            #)

    def mark_running(self):
        """Mark the start time of the record."""
        #LOGGER.debug(
        #    "Marking %s as running (RUNNING) -- previously %s",
        #    self.name,
        #    self.status)
        self.status = State.RUNNING
        if not self._start_time:
            self._start_time = round_datetime_seconds(datetime.now())

    def mark_end(self, state):
        """
        Mark the end time of the record with associated termination state.

        :param state: State enum corresponding to termination state.
        """
        #LOGGER.debug(
        #    "Marking %s as finished (%s) -- previously %s",
        #    self.name,
        #    state,
        #    self.status)
        self.status = state
        if not self._end_time:
            self._end_time = round_datetime_seconds(datetime.now())

    def mark_restart(self):
        """Mark the end time of the record."""
        #LOGGER.debug(
        #    "Marking %s as restarting (TIMEOUT) -- previously %s",
        #    self.name,
        #    self.status)
        self.status = State.TIMEDOUT
        # Designating a restart limit of zero as an unlimited restart setting.
        # Otherwise, if we're less than restart limit, attempt another restart.
        if self.restart_limit == 0 or \
                self._num_restarts < self.restart_limit:
            self._num_restarts += 1
            return True
        else:
            return False

class Step:
    """
    This class provides an abstraction for an execution step, which can be
    executed by calling execute.
    """

    def __init__(self, merlin_step_record):
        """
        :param merlin_step_record: The StepRecord object.
        """
        self.merlin_step_record = merlin_step_record
        self.restart = False

    def __getitem__(self, key):
        return self.merlin_step_record[key]

    def get_cmd(self):
        """
        get the run command text body"
        """
        print(self.merlin_step_record)
        return self["run"]["cmd"]

    def get_restart_cmd(self):
        """
        get the restart command text body, else return None
        """
        if "restart" in self["run"]:
            return self["run"]["restart"]
        return None

    def clone_changing_workspace_and_cmd(
        self, new_cmd=None, cmd_replacement_pairs=None, new_workspace=None
    ):
        """
        Produces a deep copy of the current step, performing variable
        substitutions as we go

        :param new_cmd : (Optional) replace the existing cmd with the new_cmd.
        :param cmd_replacement_pairs : (Optional) replaces strings in the cmd
            according to the list of pairs in cmd_replacement_pairs
        :param new_workspace : (Optional) the workspace for the new step.
        """
        LOG.debug(f"clone called with new_workspace {new_workspace}")
        step_dict = deepcopy(self.merlin_step_record.step)

        if new_cmd is not None:
            step_dict["run"]["cmd"] = new_cmd

        if cmd_replacement_pairs is not None:
            for str1, str2 in cmd_replacement_pairs:
                cmd = step_dict["run"]["cmd"]
                step_dict["run"]["cmd"] = re.sub(re.escape(str1), str2, cmd, flags=re.I)

                restart_cmd = self.get_restart_cmd()
                if restart_cmd:
                    step_dict["run"]["restart"] = re.sub(
                        re.escape(str1), str2, restart_cmd, flags=re.I
                    )

        if new_workspace is None:
            new_workspace = self.get_workspace()
        LOG.debug(f"cloned step with workspace {new_workspace}")
        return Step(MerlinStepRecord(new_workspace, step_dict))

    def get_task_queue(self):
        """ Retrieve the task queue for the Step."""
        return self.get_task_queue_from_dict(self.merlin_step_record)

    @staticmethod
    def get_task_queue_from_dict(step_dict):
        """ given a maestro step dict, get the task queue"""
        with suppress(TypeError, KeyError):
            queue = step_dict["run"]["task_queue"]
            if queue is None or queue.lower() == "none":
                queue = "merlin"
            return queue
        return "merlin"

    @property
    def max_retries(self):
        """
        Returns the max number of retries for this step.
        """
        return self["run"]["max_retries"]

    def __get_restart(self):
        """
        Set the restart property ensuring that restart is false
        """
        return self.__restart

    def __set_restart(self, val):
        """
        Set the restart property ensuring that restart is false
        """
        self.__restart = val

    restart = property(__get_restart, __set_restart)

    def is_parameterized(self):
        return self.merlin_step_record.param_index != -1

    def contains_global_params(self, params):
        for param_name, param in params.items():
            if f"$({param_name})" in self.get_cmd():
                return True
        return False
        
    def expand_global_params(self, params):
        """
        Return a list of parameterized copies of this step.
        """
        if params is None or len(params) == 0:
        #if (params is None or len(params) == 0) or (not self.contains_global_params(params)):
            return None

        print(f"***NAME: {self['name']}")

        expanded_steps = []
        expanded_step_names = []
        num_params = len(next(iter(params.values()))["values"])

        for num in range(num_params):
            new_step = deepcopy(self)
            new_step.merlin_step_record.param_index = num
            new_step_name = self["name"] + "/"
            for param_name, param in params.items():
                param_vals = param["values"]
                param_label = param["label"] 
                new_step["run"]["cmd"] = new_step.get_cmd().replace(f"$({param_name})", str(param_vals[num]))
                if new_step_name != self["name"] + "/":
                    new_step_name += "."
                new_step_name += param_label.replace("%%", str(param_vals[num]))
            expanded_steps.append(new_step)
            expanded_step_names.append(new_step_name)
        return list(zip(expanded_steps, expanded_step_names))

    def needs_merlin_expansion(self, labels):
        """
        :return : True if the cmd has any of the default keywords or spec
            specified sample column labels.
        """
        merlin_step_keywords = ["MERLIN_SAMPLE_ID", "MERLIN_SAMPLE_PATH", "merlin_sample_id", "merlin_sample_path"]

        needs_expansion = False

        cmd = self.get_cmd()
        for label in labels + merlin_step_keywords:
            if f"$({label})" in cmd:
                needs_expansion = True

        # The restart may need expansion while the cmd does not.
        restart_cmd = self.get_restart_cmd()
        if not needs_expansion and restart_cmd:
            for label in labels + merlin_step_keywords:
                if f"$({label})" in restart_cmd:
                    needs_expansion = True

        return needs_expansion

    def get_workspace(self):
        """
        :return : The workspace this step is to be executed in.
        """
        return self.merlin_step_record.workspace_value

    def name(self):
        """
        :return : The step name.
        """
        return self["name"]

    def execute(self, adapter_config):
        """
        Execute the step.

        :param adapter_config : A dictionary containing configuration for
            the maestro script adapter, as well as which sort of adapter
            to use.
        """
        # cls_adapter = ScriptAdapterFactory.get_adapter(adapter_config['type'])
        cls_adapter = MerlinScriptAdapter

        # Update shell if the task overrides the default value from the batch section
        print("***ADAPTER CONFIG")
        print(adapter_config)
        if "shell" not in adapter_config:
            adapter_config["shell"] = "/bin/bash" #TODO is this okay?
        default_shell = adapter_config.pop("shell")
        shell = self["run"].pop("shell", default_shell)
        adapter_config.update({"shell": shell})

        # Update batch type if the task overrides the default value from the batch section
        default_batch_type = adapter_config.pop("batch_type", adapter_config["type"])
        # Set batch_type to default if unset
        adapter_config.update({"batch_type": default_batch_type})
        # Override the default batch: type: from the step config
        batch = self["run"].pop("batch", None)
        if batch:
            batch_type = batch.pop("type", default_batch_type)
            adapter_config.update({"batch_type": batch_type})

        adapter = cls_adapter(**adapter_config)
        LOG.debug(f"Maestro step config = {adapter_config}")

        # Preserve the default shell if the step shell is different
        adapter_config.update({"shell": default_shell})
        # Preserve the default batch type if the step batch type is different
        adapter_config.update({"batch_type": default_batch_type})

        self.merlin_step_record.setup_workspace()
        # self.merlin_step_record.generate_script(adapter) TODO make sure all substitutions are taken care of beforehand
        #print(self.merlin_step_record.step)
        #import sys
        #sys.exit()
        step_name = self.name()
        step_dir = self.get_workspace()

        # dry run: sets up a workspace without executing any tasks. Each step's
        # workspace directory is created, and each step's command script is
        # written to it. The command script is not run, so there is no
        # 'MERLIN_FINISHED' file, nor '<step>.out' nor '<step>.err' log files.
        if adapter_config["dry_run"] is True:
            return ReturnCode.DRY_OK

        LOG.info(f"Executing step '{step_name}' in '{step_dir}'...")
        # TODO: once maestrowf is updated so that execute returns a
        # submissionrecord, then we need to return the record.return_code here
        # at that point, we can drop the use of MerlinScriptAdapter above, and
        # go back to using the adapter specified by the adapter_config['type']
        # above
        # If the above is done, then merlin_step in tasks.py can be changed to
        # calls to the step execute and restart functions.
        if self.restart and self.get_restart_cmd():
            return ReturnCode(self.merlin_step_record.restart(adapter))
        else:
            return ReturnCode(self.merlin_step_record.execute(adapter))
