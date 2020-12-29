import click

from merlin.merlin_click.merlin_click import OptionEatAll


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
    print(f"status")
