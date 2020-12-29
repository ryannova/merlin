import click

from merlin.merlin_click.merlin_click import OptionEatAll


@click.command()
@click.argument(
    "--spec", type=click.Path(exists=True)
)
@click.option(
    "--steps",
    cls=OptionEatAll,
    default=["all"],
    help="The specific steps in the YAML file from which you want to purge the queues. The input is a space-separated list.",
)
@click.option("--queues", type=str, default=None, help="specific queues to stop")
@click.option("--workers", type=str, default=None, help="regex match for specfic workers to stop")
@click.option(
    "--task_server",
    required=False,
    default="celery",
    type=click.Choice(["celery"], case_sensitive=False),
    help="Task server type.",
)
def cli(specification, vars, steps, worker_args):
    """
    Remove all tasks from all merlin queues (default).
    If a user would like to purge only selected queues use:
    --steps to give a steplist, the queues will be defined from the step list
    """
    print(f"run spec at {specification}.")
