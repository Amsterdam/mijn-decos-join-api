# standard library
import json
import urllib.request
from collections import namedtuple
from contextlib import suppress
from distutils.version import StrictVersion
from pathlib import Path
from subprocess import check_output
from typing import Iterable, List, NamedTuple

import pkg_resources


def git_diff(cwd) -> Iterable[str]:
    """
    Run git diff in the specified directory.
    """
    return (
        check_output(["git", "diff", "requirements.txt"], cwd=cwd).decode().splitlines()
    )


class PackageChange(NamedTuple):
    package: str
    from_version: str
    to_version: str


def normalise_package_name(package_name):
    """
    Ensure we always use the same package names when parsing git diff
    sometimes a package is referred to using - and sometimes with . (I
    think depending on pip version).
    """
    data = json.load(
        urllib.request.urlopen(f"https://pypi.org/pypi/{package_name}/json")
    )
    return data["info"]["name"]


def parse_diff(diff: Iterable[str]) -> List[PackageChange]:
    """
    Parse a git diff to find changes to dependencies.

    :param diff: The output from git diff

    :return: Iterable of package changes.
    """

    def get_change_type(line):
        for char in "-+":
            # filter single line changes
            if line.startswith(char) and not line.startswith(char * 3):
                return char

    # because we are parsing from a pip-tools generated file the specifier
    # should always be of the form ==version, so we strip the first two
    # characters
    # TODO: assert this assumption
    LineChange = namedtuple("LineChange", "change_type package version")
    changes = {
        LineChange(
            change_type,
            normalise_package_name(requirement.key),
            str(requirement.specifier)[2:],
        )
        for line in diff
        if (change_type := get_change_type(line)) is not None
        if (requirement := next(pkg_resources.parse_requirements(line[1:]), None))
        is not None
    }

    def version(package, change_type):
        changes_for_this_package_of_type = (
            c.version
            for c in changes
            if c.package == package
            if c.change_type == change_type
        )
        return next(changes_for_this_package_of_type, None)

    return [
        PackageChange(package, from_version, to_version)
        for package in {c.package for c in changes}
        if (from_version := version(package, "-"))
        != (to_version := version(package, "+"))
    ]


def print_package_version_update_message(project_package_changes: List):
    """
    Create threads on slack which show the major dependency upgrades
    and the projects that are affected.
    """
    messages = []

    for package_change in project_package_changes:
        if (
            package_change.to_version is not None
            and package_change.from_version is not None
        ):
            # if one of the versions is not strict, so we can't say anything about if this is a patch
            # release or not so we just show the message to be sure
            with suppress(ValueError):
                strict_from_version = StrictVersion(package_change.from_version)
                strict_to_version = StrictVersion(package_change.to_version)
                show_message = (
                    strict_from_version.version[0] != strict_to_version.version[0]
                )

            if package_change.from_version < package_change.to_version:
                message = f"{package_change.from_version} ➩ {package_change.to_version}"
            else:
                message = f"{package_change.from_version} ➩ {package_change.to_version}"

            if show_message:
                messages.append(f"{package_change.package} | {message}")

    print("\n".join(messages))


if __name__ == "__main__":
    path = Path(__file__).parent.parent
    diff = parse_diff(git_diff(path))
    print_package_version_update_message(diff)
