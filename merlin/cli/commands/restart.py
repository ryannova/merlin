import click


@click.command()
@click.argument(
    "restart_dir", type=click.Path(exists=True)
)  # , help="Path to workflow specification yaml file")
@click.option(
    "--local",
    is_flag=True,
    required=False,
    default=False,
    help="Run tasks locally, without distributed workers",
)
def cli(restart_dir, local):
    """
    Restart a workflow using an existing Merlin workspace.
    """
    print(f"restart at {restart_dir}. local={local}")
