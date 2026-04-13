# CloudCompare 标注流程

1. 导入连续 `.pcd` 点云帧
2. 使用 Segment 工具分割目标区域
3. 使用 unique color 对不同类别染色
4. 导出修正后的关键帧
5. 配合 Python 脚本生成 labels
