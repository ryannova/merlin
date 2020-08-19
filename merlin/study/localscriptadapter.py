"""Local interface implementation."""
import logging
import os
from enum import Enum

from maestrowf.interfaces.script import CancellationRecord, SubmissionRecord

LOGGER = logging.getLogger(__name__)


class SubmissionCode(Enum):
    OK = 0
    ERROR = 1


class CancelCode(Enum):
    OK = 0
    ERROR = 1


class JobStatusCode(Enum):
    OK = 0
    NOJOBS = 1
    ERROR = 2


def start_process(cmd, cwd=None, env=None, shell=True):
    if isinstance(cmd, list):
        shell = False
    kwargs = {
        "shell": shell,
        "universal_newlines": True,
        "stdout": PIPE,
        "stderr": PIPE,
    }
    if cwd is not None:
        kwargs["cwd"] = cwd
    if env is not None:
        kwargs["env"] = env
    return Popen(cmd, **kwargs)


class LocalScriptAdapter:
    """A ScriptAdapter class for interfacing for local execution."""

    key = "local"

    def __init__(self, **kwargs):
        """
        Initialize an instance of the LocalScriptAdapter.

        The LocalScriptAdapter is the adapter that is used for workflows that
        will execute on the user's machine. The only configurable aspect to
        this adapter is the shell that scripts are executed in.

        :param **kwargs: A dictionary with default settings for the adapter.
        """
        # LOGGER.debug("kwargs\n--------------------------\n%s", kwargs)
        super(LocalScriptAdapter, self).__init__(**kwargs)

    def _write_script(self, ws_path, step):
        """
        Write a Slurm script to the workspace of a workflow step.

        The job_map optional parameter is a map of workflow step names to job
        identifiers. This parameter so far is only planned to be used when a
        study is configured to be launched in one go (more or less a script
        chain using a scheduler's dependency setting). The functionality of
        the parameter may change depending on both future intended use.

        :param ws_path: Path to the workspace directory of the step.
        :param step: An instance of a StudyStep.
        :returns: False (will not be scheduled), the path to the
            written script for run["cmd"], and the path to the script written
            for run["restart"] (if it exists).
        """
        cmd = step.run["cmd"]
        restart = step.run["restart"]
        to_be_scheduled = False

        fname = "{}.sh".format(step.name)
        script_path = os.path.join(ws_path, fname)
        with open(script_path, "w") as script:
            script.write("#!{0}\n\n{1}\n".format(self._exec, cmd))

        if restart:
            rname = "{}.restart.sh".format(step.name)
            restart_path = os.path.join(ws_path, rname)

            with open(restart_path, "w") as script:
                script.write("#!{0}\n\n{1}\n".format(self._exec, restart))
        else:
            restart_path = None

        return to_be_scheduled, script_path, restart_path

    def check_jobs(self, joblist):
        """
        For the given job list, query execution status.

        :param joblist: A list of job identifiers to be queried.
        :returns: The return code of the status query, and a dictionary of job
            identifiers to their status.
        """
        return JobStatusCode.NOJOBS, {}

    def cancel_jobs(self, joblist):
        """
        For the given job list, cancel each job.

        :param joblist: A list of job identifiers to be cancelled.
        :returns: The return code to indicate if jobs were cancelled.
        """
        return CancellationRecord(CancelCode.OK, 0)

    def submit(self, step, path, cwd, job_map=None, env=None):
        """
        Execute the step locally.

        If cwd is specified, the submit method will operate outside of the path
        specified by the 'cwd' parameter.
        If env is specified, the submit method will set the environment
        variables for submission to the specified values. The 'env' parameter
        should be a dictionary of environment variables.

        :param step: An instance of a StudyStep.
        :param path: Path to the script to be executed.
        :param cwd: Path to the current working directory.
        :param job_map: A map of workflow step names to their job identifiers.
        :param env: A dict containing a modified environment for execution.
        :returns: The return code of the submission command and job identiifer.
        """
        LOGGER.debug("cwd = %s", cwd)
        LOGGER.debug("Script to execute: %s", path)
        p = start_process(path, shell=False, cwd=cwd, env=env)
        pid = p.pid
        output, err = p.communicate()
        retcode = p.wait()

        o_path = os.path.join(cwd, "{}.{}.out".format(step.name, pid))
        e_path = os.path.join(cwd, "{}.{}.err".format(step.name, pid))

        with open(o_path, "w") as out:
            out.write(output)

        with open(e_path, "w") as out:
            out.write(err)

        if retcode == 0:
            # LOGGER.info("Execution returned status OK.")
            return SubmissionRecord(SubmissionCode.OK, retcode, pid)
        else:
            # LOGGER.warning("Execution returned an error: %s", str(err))
            _record = SubmissionRecord(SubmissionCode.ERROR, retcode, pid)
            _record.add_info("stderr", str(err))
            return _record
