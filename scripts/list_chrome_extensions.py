#!/usr/bin/env python3
"""List extensions installed in a Chrome/Chrome Dev profile. Reads from disk, no browser launch."""

import argparse
import sys
from pathlib import Path

# Allow running without install: add src to path when executed as script
if __name__ == "__main__":
    _root = Path(__file__).resolve().parent.parent
    _src = _root / "src"
    if str(_src) not in sys.path:
        sys.path.insert(0, str(_src))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="List extensions in a Chrome/Chrome Dev profile. Reads from disk; Chrome can be open."
    )
    parser.add_argument(
        "--chrome-profile",
        nargs="?",
        const="",
        default=None,
        metavar="NAME",
        help="Profile name: Default, 'Profile 1', 'Profile 2', etc. Omit for Default.",
    )
    parser.add_argument(
        "--chrome-dev",
        action="store_true",
        help="Use Chrome Dev base path. Default is stable Chrome.",
    )
    parser.add_argument(
        "--user-data-dir",
        metavar="PATH",
        help="Full path to Chrome 'User Data' folder (overrides base). E.g. ...\\Chrome Dev\\User Data",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show description and extension ID.",
    )
    args = parser.parse_args()

    from automation_intelligence.config.settings import (
        CHROME_DEV_USER_DATA_DEFAULT,
        CHROME_USER_DATA_DEFAULT,
    )
    from automation_intelligence.browser.extensions import list_profile_extensions

    if args.user_data_dir is not None:
        user_data_dir = args.user_data_dir
        profile_directory = args.chrome_profile if args.chrome_profile else "Default"
    elif args.chrome_profile is not None:
        base = CHROME_DEV_USER_DATA_DEFAULT if args.chrome_dev else CHROME_USER_DATA_DEFAULT
        user_data_dir = str(base)
        profile_directory = args.chrome_profile if args.chrome_profile else "Default"
    else:
        base = CHROME_DEV_USER_DATA_DEFAULT if args.chrome_dev else CHROME_USER_DATA_DEFAULT
        user_data_dir = str(base)
        profile_directory = "Default"

    extensions = list_profile_extensions(user_data_dir, profile_directory)
    if not extensions:
        print("No extensions found or profile path invalid.")
        print(f"  Profile: {user_data_dir} / {profile_directory}")
        sys.exit(1)

    print(f"Profile: {user_data_dir} / {profile_directory}")
    print(f"Extensions: {len(extensions)}")
    print()
    for ext in extensions:
        if args.verbose:
            print(f"  {ext['name']}  v{ext['version']}")
            print(f"    id: {ext['extension_id']}")
            if ext.get("description"):
                print(f"    {ext['description'][:80]}{'...' if len(ext.get('description', '')) > 80 else ''}")
            print()
        else:
            print(f"  {ext['name']}  v{ext['version']}")


if __name__ == "__main__":
    main()
