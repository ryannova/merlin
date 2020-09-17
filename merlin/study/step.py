###############################################################################
# Copyright (c) 2019, Lawrence Livermore National Security, LLC.
# Produced at the Lawrence Livermore National Laboratory
# Written by the Merlin dev team, listed in the CONTRIBUTORS file.
# <merlin@llnl.gov>
#
# LLNL-CODE-797170
# All rights reserved.
# This file is part of Merlin, Version: 1.7.4.
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
from maestrowf.datastructures.environment import Variable
from maestrowf.datastructures.core.executiongraph import _StepRecord
from maestrowf.datastructures.core.study import StudyStep

from merlin.common.abstracts.enums import ReturnCode
from merlin.study.script_adapter import MerlinScriptAdapter


LOG = logging.getLogger(__name__)


class MerlinStepRecord:
    """
    This classs is a wrapper for the Maestro _StepRecord to remove 
    a re-submit message.
    """

    def __init__(self, workspace, step, **kwargs):
        """
        Initialize a new instance of a StepRecord.
        Used kwargs:
        workspace: The working directory of the record.
        status: The record's current execution state.
        jobid: A scheduler assigned job identifier.
        script: The main script used for executing the record.
        restart_script: Script to resume record execution (if applicable).
        to_be_scheduled: True if the record needs scheduling. False otherwise.
        step: The StudyStep that is represented by the record instance.
        restart_limit: Upper limit on the number of restart attempts.
        tmp_dir: A provided temp directory to write scripts to instead of step
        workspace.
        """
        print(f"***benjstep={step}")
        self.workspace = Variable("WORKSPACE", workspace)
        #step["run"]["cmd"] = self.workspace.substitute(step["run"]["cmd"])
        #step["run"]["restart"] = self.workspace.substitute(step["run"]["restart"])

        self.jobid = kwargs.get("jobid", [])
        self.script = kwargs.get("script", "")
        self.restart_script = kwargs.get("restart", "")
        self.to_be_scheduled = False
        self.step = step
        self.restart_limit = kwargs.get("restart_limit", 3)

        # Status Information
        self._num_restarts = 0
        self._submit_time = None
        self._start_time = None
        self._end_time = None
        self.status = kwargs.get("status", State.INITIALIZED)

        #_StepRecord.__init__(self, workspace, step, **kwargs)

    def mark_submitted(self):
        """Mark the submission time of the record."""
        LOG.debug(
            "Marking %s as submitted (PENDING) -- previously %s", self.name, self.status
        )
        self.status = State.PENDING
        if not self._submit_time:
            self._submit_time = datetime.now()
        else:
            LOG.debug(
                "Merlin: Cannot set the submission time of '%s' because it has "
                "already been set.",
                self.name,
            )

    def setup_workspace(self):
        """Initialize the record's workspace."""
        create_parentdir(self.workspace.value)

    def generate_script(self, adapter, tmp_dir=""):
        """
        Generate the script for executing the workflow step.
        :param adapter: Instance of adapter to be used for script generation.
        :param tmp_dir: If specified, place generated script in the specified
        temp directory.
        """
        if tmp_dir:
            scr_dir = tmp_dir
        else:
            scr_dir = self.workspace.value

        self.step["cmd"] = self.workspace.substitute(self.step["cmd"])

        LOGGER.info("Generating script for %s into %s", self.name, scr_dir)
        self.to_be_scheduled, self.script, self.restart_script = \
            adapter.write_script(scr_dir, self.step)
        LOGGER.info("Script: %s\nRestart: %s\nScheduled?: %s",
                    self.script, self.restart_script, self.to_be_scheduled)

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

    @property
    def can_restart(self):
        """
        Get whether or not the record can be restarted.
        :returns: True if the record has a restart command assigned to it.
        """
        if self.restart_script:
            return True

        return False

    def _execute(self, adapter, script):
        if self.to_be_scheduled:
            srecord = adapter.submit(
                self.step, script, self.workspace.value)
        else:
            self.mark_running()
            ladapter = ScriptAdapterFactory.get_adapter("local")()
            srecord = ladapter.submit(
                self.step, script, self.workspace.value)

        retcode = srecord.submission_code
        jobid = srecord.job_identifier
        return retcode, jobid

    def mark_running(self):
        """Mark the start time of the record."""
        LOGGER.debug(
            "Marking %s as running (RUNNING) -- previously %s",
            self.name,
            self.status)
        self.status = State.RUNNING
        if not self._start_time:
            self._start_time = round_datetime_seconds(datetime.now())

    def mark_end(self, state):
        """
        Mark the end time of the record with associated termination state.
        :param state: State enum corresponding to termination state.
        """
        LOGGER.debug(
            "Marking %s as finished (%s) -- previously %s",
            self.name,
            state,
            self.status)
        self.status = state
        if not self._end_time:
            self._end_time = round_datetime_seconds(datetime.now())

    def mark_restart(self):
        """Mark the end time of the record."""
        LOGGER.debug(
            "Marking %s as restarting (TIMEOUT) -- previously %s",
            self.name,
            self.status)
        self.status = State.TIMEDOUT
        # Designating a restart limit of zero as an unlimited restart setting.
        # Otherwise, if we're less than restart limit, attempt another restart.
        if self.restart_limit == 0 or \
                self._num_restarts < self.restart_limit:
            self._num_restarts += 1
            return True
        else:
            return False

    @property
    def is_local_step(self):
        """Return whether or not this step executes locally."""
        return not self.to_be_scheduled

    @property
    def elapsed_time(self):
        """Compute the elapsed time of the record (includes queue wait)."""
        if self._submit_time and self._end_time:
            # Return the total elapsed time.
            return get_duration(self._end_time - self._submit_time)
        elif self._submit_time and self.status == State.RUNNING:
            # Return the current elapsed time.
            return get_duration(datetime.now() - self._submit_time)
        else:
            return "--:--:--"

    @property
    def run_time(self):
        """
        Compute the run time of a record (includes restart queue time).
        :returns: A string of the records's run time.
        """
        if self._start_time and self._end_time:
            # If start and end time is set -- calculate run time.
            return get_duration(self._end_time - self._start_time)
        elif self._start_time and not self.status == State.RUNNING:
            # If start time but no end time, calculate current duration.
            return get_duration(datetime.now() - self._start_time)
        else:
            # Otherwise, return an uncalculated marker.
            return "--:--:--"

    @property
    def name(self):
        """
        Get the name of the step represented by the record instance.
        :returns: The name of the StudyStep contained within the record.
        """
        return self.step.real_name

    @property
    def walltime(self):
        """
        Get the requested wall time of the record instance.
        :returns: A string representing the requested computing time.
        """
        return self.step["walltime"]

    @property
    def time_submitted(self):
        """
        Get the time the step started.
        :returns: A formatted string of the date and time the step started.
        """
        if self._submit_time:
            return str(self._submit_time)
        else:
            return "--"

    @property
    def time_start(self):
        """
        Get the time the step started.
        :returns: A formatted string of the date and time the step started.
        """
        if self._start_time:
            return str(self._start_time)
        else:
            return "--"

    @property
    def time_end(self):
        """
        Get the time the step ended.
        :returns: A formatted string of the date and time the step ended.
        """
        if self._end_time:
            return str(self._end_time)
        else:
            return "--"

    @property
    def restarts(self):
        """
        Get the number of restarts the step has executed.
        :returns: An int representing the number of restarts.
        """
        return self._num_restarts


