#!/usr/bin/env python3

import argparse
import os
import subprocess
from pathlib import Path


def upload_file(local_file: str, host: str, username: str, key_path: str, remote_dir: str):
    if not os.path.exists(local_file):
        raise FileNotFoundError(local_file)

    cmd = [
        "scp",
        "-i", key_path,
        "-o", "StrictHostKeyChecking=no",
        local_file,
        f"{username}@{host}:{remote_dir}/",
    ]
    subprocess.run(cmd, check=True)
    print(f"Uploaded {local_file} -> {username}@{host}:{remote_dir}")


def main():
    parser = argparse.ArgumentParser(description="Upload downloaded MP3s to the Oracle Cloud host")
    parser.add_argument("--file", required=True)
    parser.add_argument("--host", required=True)
    parser.add_argument("--user", required=True)
    parser.add_argument("--key", required=True)
    parser.add_argument("--remote-dir", required=True, default="/home/ubuntu/media/music")
    args = parser.parse_args()

    upload_file(args.file, args.host, args.user, args.key, args.remote_dir)


if __name__ == "__main__":
    main()
