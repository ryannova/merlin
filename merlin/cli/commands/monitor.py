import click
import time
from types import SimpleNamespace

from merlin import router
from merlin.cli.utils import OptionEatAll
from merlin.cli.utils import get_merlin_spec_with_override

@click.command()
@click.argument(
    "specification", type=click.Path(exists=True)
)
@click.option(
    "--vars",
    cls=OptionEatAll,
    default=None,
    help="Specify desired Merlin variable values to override those found in the specification. Space-delimited. "
    "Example: '--vars LEARN=path/to/new_learn.py EPOCHS=3'",
)
@click.option(
    "--steps",
    cls=OptionEatAll,
    default=["all"],
    help="The specific steps in the YAML file you want to monitor",
)
@click.option(
    "--sleep",
    type=int,
    default=60,help="Sleep duration between checking for workers.")
@click.option(
    "--task_server",
    required=False,
    default="celery",
    type=click.Choice(["celery"], case_sensitive=False),
    help="Task server type.",
)
def cli(specification, vars, steps, sleep, task_server):
    """
    Check for active workers on an allocation.
    """
    print("Monitor: checking queues ...")
    args = SimpleNamespace(**{"specification": specification, "variables": vars, "sleep": sleep, "task_server": task_server, "steps": steps})
    spec, _ = get_merlin_spec_with_override(args)
    while router.check_merlin_status(args, spec):
        LOG.info("Monitor: found tasks in queues")
        time.sleep(sleep)
    print("Monitor: ... stop condition met")
