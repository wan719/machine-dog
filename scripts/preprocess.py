from pathlib import Path
import argparse


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()

    in_dir = Path(args.input)
    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)

    for pcd in in_dir.glob('*.pcd'):
        target = out_dir / pcd.name
        target.write_text(pcd.read_text(encoding='utf-8'), encoding='utf-8')
        print(f'[OK] preprocessed: {pcd.name}')


if __name__ == '__main__':
    main()
