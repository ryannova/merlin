import os

import click

from merlin import router
from merlin.cli.custom import OptionEatAll
from merlin.cli.utils import banner_small, parse_override_vars
from merlin.study.study import MerlinStudy


@click.command()
@click.argument(
    "specification",
    type=click.Path(exists=True),
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
    default=None,
    help="Provide a pgen file to override global.parameters.",
)
@click.option(
    "--pargs",
    multiple=True,
    required=False,
    default=None,
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
    print("specification")
    print(specification)
    print("local")
    print(local)
    print("level")
    print(level)
    print("vars")
    print(vars)
    print("samplesfile")
    print(samplesfile)
    print("dry")
    print(dry)
    print("pgen")
    print(pgen)
    print("pargs")
    print(pargs)
    variables_dict = parse_override_vars(vars)

    # pgen checks
    if pargs and not pgen:
        raise ValueError(
            "Cannot use the 'pargs' parameter without specifying a 'pgen'!"
        )

    if samplesfile:
        samplesfile = os.path.abspath(samplesfile)

    run_type = "batch"
    if local:
        run_type = "local"

    study = MerlinStudy(
        os.path.abspath(specification),
        override_vars=variables_dict,
        samples_file=samplesfile,
        dry_run=dry,
        no_errors=no_errors,
        pgen_file=pgen,
        pargs=pargs,
    )
    router.run_task_server(study, run_type)
