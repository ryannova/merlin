import click


@click.command()
@click.argument("workflow", type=str)
@click.option("-p", "--path", type=click.Path(exists=True), default=None, help="Specify a path to write the workflow to. Defaults to current working directory")
def cli(workflow, path):
    """
    Generate an example merlin workflow. Use 'merlin example list' to see available options.
    """
    print("example command")
