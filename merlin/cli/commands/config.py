import os

import click

from merlin import router
from merlin.cli.utils import OptionEatAll


@click.command()
@click.option(
    "-o",
    "--output_dir",
    type=str,
    default=None,
    help="Optional directory to place the default config file.\nDefault: ~/.merlin",
)
@click.option(
    "--task_server",
    required=False,
    default="celery",
    type=click.Choice(["celery"], case_sensitive=False),
    help="Task server type.",
)
@click.option(
    "--broker",
    type=click.Choice(["rabbitmq", "redis"], case_sensitive=False),
    default="rabbitmq",
    help="Optional broker type, backend will be redis\nDefault: rabbitmq",
)
def cli(
    output_dir,
    task_server,
    broker,
):
    """
    Create a default merlin server config file in ~/.merlin.
    """
    if output_dir is None:
        user_home = os.path.expanduser("~")
        output_dir = os.path.join(user_home, ".merlin")
    _ = router.create_config(task_server, output_dir, broker)
