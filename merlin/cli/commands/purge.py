import click
from types import SimpleNamespace

from merlin import router
from merlin.ascii_art import banner_small
from merlin.cli.utils import OptionEatAll
from merlin.cli.utils import get_merlin_spec_with_override

@click.command()
@click.argument(
    "specification", type=click.Path(exists=True)
)
@click.option("-f", "--force", is_flag=True, default=False, help="Purge the tasks without confirmation")
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
    help="The specific steps in the YAML file from which you want to purge the queues. The input is a space-separated list.",
)
@click.option("--worker-args", default="", help="celery worker arguments in quotes.")
def cli(specification, force, vars, steps, worker_args):
    """
    Remove all tasks from all merlin queues (default).
    If a user would like to purge only selected queues use:
    --steps to give a steplist, the queues will be defined from the step list
    """
    print(banner_small)
    args = SimpleNamespace(**{"specification": specification, "variables": vars, "steps": steps})
    spec, _ = get_merlin_spec_with_override(args)
    ret = router.purge_tasks(
        spec.merlin["resources"]["task_server"],
        spec,
        force,
        steps,
    )

    #LOG.info(f"Purge return = {ret} .")
