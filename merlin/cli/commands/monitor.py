import click

from merlin.cli.custom import OptionEatAll

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
    print("monitor command")
