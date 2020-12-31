import click

from merlin.cli.custom import OptionEatAll


@click.command()
@click.option(
    "-o", "--output_dir", type=str, default=None,
    help="Optional directory to place the default config file.\nDefault: ~/.merlin")
@click.option(
    "--task_server",
    required=False,
    default="celery",
    type=click.Choice(["celery"], case_sensitive=False),
    help="Task server type.",
)
@click.option(
    "--broker", type=click.Choice(["rabbitmq", "redis"], case_sensitive=False), default="rabbitmq",
    help="Optional broker type, backend will be redis\nDefault: rabbitmq")
def cli(
    output_dir,
    task_server,
    broker,
):
    """
    Create a default merlin server config file in ~/.merlin.
    """
    print(f"config")