class Step:
    """
    This class provides an abstraction for an execution step, which can be
    executed by calling execute.
    """

    def __init__(self, maestro_step_record):
        """
        :param maestro_step_record: The StepRecord object.
        """
        self.mstep = maestro_step_record
        self.restart = False

    def get_cmd(self):
        """
        get the run command text body"
        """
        return self.mstep.step.__dict__["run"]["cmd"]

    def get_restart_cmd(self):
        """
        get the restart command text body, else return None"
        """
        return self.mstep.step.__dict__["run"]["restart"]

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
        step_dict = deepcopy(self.mstep.step.__dict__)

        if new_cmd is not None:
            step_dict["run"]["cmd"] = new_cmd

        if cmd_replacement_pairs is not None:
            for str1, str2 in cmd_replacement_pairs:
                cmd = step_dict["run"]["cmd"]
                step_dict["run"]["cmd"] = re.sub(re.escape(str1), str2, cmd, flags=re.I)

                restart_cmd = step_dict["run"]["restart"]
                if restart_cmd:
                    step_dict["run"]["restart"] = re.sub(
                        re.escape(str1), str2, restart_cmd, flags=re.I
                    )

        if new_workspace is None:
            new_workspace = self.get_workspace()
        LOG.debug(f"cloned step with workspace {new_workspace}")
        study_step = StudyStep()
        study_step.name = step_dict["name"]
        study_step.description = step_dict["description"]
        study_step.run = step_dict["run"]
        return Step(MerlinStepRecord(new_workspace, study_step))

    def get_task_queue(self):
        """ Retrieve the task queue for the Step."""
        return self.get_task_queue_from_dict(self.mstep.step.__dict__)

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
        return self.mstep.step.__dict__["run"]["max_retries"]

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

    def needs_merlin_expansion(self, labels):
        """
        :return : True if the cmd has any of the default keywords or spec
            specified sample column labels.
        """
        needs_expansion = False

        cmd = self.get_cmd()
        for label in labels + [
            "MERLIN_SAMPLE_ID",
            "MERLIN_SAMPLE_PATH",
            "merlin_sample_id",
            "merlin_sample_path",
        ]:
            if f"$({label})" in cmd:
                needs_expansion = True

        # The restart may need expansion while the cmd does not.
        restart_cmd = self.get_restart_cmd()
        if not needs_expansion and restart_cmd:
            for label in labels + [
                "MERLIN_SAMPLE_ID",
                "MERLIN_SAMPLE_PATH",
                "merlin_sample_id",
                "merlin_sample_path",
            ]:
                if f"$({label})" in restart_cmd:
                    needs_expansion = True

        return needs_expansion

    def get_workspace(self):
        """
        :return : The workspace this step is to be executed in.
        """
        return self.mstep.workspace.value

    def name(self):
        """
        :return : The step name.
        """
        return self.mstep.step.__dict__["name"]

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
        default_shell = adapter_config.pop("shell")
        shell = self.mstep.step["run"].pop("shell", default_shell)
        adapter_config.update({"shell": shell})

        # Update batch type if the task overrides the default value from the batch section
        default_batch_type = adapter_config.pop("batch_type", adapter_config["type"])
        # Set batch_type to default if unset
        adapter_config.update({"batch_type": default_batch_type})
        # Override the default batch: type: from the step config
        batch = self.mstep.step.run.pop("batch", None)
        if batch:
            batch_type = batch.pop("type", default_batch_type)
            adapter_config.update({"batch_type": batch_type})

        adapter = cls_adapter(**adapter_config)
        LOG.debug(f"Maestro step config = {adapter_config}")

        # Preserve the default shell if the step shell is different
        adapter_config.update({"shell": default_shell})
        # Preserve the default batch type if the step batch type is different
        adapter_config.update({"batch_type": default_batch_type})

        self.mstep.setup_workspace()
        self.mstep.generate_script(adapter)
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
            return ReturnCode(self.mstep.restart(adapter))
        else:
            return ReturnCode(self.mstep.execute(adapter))
