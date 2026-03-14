"""File writer with overwrite guard."""
import pathlib
from typing import Optional

import typer
from rich.console import Console

console = Console()


def write_file(
    filename: str,
    content: str,
    *,
    force: bool = False,
    output_path: Optional[pathlib.Path] = None,
) -> None:
    """Write content to output_path (or cwd/filename if not given).

    If the file already exists and force is False and no output_path was
    provided (i.e. the interactive UI didn't already confirm), prompt the
    user before overwriting.
    """
    path = output_path if output_path is not None else pathlib.Path.cwd() / filename

    if path.exists() and not force and output_path is None:
        typer.confirm(f"{path.name} already exists. Overwrite?", abort=True)

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    console.print(f"[green]Written:[/green] {path}")
