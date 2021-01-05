import click


@click.command()
def cli():
    """
    Display info about the merlin and the python configuration. Useful for debugging.
    """
    from merlin import display
    args = None
    display.print_info(args)
