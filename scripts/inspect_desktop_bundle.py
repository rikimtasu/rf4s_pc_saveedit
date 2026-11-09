"""Report compressed and unpacked sizes in a PyInstaller desktop executable."""
import argparse
from collections import defaultdict
from PyInstaller.archive.readers import CArchiveReader


def group(name):
    name = name.replace('\\', '/')
    for prefix, label in [('PySide6/qml/', 'QML'), ('PySide6/plugins/', 'Qt plugins'), ('PySide6/translations/', 'Qt translations'), ('PySide6/resources/', 'Qt resources'), ('web/', 'Save logic / references')]:
        if name.startswith(prefix):
            return label
    return 'Other runtime'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('executable')
    args = parser.parse_args()
    archive = CArchiveReader(args.executable)
    totals = defaultdict(lambda: [0, 0, 0])
    for name, entry in archive.toc.items():
        sizes = totals[group(name)]
        sizes[0] += entry[1]
        sizes[1] += entry[2]
        sizes[2] += 1
    print('Group: compressed MiB / unpacked MiB / files')
    for name, sizes in sorted(totals.items(), key=lambda entry: -entry[1][0]):
        print(f'{name}: {sizes[0] / 1048576:.2f} / {sizes[1] / 1048576:.2f} / {sizes[2]}')
    print('\nLargest entries: compressed MiB / unpacked MiB / path')
    for name, entry in sorted(archive.toc.items(), key=lambda entry: -entry[1][1])[:30]:
        print(f'{entry[1] / 1048576:7.2f} / {entry[2] / 1048576:7.2f} / {name}')


if __name__ == '__main__':
    main()
