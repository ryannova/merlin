import click

from merlin.cli.custom import OptionEatAll


@click.command()
@click.argument(
    "specification", type=click.Path(exists=True)
)  # , help="Path to workflow specification yaml file")
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
    help="The specific steps in the YAML file you want workers for",
)
@click.option("--worker-args", default="", help="celery worker arguments in quotes.")
def cli(specification, vars, steps, worker_args):
    """
    Run the workers associated with a Merlin YAML study
    specification. Does -not- queue tasks, just launches
    workers tied to the correct queues.
    """
    print(f"run spec at {specification}.")
