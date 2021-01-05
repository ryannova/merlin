import click
import glob
import os

from merlin import router
from merlin.ascii_art import banner_small
from merlin.cli.utils import verify_filepath
from merlin.study.study import MerlinStudy


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
    print(banner_small)
    filepath = os.path.join(restart_dir, "merlin_info", "*.expanded.yaml")
    possible_specs = glob.glob(filepath)
    if len(possible_specs) == 0:
        raise ValueError(
            f"'{filepath}' does not match any provenance spec file to restart from."
        )
    elif len(possible_specs) > 1:
        raise ValueError(
            f"'{filepath}' matches more than one provenance spec file to restart from."
        )
    filepath = verify_filepath(possible_specs[0])
    print(f"Restarting workflow at '{restart_dir}'")
    study = MerlinStudy(filepath, restart_dir=restart_dir)
    router.run_task_server(study, local)
