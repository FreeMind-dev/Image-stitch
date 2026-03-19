"""
帧同步模块单元测试

测试 FrameSynchronizer 在不同同步模式下的行为：
- 全静态图 -> 单帧结果
- TIME_SYNC 基于时间的独立循环模式
- LOOP 简单循环模式
- LONGEST 最长模式
- SHORTEST 最短模式
- LCM 最小公倍数精确同步模式
- LCM 超限降级回退
"""

import pytest
from PIL import Image

from image_stitch.core.frame_sync import FrameSynchronizer, SyncMode, SyncResult
from image_stitch.core.image_loader import ImageInfo


# ==================== 全静态图测试 ====================

class TestAllStatic:
    """全部静态图的同步测试"""

    def test_all_static_single_frame(self, red_info, green_info, blue_info):
        """全部静态图片只产生一帧"""
        sync = FrameSynchronizer(mode=SyncMode.LOOP)
        result = sync.sync([red_info, green_info, blue_info])

        assert isinstance(result, SyncResult)
        assert result.total_frames == 1
        assert result.total_duration == 0
        assert len(result.frame_indices) == 1
        assert result.frame_indices[0] == (0, 0, 0)

    def test_all_static_time_sync(self, red_info, green_info):
        """TIME_SYNC 模式下全部静态图也只产生一帧"""
        sync = FrameSynchronizer(mode=SyncMode.TIME_SYNC)
        result = sync.sync([red_info, green_info])

        assert result.total_frames == 1
        assert result.total_duration == 0

    def test_all_static_lcm(self, red_info, blue_info):
        """LCM 模式下全部静态图也只产生一帧"""
        sync = FrameSynchronizer(mode=SyncMode.LCM)
        result = sync.sync([red_info, blue_info])

        assert result.total_frames == 1

    def test_empty_raises(self):
        """空输入列表应抛出 ValueError"""
        sync = FrameSynchronizer()
        with pytest.raises(ValueError, match="至少需要一个图像"):
            sync.sync([])


# ==================== TIME_SYNC 模式测试 ====================

class TestTimeSyncMode:
    """TIME_SYNC 基于时间的独立循环模式测试"""

    def test_single_animated(self, anim1_info):
        """单个动画的 TIME_SYNC"""
        sync = FrameSynchronizer(mode=SyncMode.TIME_SYNC)
        result = sync.sync([anim1_info])

        assert result.total_frames >= 1
        assert all(dur >= FrameSynchronizer.MIN_FRAME_DURATION for dur in result.durations)

    def test_mixed_static_animated(self, red_info, anim1_info):
        """混合静态和动态图的 TIME_SYNC"""
        sync = FrameSynchronizer(mode=SyncMode.TIME_SYNC)
        result = sync.sync([red_info, anim1_info])

        assert result.total_frames >= 1
        # 静态图帧索引始终为 0
        for indices in result.frame_indices:
            assert indices[0] == 0  # 静态图 (red) 始终第 0 帧

    def test_two_animated(self, anim1_info, anim2_info):
        """两个动画的 TIME_SYNC"""
        sync = FrameSynchronizer(mode=SyncMode.TIME_SYNC)
        result = sync.sync([anim1_info, anim2_info])

        assert result.total_frames >= 1
        assert len(result.frame_indices) == result.total_frames
        assert len(result.durations) == result.total_frames

    def test_frame_duration_minimum(self, test_a_info, test_b_info):
        """帧时长不低于最小值 (20ms)"""
        sync = FrameSynchronizer(mode=SyncMode.TIME_SYNC)
        result = sync.sync([test_a_info, test_b_info])

        for dur in result.durations:
            assert dur >= FrameSynchronizer.MIN_FRAME_DURATION

    def test_indices_tuple_length(self, red_info, anim1_info, anim2_info):
        """帧索引元组长度匹配图片数量"""
        sync = FrameSynchronizer(mode=SyncMode.TIME_SYNC)
        result = sync.sync([red_info, anim1_info, anim2_info])

        for indices in result.frame_indices:
            assert len(indices) == 3

    def test_max_frames_limit(self, test_a_info, test_b_info):
        """最大帧数限制生效"""
        sync = FrameSynchronizer(mode=SyncMode.TIME_SYNC, max_frames=10)
        result = sync.sync([test_a_info, test_b_info])

        assert result.total_frames <= 10

    def test_short_duration_still_generates_one_frame(self):
        """总时长短于最小帧时长时，仍应至少输出一帧"""
        frame = Image.new("RGBA", (10, 10), (255, 0, 0, 255))
        info = ImageInfo(
            path="short.webp",
            is_animated=True,
            n_frames=1,
            width=10,
            height=10,
            format="WEBP",
            frames=[frame],
            durations=[10],
            total_duration=10,
        )

        sync = FrameSynchronizer(mode=SyncMode.TIME_SYNC)
        result = sync.sync([info])

        assert result.total_frames == 1
        assert result.frame_indices == [(0,)]
        assert result.durations == [FrameSynchronizer.MIN_FRAME_DURATION]


