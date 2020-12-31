import click

from merlin.cli.custom import OptionEatAll


@click.command()
@click.argument(
    "specification", type=click.Path(exists=True)
)
@click.option(
    "--local",
    is_flag=True,
    required=False,
    default=False,
    help="Run tasks locally, without distributed workers",
)
@click.option(
    "--level",
    required=False,
    default="info",
    type=click.Choice(["debug", "info"], case_sensitive=False),
)
@click.option(
    "--vars",
    cls=OptionEatAll,
    default=None,
    help="Specify desired Merlin variable values to override those found in the specification. Space-delimited. "
    "Example: '--vars LEARN=path/to/new_learn.py EPOCHS=3'",
)
@click.option(
    "--task_server",
    required=False,
    default="celery",
    type=click.Choice(["celery"], case_sensitive=False),
    help="Task server type.",
)
@click.option(
    "--samplesfile",
    type=click.Path(exists=True),
    required=False,
    default=None,
    help="Specify file containing samples instead of generating one at start of workflow. Valid choices: TODO",
)
@click.option("--dry", is_flag=True, default=False, required=False, help="")
@click.option(
    "--no-errors",
    is_flag=True,
    default=False,
    required=False,
    help="Flag to ignore some flux errors for testing (often used with --dry --local).",
)
@click.option(
    "--pgen",
    type=click.Path(exists=True),
    required=False,
    help="Provide a pgen file to override global.parameters.",
)
@click.option(
    "--pargs",
    multiple=True,
    required=False,
    help="A string that represents a single argument to pass "
    "a custom parameter generation function. Reuse '--parg' "
    "to pass multiple arguments. [Use with '--pgen']",
)
def cli(
    specification,
    local,
    level,
    vars,
    task_server,
    samplesfile,
    dry,
    no_errors,
    pgen,
    pargs,
):
    """
    Queue tasks for a Merlin workflow.
    """
    print(f"run spec at {spec_path}. local={local}, level={level}")
