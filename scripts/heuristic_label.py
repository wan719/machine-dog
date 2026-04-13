from pathlib import Path
import argparse


def label_points(lines):
    labels = []
    for line in lines:
        parts = line.strip().split()
        if len(parts) < 3:
            continue
        try:
            z = float(parts[2])
        except ValueError:
            continue
        label = 1 if z < 0.15 else 3
        labels.append(str(label))
    return labels


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()

    in_dir = Path(args.input)
    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)

    for pcd in in_dir.glob('*.pcd'):
        lines = pcd.read_text(encoding='utf-8').splitlines()
        labels = label_points(lines)
        (out_dir / (pcd.stem + '.labels')).write_text('\n'.join(labels), encoding='utf-8')
        print(f'[OK] labeled: {pcd.name}')


if __name__ == '__main__':
    main()
