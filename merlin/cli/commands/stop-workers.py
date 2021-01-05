import click

from merlin import router
from merlin.ascii_art import banner_small
from merlin.cli.custom import OptionEatAll
from merlin.spec.specification import MerlinSpec


@click.command()
@click.option(
    "--spec", type=click.Path(exists=True), default=None
)
@click.option(
    "--steps",
    cls=OptionEatAll,
    default=["all"],
    help="The specific steps in the YAML file from which you want to purge the queues. The input is a space-separated list.",
)
@click.option("--queues", type=str, default=None, help="specific queues to stop")
@click.option("--workers", type=str, default=None, help="regex match for specfic workers to stop")
@click.option(
    "--task_server",
    required=False,
    default="celery",
    type=click.Choice(["celery"], case_sensitive=False),
    help="Task server type.",
)
def cli(spec, steps, queues, workers, task_server):
    """
    Attempt to stop task server workers. Defaults to all workers.
    """
    print(banner_small)
    worker_names = []
    if spec:
        spec = MerlinSpec.load_specification(spec)
        worker_names = spec.get_worker_names()
        for worker_name in worker_names:
            if "$" in worker_name:
                pass
                #LOG.warning(
                #    f"Worker '{worker_name}' is unexpanded. Target provenance spec instead?"
                #)
    router.stop_workers(task_server, worker_names, queues, workers)
