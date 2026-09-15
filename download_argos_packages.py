#!/usr/bin/env python3
"""Download and install every official Argos Translate language package."""
import sys
import time
import traceback

import argos_setup
from argostranslate import package


def _already_installed():
    installed = set()
    for pkg in package.get_installed_packages():
        installed.add((pkg.from_code, pkg.to_code, getattr(pkg, "type", "translate")))
    return installed


def _install_with_retry(available_package, attempts=3):
    last_error = None
    for attempt in range(1, attempts + 1):
        try:
            available_package.install()
            return
        except Exception as err:
            last_error = err
            print("  attempt {} failed: {}".format(attempt, err))
            if attempt < attempts:
                time.sleep(2 * attempt)
    raise last_error


def main():
    print("Installing Argos Translate packages into {}".format(
        argos_setup.PACKAGES_DIR))
    package.update_package_index()
    available_packages = package.get_available_packages()
    installed = _already_installed()
    to_install = [
        pkg for pkg in available_packages
        if (pkg.from_code, pkg.to_code, getattr(pkg, "type", "translate"))
        not in installed
    ]

    print("{} official packages, {} already installed, {} to download".format(
        len(available_packages), len(installed), len(to_install)))

    failed = []
    for i, pkg in enumerate(to_install, 1):
        print("[{}/{}] {} ({} -> {})".format(
            i, len(to_install), pkg, pkg.from_code, pkg.to_code),
              flush=True)
        try:
            _install_with_retry(pkg)
        except Exception:
            traceback.print_exc()
            failed.append(pkg)

    installed_after = _already_installed()
    print("Installed {} packages in {}".format(
        len(installed_after), argos_setup.PACKAGES_DIR))
    if failed:
        print("Failed to install {} package(s):".format(len(failed)))
        for pkg in failed:
            print("  {} ({} -> {})".format(pkg, pkg.from_code, pkg.to_code))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
