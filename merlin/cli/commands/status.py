import click
from types import SimpleNamespace

from merlin import router
from merlin.ascii_art import banner_small
from merlin.cli.custom import OptionEatAll
from merlin.cli.utils import get_merlin_spec_with_override


@click.command()
@click.argument(
    "specification", type=click.Path(exists=True)
)
@click.option(
    "--steps",
    cls=OptionEatAll,
    default=["all"],
    help="The specific steps in the YAML file you want to query. The input is a space-separated list.",
)
@click.option(
    "--task_server",
    required=False,
    default="celery",
    type=click.Choice(["celery"], case_sensitive=False),
    help="Task server type.",
)
@click.option(
    "--vars",
    cls=OptionEatAll,
    default=None,
    help="Specify desired Merlin variable values to override those found in the specification. Space-delimited. "
    "Example: '--vars LEARN=path/to/new_learn.py EPOCHS=3'",
)
@click.option(
    "--csv",
    type=str,
    default=None,
    help="csv file to dump status report to",
)
def cli(specification, vars, steps, task_server, csv):
    """
    List server stats (name, number of tasks to do,
    number of connected workers) for a workflow spec.
    """
    print(banner_small)
    args = SimpleNamespace(**{"specification": specification, "variables": vars, "task_server": task_server, "steps": steps, "csv": csv})
    spec, _ = get_merlin_spec_with_override(args)
    ret = router.query_status(task_server, spec, steps)
    for name, jobs, consumers in ret:
        print(f"{name:30} - Workers: {consumers:10} - Queued Tasks: {jobs:10}")
    if csv is not None:
        router.dump_status(ret, csv)
