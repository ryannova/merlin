import click

from merlin.cli.custom import OptionEatAll


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
def cli(spec, steps, queues, workers, task_server):
    """
    Attempt to stop task server workers. Defaults to all workers.
    """
    print(f"run spec at {specification}.")
