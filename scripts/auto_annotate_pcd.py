from pathlib import Path
import argparse
import json
import numpy as np
import open3d as o3d

LABELS = {
    0: {"name": "unknown", "color": [0.5, 0.5, 0.5]},
    1: {"name": "ground", "color": [0.0, 0.8, 0.0]},
    2: {"name": "wall", "color": [0.0, 0.2, 1.0]},
    3: {"name": "obstacle", "color": [1.0, 0.0, 0.0]},
    5: {"name": "robot_self", "color": [1.0, 1.0, 0.0]},
}


def ensure_dir(path: Path):
    path.mkdir(parents=True, exist_ok=True)


def label_one_cloud(pcd: o3d.geometry.PointCloud, ground_dist: float, robot_radius: float):
    points = np.asarray(pcd.points)
    labels = np.zeros(len(points), dtype=np.int32)

    if len(points) == 0:
        return labels, pcd

    # 1. robot self: near lidar origin
    xy_dist = np.linalg.norm(points[:, :2], axis=1)
    labels[xy_dist < robot_radius] = 5

    # 2. ground plane by RANSAC
    remaining_idx = np.where(labels == 0)[0]
    if len(remaining_idx) >= 30:
        remain_cloud = pcd.select_by_index(remaining_idx.tolist())
        try:
            plane_model, inliers = remain_cloud.segment_plane(
                distance_threshold=ground_dist,
                ransac_n=3,
                num_iterations=1000,
            )
            normal = np.asarray(plane_model[:3], dtype=float)
            normal = normal / (np.linalg.norm(normal) + 1e-9)
            # ground plane normal should be close to z-axis
            if abs(normal[2]) > 0.75:
                ground_global_idx = remaining_idx[np.asarray(inliers, dtype=int)]
                labels[ground_global_idx] = 1
        except RuntimeError:
            pass

    # 3. wall-like points: high vertical structures, simple fallback by height
    unlabeled = labels == 0
    z = points[:, 2]
    labels[unlabeled & (z > 1.2)] = 2

    # 4. remaining non-ground structures are obstacles
    labels[labels == 0] = 3

    colored = o3d.geometry.PointCloud()
    colored.points = o3d.utility.Vector3dVector(points)
    colors = np.array([LABELS[int(v)]["color"] for v in labels], dtype=float)
    colored.colors = o3d.utility.Vector3dVector(colors)
    return labels, colored


def write_labels(path: Path, labels: np.ndarray):
    path.write_text("\n".join(str(int(x)) for x in labels), encoding="utf-8")


def save_screenshot(pcd: o3d.geometry.PointCloud, out_path: Path, width=1280, height=720):
    vis = o3d.visualization.Visualizer()
    vis.create_window(visible=False, width=width, height=height)
    vis.add_geometry(pcd)
    ctr = vis.get_view_control()
    ctr.set_zoom(0.7)
    vis.poll_events()
    vis.update_renderer()
    vis.capture_screen_image(str(out_path), do_render=True)
    vis.destroy_window()


def main():
    parser = argparse.ArgumentParser(description="Auto annotate all .pcd files and export colored visualization.")
    parser.add_argument("--input", required=True, help="Input folder containing .pcd files")
    parser.add_argument("--output", required=True, help="Output folder")
    parser.add_argument("--ground-dist", type=float, default=0.08, help="RANSAC ground distance threshold")
    parser.add_argument("--robot-radius", type=float, default=0.35, help="Near-origin radius for robot self points")
    parser.add_argument("--screenshot", action="store_true", help="Save PNG screenshots")
    args = parser.parse_args()

    input_dir = Path(args.input)
    output_dir = Path(args.output)
    labels_dir = output_dir / "labels"
    colored_dir = output_dir / "colored_pcd"
    screenshots_dir = output_dir / "screenshots"
    ensure_dir(labels_dir)
    ensure_dir(colored_dir)
    if args.screenshot:
        ensure_dir(screenshots_dir)

    pcd_files = sorted(input_dir.glob("*.pcd"))
    if not pcd_files:
        raise FileNotFoundError(f"No .pcd files found in {input_dir}")

    summary = []
    for pcd_path in pcd_files:
        pcd = o3d.io.read_point_cloud(str(pcd_path))
        labels, colored = label_one_cloud(pcd, args.ground_dist, args.robot_radius)

        label_path = labels_dir / f"{pcd_path.stem}.labels"
        colored_path = colored_dir / f"{pcd_path.stem}_annotated.ply"
        write_labels(label_path, labels)
        o3d.io.write_point_cloud(str(colored_path), colored)

        if args.screenshot:
            save_screenshot(colored, screenshots_dir / f"{pcd_path.stem}_annotated.png")

        counts = {LABELS[k]["name"]: int(np.sum(labels == k)) for k in LABELS}
        summary.append({"frame": pcd_path.name, "points": int(len(labels)), "counts": counts})
        print(f"[OK] {pcd_path.name}: {counts}")

    (output_dir / "annotation_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"[DONE] annotated {len(pcd_files)} frames -> {output_dir}")


if __name__ == "__main__":
    main()
