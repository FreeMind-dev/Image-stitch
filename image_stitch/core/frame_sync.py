"""
帧同步模块

处理多个动画图片的帧同步问题：
- 不同帧数的同步
- 不同帧时长的同步
- 静态图与动态图的同步

提供多种同步模式，默认使用简单循环模式以保证流畅播放。
"""

from enum import Enum
from dataclasses import dataclass
from typing import List, Tuple, Set
from .image_loader import ImageInfo
from ..utils.math_utils import lcm_multiple, lcm


class SyncMode(Enum):
    """
    帧同步模式

    TIME_SYNC: 基于时间的独立循环模式（默认，推荐）- 每个GIF按自己的时长独立循环
    LOOP: 简单循环模式 - 按帧索引循环，保持流畅
    LONGEST: 以最长动画为准，较短的动画循环播放
    SHORTEST: 以最短动画为准，较长的动画截断
    LCM: 使用最小公倍数，精确同步但可能产生很多帧
    """
    TIME_SYNC = "time_sync"
    LOOP = "loop"
    LONGEST = "longest"
    SHORTEST = "shortest"
    LCM = "lcm"


@dataclass
class SyncResult:
    """
    同步结果

    属性:
        frame_indices: 每帧的索引元组列表，如 [(0,0), (0,1), (1,0), ...]
                       每个元组对应各输入图像的帧索引
        durations: 每帧时长列表（毫秒）
        total_frames: 总帧数
        total_duration: 总时长（毫秒）
    """
    frame_indices: List[Tuple[int, ...]]
    durations: List[int]
    total_frames: int
    total_duration: int


