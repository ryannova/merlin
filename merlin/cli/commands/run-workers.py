from types import SimpleNamespace

import click

from merlin import router
from merlin.ascii_art import banner_small
from merlin.cli.custom import OptionEatAll
from merlin.cli.utils import get_merlin_spec_with_override


@click.command()
@click.argument(
    "specification", type=click.Path(exists=True)
)  # , help="Path to workflow specification yaml file")
@click.option(
    "--vars",
    cls=OptionEatAll,
    default=None,
    help="Specify desired Merlin variable values to override those found in the specification. Space-delimited. "
    "Example: '--vars LEARN=path/to/new_learn.py EPOCHS=3'",
)
@click.option(
    "--worker-args",
    type=str,
    required=False,
    default="",
    help="celery worker arguments in quotes.",
)
@click.option(
    "--echo",
    is_flag=True,
    required=False,
    default=False,
    help="Just echo the command; do not actually run it",
)
@click.option(
    "--steps",
    cls=OptionEatAll,
    default=["all"],
    help="The specific steps in the YAML file you want workers for",
)
@click.option("--worker-args", default="", help="celery worker arguments in quotes.")
def cli(specification, vars, steps, worker_args, echo):
    """
    Run the workers associated with a Merlin YAML study
    specification. Does -not- queue tasks, just launches
    workers tied to the correct queues.
    """
    if not echo:
        print(banner_small)
    args = SimpleNamespace(
        **{
            "specification": specification,
            "variables": vars,
            "steps": steps,
            "worker_args": worker_args,
            "echo": echo,
        }
    )
    spec, filepath = get_merlin_spec_with_override(args)
    if not echo:
        pass
        # LOG.info(f"Launching workers from '{filepath}'")
    status = router.launch_workers(spec, steps, worker_args, echo)
    if echo:
        print(status)
    else:
        pass
        # LOG.debug(f"celery command: {status}")
