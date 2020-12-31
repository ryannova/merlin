import click


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
    print(f"task server = {task_server}.")
