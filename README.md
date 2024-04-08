# Downloads Cleanup

A Python utility for organizing and cleaning up your downloads directory.

## Overview

This utility supports various strategies for handling files, including overwrite, rename, skip, and raise exceptions based on file existence.

## Usage

To use this utility, first ensure you setup your config file:

```bash
cp example.cleanup.config.json cleanup.config.json
notepad cleanup.config.json
```

Then you can run the script:

```bash
python cleanup.py --help
```

The `--data` argument expects a JSON file produced by running [Get-ChildKinds](https://github.com/DJStompZone/DownloadsCleanup/blob/main/Get-ChildKinds.ps1)

This Cmdlet can be used to generate a list of all files in a given directory along with each file's associated `kind` property, like so:

```ps1
Get-ChildKinds -DirectoryPath "~\Downloads\" -OutputType "json" | Out-File -FilePath ./DownloadKinds.json -Encoding utf8
```
