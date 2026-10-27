# 环境和渲染注意点

参考工程已在Python3.12／Manim Community0.22.0与FFmpeg／ffprobe下验证。优先使用已有Manim环境；不要假设系统默认Python已安装Manim。Windows中文字体可用Microsoft YaHei，其他系统需选择已安装的中文字体。公式可用Text，无需LaTeX。下方`python`应替换为当前Manim环境的解释器。

```powershell
python -m manim render -qh --fps 30 --renderer=cairo scene.py SceneClass
```

曾出现嵌套组改变子对象数量后，模型正确但部分标签未显示、包围盒异常导致连线偏移。复杂节点变更采用已验证方式：

1. 新建规范VGroup，动画目标使用它的副本。
2. ReplacementTransform替换整节点；结束移除动画目标，加入未参与形变的规范节点，更新引用，确保它是顶层场景对象。
3. 数据行来源提示用独立SurroundingRectangle＋ShowPassingFlash，不直接改变持久数据子对象。
4. 父子线用固定布局锚点／已知节点高度，避免读临时形变包围盒。

只在相应复杂组场景使用，不给普通对象强加固定动作。实现见`../assets/h2h_reference/scene_upward_labels.py`的PersistentTree。始终先复制参考工程到任务目录，不能在技能资产中生成视频或改文件。

Manim拼接曾出现一个重复时间戳。`../scripts/export_verify.py`用恒定帧率导出，再全片解码并查媒体流、抽实际帧。只读ffprobe元数据不足以证明可正常播放。

该导出脚本只需Python标准库和FFmpeg／ffprobe，不依赖Git Bash。参考专项检查脚本额外用Pillow生成接触表，现有Manim环境已包含Pillow。