# ==================== LOOP 模式测试 ====================

class TestLoopMode:
    """LOOP 简单循环模式测试"""

    def test_single_animated(self, anim1_info):
        """单个动画的 LOOP 模式"""
        sync = FrameSynchronizer(mode=SyncMode.LOOP)
        result = sync.sync([anim1_info])

        assert result.total_frames == anim1_info.n_frames
        assert result.durations == anim1_info.durations

    def test_loop_uses_max_frames_count(self, anim1_info, anim2_info):
        """LOOP 模式以帧数最多的动画为基准"""
        sync = FrameSynchronizer(mode=SyncMode.LOOP)
        result = sync.sync([anim1_info, anim2_info])

        # anim2 有 5 帧 > anim1 的 3 帧
        assert result.total_frames == 5
        assert result.durations == anim2_info.durations

    def test_loop_frame_cycling(self, anim1_info, anim2_info):
        """LOOP 模式中较短动画按帧索引循环"""
        sync = FrameSynchronizer(mode=SyncMode.LOOP)
        result = sync.sync([anim1_info, anim2_info])

        # anim1 有 3 帧，在 5 帧循环中索引应为 0,1,2,0,1
        expected_anim1_indices = [0, 1, 2, 0, 1]
        actual_anim1_indices = [indices[0] for indices in result.frame_indices]
        assert actual_anim1_indices == expected_anim1_indices

    def test_loop_static_always_zero(self, red_info, anim2_info):
        """LOOP 模式中静态图帧索引始终为 0"""
        sync = FrameSynchronizer(mode=SyncMode.LOOP)
        result = sync.sync([red_info, anim2_info])

        for indices in result.frame_indices:
            assert indices[0] == 0  # 静态图始终第 0 帧

    def test_loop_all_static(self, red_info, green_info):
        """LOOP 模式全部静态图返回单帧"""
        sync = FrameSynchronizer(mode=SyncMode.LOOP)
        result = sync.sync([red_info, green_info])

        assert result.total_frames == 1


# ==================== LONGEST 模式测试 ====================

class TestLongestMode:
    """LONGEST 最长模式测试"""

    def test_longest_uses_max_duration(self, test_a_info, test_b_info):
        """LONGEST 模式以总时长最长的动画为基准"""
        sync = FrameSynchronizer(mode=SyncMode.LONGEST)
        result = sync.sync([test_a_info, test_b_info])

        # 基准动画的帧数
        max_dur_info = max([test_a_info, test_b_info], key=lambda x: x.total_duration)
        assert result.total_frames == max_dur_info.n_frames
        assert result.total_duration == max_dur_info.total_duration

    def test_longest_with_static(self, red_info, anim1_info):
        """LONGEST 模式包含静态图"""
        sync = FrameSynchronizer(mode=SyncMode.LONGEST)
        result = sync.sync([red_info, anim1_info])

        assert result.total_frames == anim1_info.n_frames

    def test_longest_indices_valid(self, test_a_info, test_b_info):
        """LONGEST 模式帧索引在各动画有效范围内"""
        sync = FrameSynchronizer(mode=SyncMode.LONGEST)
        result = sync.sync([test_a_info, test_b_info])

        for indices in result.frame_indices:
            assert 0 <= indices[0] < test_a_info.n_frames
            assert 0 <= indices[1] < test_b_info.n_frames


# ==================== SHORTEST 模式测试 ====================

