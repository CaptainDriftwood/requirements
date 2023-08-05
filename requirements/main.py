import pathlib

import click

"""
Command line application to take a package name as the first argument,
and then as the second argument take a string to replace the package name
with. The last argument is optional and is the path to a directory, or an
individual file. If the last argument is not provided, then the current
working directory is used. If the last argument is a directory, then all the
files that are requirements.txt files are updated. If the last argument is a
file, then only that file is updated.
"""


def replace_file_contents(
    file_path: pathlib.Path, package_name: str, new_package_name: str, preview: bool
):
    """
    Replace the contents of a file with new contents
    """
    contents = file_path.read_text()
    contents = contents.replace(package_name, new_package_name)
    if preview:
        print(f"Previewing changes to {file_path}")
        print(contents)
    else:
        file_path.write_text(contents)
        print(f"Updated {file_path}")


@click.command()
@click.argument("package_name")
@click.argument("new_package_name")
@click.argument("paths")
@click.option("--preview", is_flag=True, help="Preview changes")
@click.version_option()
def cli(package_name, new_package_name, paths, preview: bool):
    """
    Update requirements.txt files with new package name
    """
    if preview:
        print("Previewing changes")

    paths = [pathlib.Path(*paths)]

    for path in paths:
        if path.is_dir():
            requirements_files = path.glob("**/requirements.txt")
        else:
            if path.name == "requirements.txt":
                requirements_files = []
            else:
                print(f"{paths} is not a requirements.txt file")
                exit(1)

        for requirements_file in requirements_files:
            contents = requirements_file.read_text()
            contents = contents.replace(package_name, new_package_name)
            requirements_file.write_text(contents)
            print(f"Updated {requirements_file}")


if __name__ == "__main__":
    cli()
