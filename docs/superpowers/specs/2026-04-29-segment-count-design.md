# 录制段数功能设计文档

## 1. 概述

### 1.1 需求描述

用户希望在新增直播间时，添加一个"录制段数"功能。用户输入段数（如2），表示只录制2段，然后自动停止录制并停止监控。

### 1.2 业务规则

- 录制段数功能必须在启用分段录制时才能设置
- 默认值为空或0，表示无限录制（保持现有行为）
- 当录制达到设定的段数后，自动停止录制并停止监控

## 2. 技术设计

### 2.1 数据模型修改

**文件**: `app/models/recording/recording_model.py`

在 `Recording` 类中添加 `segment_count` 字段：

```python
class Recording:
    def __init__(
        self,
        rec_id,
        url,
        streamer_name,
        record_format,
        quality,
        segment_record,
        segment_time,
        segment_count,  # 新增字段
        # ... 其他字段
    ):
        # ... 其他初始化
        self.segment_count = segment_count or 0  # 默认为0表示无限录制
```

更新 `to_dict()` 和 `from_dict()` 方法：

```python
def to_dict(self):
    return {
        # ... 其他字段
        "segment_count": self.segment_count,
    }

@classmethod
def from_dict(cls, data):
    recording = cls(
        # ... 其他字段
        data.get("segment_count"),
    )
```

### 2.2 UI 修改

**文件**: `app/ui/components/business/recording_dialog.py`

在分段录制设置下方添加"录制段数"输入框：

```python
# 在 segment_input 下方添加
segment_count_input = ft.TextField(
    label=self._["segment_count"],
    hint_text=self._["input_segment_count"],
    border_radius=5,
    filled=False,
    value=segment_count,
    visible=segment_record,  # 与分段录制设置联动
)

# 修改 on_segment_setting_change 函数
async def on_segment_setting_change(e):
    selected_value = e.control.value
    segment_input.visible = selected_value == self._["yes"]
    segment_count_input.visible = selected_value == self._["yes"]  # 新增
    self.page.update()
```

### 2.3 录制逻辑修改

**文件**: `app/core/recording/stream_manager.py`

在 `LiveStreamRecorder` 类中添加计数逻辑：

```python
class LiveStreamRecorder:
    DEFAULT_SEGMENT_TIME = "1800"
    DEFAULT_SAVE_FORMAT = "mp4"
    DEFAULT_QUALITY = VideoQuality.OD

    def __init__(self, app, recording, recording_info):
        # ... 其他初始化
        self.segment_count = self._get_info("segment_count", default=0)
        self.current_segment_count = 0
```

在 FFmpeg 分段录制时监控生成的文件数量：

```python
async def monitor_segment_count(self, save_path):
    """监控分段录制数量，达到设定值时自动停止"""
    if self.segment_count <= 0:
        return  # 无限录制
    
    import glob
    import os
    
    # 获取保存路径的目录和文件名前缀
    save_dir = os.path.dirname(save_path)
    file_prefix = os.path.basename(save_path).split("_%03d")[0]
    
    while not self.should_stop:
        await asyncio.sleep(5)  # 每5秒检查一次
        
        # 统计已生成的分段文件数量
        pattern = os.path.join(save_dir, f"{file_prefix}_*")
        segment_files = glob.glob(pattern)
        
        if len(segment_files) >= self.segment_count:
            logger.info(f"已达到设定的录制段数 {self.segment_count}，自动停止录制")
            self.should_stop = True
            break
```

在 `start_ffmpeg` 方法中启动监控任务：

```python
async def start_ffmpeg(self, record_name, live_url, record_url, ffmpeg_command, save_type, script_command=None):
    # ... 其他代码
    
    if self.segment_record and self.segment_count > 0:
        # 启动分段数量监控任务
        monitor_task = asyncio.create_task(self.monitor_segment_count(ffmpeg_command[-1]))
    
    # ... 其他代码
    
    if self.segment_record and self.segment_count > 0:
        monitor_task.cancel()
```

### 2.4 多语言支持

**文件**: `locales/zh_CN.json`

```json
{
    "recording_dialog": {
        "segment_count": "录制段数",
        "input_segment_count": "输入录制段数（0表示无限录制）"
    }
}
```

**文件**: `locales/en_US.json`

```json
{
    "recording_dialog": {
        "segment_count": "Segment Count",
        "input_segment_count": "Enter segment count (0 for unlimited)"
    }
}
```

## 3. 测试用例

### 3.1 单元测试

**文件**: `tests/test_recording_dialog.py`

```python
def test_segment_count_visibility():
    """测试录制段数输入框的可见性"""
    # 当分段录制禁用时，录制段数输入框应该隐藏
    # 当分段录制启用时，录制段数输入框应该显示

def test_segment_count_validation():
    """测试录制段数输入验证"""
    # 只能输入正整数
    # 0表示无限录制
```

### 3.2 集成测试

```python
def test_auto_stop_on_segment_count_reached():
    """测试达到设定段数后自动停止录制"""
    # 设置录制段数为2
    # 模拟分段录制
    # 验证录制在2段后自动停止
```

## 4. 部署说明

### 4.1 数据库迁移

无需数据库迁移，因为数据存储在 JSON 文件中。

### 4.2 配置更新

无需更新配置文件，因为新字段有默认值。

## 5. 风险与限制

### 5.1 风险

- 文件监控可能存在延迟，导致实际录制段数略多于设定值
- 如果用户手动停止录制，计数器不会重置

### 5.2 限制

- 录制段数功能仅支持分段录制模式
- 不支持跨会话的段数累计

## 6. 未来扩展

### 6.1 可能的改进

- 支持跨会话的段数累计
- 支持按时间限制录制（如录制2小时）
- 支持录制完成后自动转码