class TestShortestMode:
    """SHORTEST 最短模式测试"""

    def test_shortest_uses_min_duration(self, test_a_info, test_b_info):
        """SHORTEST 模式以总时长最短的动画为基准"""
        sync = FrameSynchronizer(mode=SyncMode.SHORTEST)
        result = sync.sync([test_a_info, test_b_info])

        min_dur_info = min([test_a_info, test_b_info], key=lambda x: x.total_duration)
        assert result.total_frames == min_dur_info.n_frames
        assert result.total_duration == min_dur_info.total_duration

    def test_shortest_with_static(self, red_info, anim1_info):
        """SHORTEST 模式包含静态图"""
        sync = FrameSynchronizer(mode=SyncMode.SHORTEST)
        result = sync.sync([red_info, anim1_info])

        assert result.total_frames == anim1_info.n_frames

    def test_shortest_indices_valid(self, test_a_info, test_b_info):
        """SHORTEST 模式帧索引在各动画有效范围内"""
        sync = FrameSynchronizer(mode=SyncMode.SHORTEST)
        result = sync.sync([test_a_info, test_b_info])

        for indices in result.frame_indices:
            assert 0 <= indices[0] < test_a_info.n_frames
            assert 0 <= indices[1] < test_b_info.n_frames


# ==================== LCM 模式测试 ====================

class TestLcmMode:
    """LCM 最小公倍数精确同步模式测试"""

    def test_lcm_frame_count(self, anim1_info, anim2_info):
        """LCM 模式帧数为各动画帧数的最小公倍数"""
        sync = FrameSynchronizer(mode=SyncMode.LCM, max_frames=500)
        result = sync.sync([anim1_info, anim2_info])

        # lcm(3, 5) = 15
        assert result.total_frames == 15

    def test_lcm_indices_cycling(self, anim1_info, anim2_info):
        """LCM 模式帧索引循环正确"""
        sync = FrameSynchronizer(mode=SyncMode.LCM, max_frames=500)
        result = sync.sync([anim1_info, anim2_info])

        # 验证每个动画的帧索引都是循环的
        for indices in result.frame_indices:
            assert 0 <= indices[0] < anim1_info.n_frames
            assert 0 <= indices[1] < anim2_info.n_frames

    def test_lcm_fallback_when_too_many(self, test_a_info, test_b_info):
        """LCM 超过最大帧数限制时降级为 LOOP 模式"""
        # 设置非常小的 max_frames 以触发降级
        sync = FrameSynchronizer(mode=SyncMode.LCM, max_frames=5)
        result = sync.sync([test_a_info, test_b_info])

        # lcm(10, 8) = 40 > 5, 应降级为 LOOP
        # LOOP 模式以帧数最多的动画为基准
        max_frames = max(test_a_info.n_frames, test_b_info.n_frames)
        assert result.total_frames == max_frames

    def test_lcm_with_static(self, red_info, anim1_info):
        """LCM 模式包含静态图"""
        sync = FrameSynchronizer(mode=SyncMode.LCM, max_frames=500)
        result = sync.sync([red_info, anim1_info])

        # 只有一个动画，lcm 就是它的帧数
        assert result.total_frames == anim1_info.n_frames

    def test_lcm_durations_consistent(self, anim1_info, anim2_info):
        """LCM 模式帧时长不低于最小值"""
        sync = FrameSynchronizer(mode=SyncMode.LCM, max_frames=500)
        result = sync.sync([anim1_info, anim2_info])

        for dur in result.durations:
            assert dur >= FrameSynchronizer.MIN_FRAME_DURATION


# ==================== SyncResult 数据结构测试 ====================

class TestSyncResult:
    """SyncResult 数据结构一致性测试"""

    @pytest.mark.parametrize("mode", [
        SyncMode.TIME_SYNC, SyncMode.LOOP, SyncMode.LONGEST,
        SyncMode.SHORTEST, SyncMode.LCM,
    ])
    def test_result_consistency(self, mode, anim1_info, anim2_info):
        """各模式下 SyncResult 帧索引/时长/帧数的一致性"""
        sync = FrameSynchronizer(mode=mode, max_frames=500)
        result = sync.sync([anim1_info, anim2_info])

        assert len(result.frame_indices) == result.total_frames
        assert len(result.durations) == result.total_frames
        assert result.total_duration == sum(result.durations)


class TestValidation:
    """参数校验测试"""

    def test_invalid_max_frames_raises(self):
        """max_frames 必须大于 0"""
        with pytest.raises(ValueError, match="max_frames"):
            FrameSynchronizer(max_frames=0)
