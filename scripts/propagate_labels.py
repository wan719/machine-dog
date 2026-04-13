from pathlib import Path
import argparse


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', required=True)
    parser.add_argument('--target', required=True)
    args = parser.parse_args()

    src = Path(args.source)
    tgt = Path(args.target)
    tgt.mkdir(parents=True, exist_ok=True)

    for label_file in src.glob('*.labels'):
        (tgt / label_file.name).write_text(label_file.read_text(encoding='utf-8'), encoding='utf-8')
        print(f'[OK] propagated: {label_file.name}')


if __name__ == '__main__':
    main()