class FrameSynchronizer:
    """
    帧同步器

    处理多个动画图片的帧同步，生成统一的帧序列。

    使用示例:
        >>> sync = FrameSynchronizer(mode=SyncMode.LOOP)
        >>> result = sync.sync([info1, info2, info3])
        >>> print(result.total_frames)  # 同步后的总帧数
    """

    # GIF 最小帧时长（毫秒），低于此值会导致播放卡顿
    MIN_FRAME_DURATION = 20

    def __init__(self, mode: SyncMode = SyncMode.TIME_SYNC, max_frames: int = 300):
        """
        初始化同步器

        参数:
            mode: 同步模式，默认 TIME_SYNC（基于时间的独立循环，推荐）
            max_frames: 最大帧数限制
        """
        if max_frames < 1:
            raise ValueError("max_frames 必须大于 0")

        self.mode = mode
        self.max_frames = max_frames

    def sync(self, images: List[ImageInfo]) -> SyncResult:
        """
        同步多个图像的帧序列

        参数:
            images: ImageInfo 对象列表

        返回:
            SyncResult 对象，包含同步后的帧索引和时长
        """
        if not images:
            raise ValueError("至少需要一个图像")

        # 全部为静态图
        if all(not info.is_animated for info in images):
            return SyncResult(
                frame_indices=[tuple(0 for _ in images)],
                durations=[0],
                total_frames=1,
                total_duration=0,
            )

        # 根据模式选择同步算法
        if self.mode == SyncMode.TIME_SYNC:
            return self._sync_time_based(images)
        elif self.mode == SyncMode.LOOP:
            return self._sync_loop(images)
        elif self.mode == SyncMode.LONGEST:
            return self._sync_longest(images)
        elif self.mode == SyncMode.SHORTEST:
            return self._sync_shortest(images)
        else:  # LCM
            return self._sync_lcm(images)

    def _sync_time_based(self, images: List[ImageInfo]) -> SyncResult:
        """
        基于时间的独立循环模式（推荐）

        每个GIF按自己的总时长独立循环，输出动画总时长为最长GIF的时长。
        使用智能帧率采样，根据输出时长自动调整帧率以控制文件大小。

        优点：
        - 每个子图独立循环，互不影响
        - 使用最长时长而非LCM，大幅减少输出帧数
        - 智能帧率调整，平衡流畅度和文件大小
        """
        animated = [info for info in images if info.is_animated]
        if not animated:
            # 全部静态图，返回单帧
            return SyncResult(
                frame_indices=[tuple(0 for _ in images)],
                durations=[0],
                total_frames=1,
                total_duration=0,
            )

        # 使用最长动画的时长作为目标时长（不再使用LCM，大幅减少帧数）
        total_durations = [info.total_duration for info in animated]
        target_duration = max(total_durations)

        # 智能帧率调整：根据输出时长动态选择帧率
        # 使用10ms倍数的帧时长（GIF标准，兼容性最好）
        # 最低帧率20fps确保流畅播放
        if target_duration > 20000:  # >20秒
            frame_duration = 50   # 20fps - 最低帧率（保证基本流畅）
        elif target_duration > 10000:  # >10秒
            frame_duration = 40   # 25fps - 较流畅
        elif target_duration > 5000:  # >5秒
            frame_duration = 30   # ~33fps - 流畅
        elif target_duration > 2000:  # >2秒
            frame_duration = 30   # ~33fps - 流畅
        else:
            frame_duration = 20   # 50fps - 最流畅（短动画）

        # 计算帧数
        n_frames = max(1, target_duration // frame_duration)

        # 限制最大帧数（默认300帧，平衡流畅度和文件大小）
        # 对于较短的动画，允许更多帧以保持原始流畅度
        if target_duration <= 5000:  # ≤5秒
            max_output_frames = min(self.max_frames, 250)  # 允许50fps
        else:
            max_output_frames = min(self.max_frames, 400)  # 较长动画允许更多帧

        if n_frames > max_output_frames:
            n_frames = max_output_frames
            frame_duration = target_duration // n_frames
            # 确保帧时长是10ms的倍数（GIF标准）
            frame_duration = (frame_duration // 10) * 10
            if frame_duration < self.MIN_FRAME_DURATION:
                frame_duration = self.MIN_FRAME_DURATION

        # 确保帧时长不低于最小值
        if frame_duration < self.MIN_FRAME_DURATION:
            frame_duration = self.MIN_FRAME_DURATION
            n_frames = max(1, target_duration // frame_duration)

        # 生成帧索引：每个时间点，各GIF按 time % total_duration 独立循环
        frame_indices = []
        durations = []
        for frame_idx in range(n_frames):
            current_time = frame_idx * frame_duration
            indices = []
            for info in images:
                if info.is_animated:
                    # 独立循环：根据当前时间在该动画周期内的位置找帧
                    t = current_time % info.total_duration
                    idx = self._get_frame_at_time_from_info(info, t)
                    indices.append(idx)
                else:
                    # 静态图始终第0帧
                    indices.append(0)
            frame_indices.append(tuple(indices))
            durations.append(frame_duration)

        return SyncResult(
            frame_indices=frame_indices,
            durations=durations,
            total_frames=n_frames,
            total_duration=sum(durations),
        )

    def _sync_loop(self, images: List[ImageInfo]) -> SyncResult:
        """
        简单循环模式（推荐）

        以帧数最多的动画为基准，其他动画按帧索引循环。
        使用帧数最多的动画的帧时长。

        优点：保持原始帧率，播放流畅
        """
        # 找出帧数最多的动画
        animated_infos = [(i, info) for i, info in enumerate(images) if info.is_animated]
        if not animated_infos:
            return SyncResult(
                frame_indices=[tuple(0 for _ in images)],
                durations=[0],
                total_frames=1,
                total_duration=0,
            )

        # 以帧数最多的动画为基准
        max_frames_idx, base_info = max(animated_infos, key=lambda x: x[1].n_frames)
        n_frames = base_info.n_frames
        durations = base_info.durations.copy()

        # 生成帧索引
        frame_indices = []
        for frame_idx in range(n_frames):
            indices = []
            for i, info in enumerate(images):
                if info.is_animated:
                    # 循环取帧
                    indices.append(frame_idx % info.n_frames)
                else:
                    # 静态图始终是第 0 帧
                    indices.append(0)
            frame_indices.append(tuple(indices))

        return SyncResult(
            frame_indices=frame_indices,
            durations=durations,
            total_frames=n_frames,
            total_duration=sum(durations),
        )

    def _sync_longest(self, images: List[ImageInfo]) -> SyncResult:
        """
        最长模式

        以总时长最长的动画为基准，其他动画循环播放。
        """
        # 找出总时长最长的动画
        animated_infos = [(i, info) for i, info in enumerate(images) if info.is_animated]
        if not animated_infos:
            return self._sync_loop(images)

        max_duration_idx, base_info = max(animated_infos, key=lambda x: x[1].total_duration)
        n_frames = base_info.n_frames
        durations = base_info.durations.copy()
        total_duration = base_info.total_duration

        # 生成帧索引
        frame_indices = []
        current_time = 0
        for frame_idx in range(n_frames):
            indices = []
            for i, info in enumerate(images):
                if info.is_animated:
                    if i == max_duration_idx:
                        indices.append(frame_idx)
                    else:
                        # 根据时间找到对应帧
                        t = current_time % info.total_duration
                        idx = self._get_frame_at_time_from_info(info, t)
                        indices.append(idx)
                else:
                    indices.append(0)
            frame_indices.append(tuple(indices))
            current_time += durations[frame_idx]

        return SyncResult(
            frame_indices=frame_indices,
            durations=durations,
            total_frames=n_frames,
            total_duration=total_duration,
        )

    def _sync_shortest(self, images: List[ImageInfo]) -> SyncResult:
        """
        最短模式

        以总时长最短的动画为基准，其他动画截断。
        """
        # 找出总时长最短的动画
        animated_infos = [(i, info) for i, info in enumerate(images) if info.is_animated]
        if not animated_infos:
            return self._sync_loop(images)

        min_duration_idx, base_info = min(animated_infos, key=lambda x: x[1].total_duration)
        n_frames = base_info.n_frames
        durations = base_info.durations.copy()
        total_duration = base_info.total_duration

        # 生成帧索引
        frame_indices = []
        current_time = 0
        for frame_idx in range(n_frames):
            indices = []
            for i, info in enumerate(images):
                if info.is_animated:
                    if i == min_duration_idx:
                        indices.append(frame_idx)
                    else:
                        # 根据时间找到对应帧（不循环，直接截断）
                        t = min(current_time, info.total_duration - 1)
                        idx = self._get_frame_at_time_from_info(info, t)
                        indices.append(idx)
                else:
                    indices.append(0)
            frame_indices.append(tuple(indices))
            current_time += durations[frame_idx]

        return SyncResult(
            frame_indices=frame_indices,
            durations=durations,
            total_frames=n_frames,
            total_duration=total_duration,
        )

    def _sync_lcm(self, images: List[ImageInfo]) -> SyncResult:
        """
        LCM 精确同步模式

        使用帧数的最小公倍数，确保所有动画完美循环。
        注意：可能产生大量帧，建议仅在需要精确同步时使用。
        """
        animated_infos = [info for info in images if info.is_animated]
        if not animated_infos:
            return self._sync_loop(images)

        # 计算帧数的 LCM
        frame_counts = [info.n_frames for info in animated_infos]
        target_frames = frame_counts[0]
        for fc in frame_counts[1:]:
            target_frames = lcm(target_frames, fc)

        # 限制最大帧数
        if target_frames > self.max_frames:
            # 降级为 LOOP 模式
            return self._sync_loop(images)

        # 计算统一的帧时长（使用平均值）
        total_durations = [info.total_duration for info in animated_infos]
        avg_total_duration = sum(total_durations) // len(total_durations)
        frame_duration = max(avg_total_duration // target_frames, self.MIN_FRAME_DURATION)

        # 生成帧索引
        frame_indices = []
        durations = []
        for frame_idx in range(target_frames):
            indices = []
            for info in images:
                if info.is_animated:
                    # 按 LCM 比例映射帧索引
                    idx = frame_idx % info.n_frames
                    indices.append(idx)
                else:
                    indices.append(0)
            frame_indices.append(tuple(indices))
            durations.append(frame_duration)

        return SyncResult(
            frame_indices=frame_indices,
            durations=durations,
            total_frames=target_frames,
            total_duration=sum(durations),
        )

    def _get_frame_at_time_from_info(self, info: ImageInfo, t: int) -> int:
        """
        根据时间获取帧索引

        参数:
            info: ImageInfo 对象
            t: 时间点（毫秒）

        返回:
            帧索引
        """
        cumulative = 0
        for i, duration in enumerate(info.durations):
            cumulative += duration
            if t < cumulative:
                return i
        return info.n_frames - 1
