import click

from merlin.ascii_art import banner_small
from merlin.examples.generator import list_examples, setup_example


@click.command()
@click.argument("workflow", type=str)
@click.option(
    "-p",
    "--path",
    type=click.Path(exists=True),
    default=None,
    help="Specify a path to write the workflow to. Defaults to current working directory",
)
def cli(workflow, path):
    """
    Generate an example merlin workflow. Use 'merlin example list' to see available options.
    """
    if workflow == "list":
        print(list_examples())
    else:
        print(banner_small)
        setup_example(workflow, path)
