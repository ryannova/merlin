import click

from merlin import router
from merlin.ascii_art import banner_small


@click.command()
@click.option(
    "--task_server",
    required=False,
    default="celery",
    type=click.Choice(["celery"], case_sensitive=False),
    help="Task server type.",
)
def cli(task_server):
    """
    List connected task server workers.
    """
    print(banner_small)
    router.query_workers(task_server)
