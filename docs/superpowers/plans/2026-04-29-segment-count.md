# 录制段数功能实施计划

> **致自动化代理：** 必须使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 来逐任务实施此计划。步骤使用复选框（`- [ ]`）语法进行跟踪。

**目标：** 为直播录制添加"录制段数"功能，用户可指定录制段数，达到设定值后自动停止录制并停止监控。

**架构：** 在现有分段录制功能基础上，添加段数限制功能。通过监控 FFmpeg 生成的分段文件数量，当达到设定值时自动停止录制。

**技术栈：** Python, Flet UI, FFmpeg, asyncio

---

## 文件结构

### 需要修改的文件

| 文件路径 | 修改内容 |
|---------|----------|
| `app/models/recording/recording_model.py` | 添加 `segment_count` 字段 |
| `app/ui/components/business/recording_dialog.py` | 添加录制段数输入框 |
| `app/core/recording/stream_manager.py` | 添加段数计数和自动停止逻辑 |
| `locales/zh_CN.json` | 添加中文翻译 |
| `locales/en_US.json` | 添加英文翻译 |
| `tests/test_recording_dialog.py` | 添加测试用例 |

---

## 任务分解

### 任务 1: 修改 Recording 模型

**文件：**
- 修改: `app/models/recording/recording_model.py`

- [ ] **步骤 1: 添加 segment_count 字段到 __init__ 方法**

在 `__init__` 方法中添加 `segment_count` 参数：

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
        monitor_status,
        scheduled_recording,
        scheduled_start_time,
        monitor_hours,
        recording_dir,
        enabled_message_push,
        only_notify_no_record,
        flv_use_direct_download
    ):
        # ... 其他初始化
        self.segment_count = segment_count or 0  # 默认为0表示无限录制
```

- [ ] **步骤 2: 更新 to_dict 方法**

在 `to_dict` 方法中添加 `segment_count` 字段：

```python
def to_dict(self):
    return {
        # ... 其他字段
        "segment_count": self.segment_count,
    }
```

- [ ] **步骤 3: 更新 from_dict 方法**

在 `from_dict` 方法中添加 `segment_count` 字段：

```python
@classmethod
def from_dict(cls, data):
    recording = cls(
        # ... 其他字段
        data.get("segment_count"),
    )
```

- [ ] **步骤 4: 提交更改**

```bash
git add app/models/recording/recording_model.py
git commit -m "feat: add segment_count field to Recording model"
```

---

### 任务 2: 添加多语言支持

**文件：**
- 修改: `locales/zh_CN.json`
- 修改: `locales/en_US.json`

- [ ] **步骤 1: 添加中文翻译**

在 `locales/zh_CN.json` 的 `recording_dialog` 部分添加：

```json
{
    "recording_dialog": {
        "segment_count": "录制段数",
        "input_segment_count": "输入录制段数（0表示无限录制）"
    }
}
```

- [ ] **步骤 2: 添加英文翻译**

在 `locales/en_US.json` 的 `recording_dialog` 部分添加：

```json
{
    "recording_dialog": {
        "segment_count": "Segment Count",
        "input_segment_count": "Enter segment count (0 for unlimited)"
    }
}
```

- [ ] **步骤 3: 提交更改**

```bash
git add locales/zh_CN.json locales/en_US.json
git commit -m "feat: add segment count translations"
```

---

### 任务 3: 修改 RecordingDialog UI

**文件：**
- 修改: `app/ui/components/business/recording_dialog.py`

- [ ] **步骤 1: 添加 segment_count 变量初始化**

在 `show_dialog` 方法中，找到 `segment_time` 初始化的位置，在其下方添加：

```python
segment_count = config.get_value("segment_count", "segment_count", 0)
```

- [ ] **步骤 2: 添加 segment_count_input 控件**

在 `segment_input` 定义的下方添加：

```python
segment_count_input = ft.TextField(
    label=self._["segment_count"],
    hint_text=self._["input_segment_count"],
    border_radius=5,
    filled=False,
    value=segment_count,
    visible=segment_record,
    keyboard_type=ft.KeyboardType.NUMBER,
)
```

- [ ] **步骤 3: 修改 on_segment_setting_change 函数**

修改 `on_segment_setting_change` 函数，使其同时控制 `segment_count_input` 的可见性：

```python
async def on_segment_setting_change(e):
    selected_value = e.control.value
    segment_input.visible = selected_value == self._["yes"]
    segment_count_input.visible = selected_value == self._["yes"]
    self.page.update()
```

- [ ] **步骤 4: 将 segment_count_input 添加到布局**

在 `segment_input` 的下方添加 `segment_count_input` 到布局中：

```python
# 在 single_input tab 的 content 中
segment_setting_dropdown,
segment_input,
segment_count_input,  # 新增
scheduled_setting_dropdown,
```

- [ ] **步骤 5: 修改 _build_single_recording_payload 方法调用**

在 `on_confirm` 函数中，找到 `_build_single_recording_payload` 调用，添加 `segment_count_value` 参数：

```python
recordings_info = await self._build_single_recording_payload(
    url_value=url_field.value,
    streamer_name_value=streamer_name_field.value,
    quality_value=quality_dropdown.value,
    record_format_value=record_format_field.value,
    recording_dir_value=recording_dir_field.value,
    segment_visible=segment_input.visible,
    segment_time_value=segment_input.value,
    segment_count_value=segment_count_input.value,  # 新增
    scheduled_recording_enabled=scheduled_setting_dropdown.value == "true",
    # ... 其他参数
)
```

- [ ] **步骤 6: 修改 _build_single_recording_payload 方法定义**

修改 `_build_single_recording_payload` 方法，添加 `segment_count_value` 参数：

```python
async def _build_single_recording_payload(
    self,
    *,
    url_value,
    streamer_name_value,
    quality_value,
    record_format_value,
    recording_dir_value,
    segment_visible,
    segment_time_value,
    segment_count_value,  # 新增
    scheduled_recording_enabled,
    scheduled_start_time_values,
    monitor_hours_values,
    message_push_enabled,
    only_notify_no_record,
    flv_use_direct_download,
    rec_id,
    initial_values,
):
    # ... 其他代码
    
    return [
        {
            # ... 其他字段
            "segment_record": segment_visible,
            "segment_time": segment_time_value,
            "segment_count": segment_count_value,  # 新增
            # ... 其他字段
        }
    ]
```

- [ ] **步骤 7: 提交更改**

```bash
git add app/ui/components/business/recording_dialog.py
git commit -m "feat: add segment count input to recording dialog"
```

---

### 任务 4: 修改 LiveStreamRecorder 录制逻辑

**文件：**
- 修改: `app/core/recording/stream_manager.py`

- [ ] **步骤 1: 添加 segment_count 属性**

在 `__init__` 方法中，找到 `segment_time` 初始化的位置，在其下方添加：

```python
self.segment_count = self._get_info("segment_count", default=0)
self.current_segment_count = 0
```

- [ ] **步骤 2: 添加 monitor_segment_count 方法**

在 `LiveStreamRecorder` 类中添加新方法：

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

- [ ] **步骤 3: 修改 start_ffmpeg 方法**

在 `start_ffmpeg` 方法中，找到 `process = await asyncio.create_subprocess_exec(...)` 的位置，在其后添加监控任务：

```python
# 在 process 创建后添加
monitor_task = None
if self.segment_record and self.segment_count > 0:
    monitor_task = asyncio.create_task(self.monitor_segment_count(ffmpeg_command[-1]))
```

在 `start_ffmpeg` 方法的 `finally` 块中添加取消监控任务：

```python
finally:
    if monitor_task:
        monitor_task.cancel()
    self.recording.record_url = None
```

- [ ] **步骤 4: 提交更改**

```bash
git add app/core/recording/stream_manager.py
git commit -m "feat: add segment count monitoring and auto-stop"
```

---

### 任务 5: 添加测试用例

**文件：**
- 修改: `tests/test_recording_dialog.py`

- [ ] **步骤 1: 添加测试用例**

在测试文件中添加：

```python
def test_segment_count_default_value():
    """测试录制段数默认值为0"""
    # 创建录制配置
    # 验证 segment_count 默认值为 0

def test_segment_count_visibility_when_segment_enabled():
    """测试分段录制启用时，录制段数输入框可见"""
    # 启用分段录制
    # 验证 segment_count_input 可见

def test_segment_count_visibility_when_segment_disabled():
    """测试分段录制禁用时，录制段数输入框隐藏"""
    # 禁用分段录制
    # 验证 segment_count_input 隐藏
```

- [ ] **步骤 2: 运行测试**

```bash
pytest tests/test_recording_dialog.py -v
```

- [ ] **步骤 3: 提交更改**

```bash
git add tests/test_recording_dialog.py
git commit -m "test: add segment count tests"
```

---

## 验证清单

完成所有任务后，执行以下验证：

- [ ] 运行所有测试：`pytest tests/ -v`
- [ ] 检查代码风格：`ruff check app/`
- [ ] 启动应用并测试功能
- [ ] 验证录制段数输入框在分段录制启用时显示
- [ ] 验证录制段数输入框在分段录制禁用时隐藏
- [ ] 验证达到设定段数后自动停止录制

---

## 注意事项

1. **向后兼容性**：默认值为0表示无限录制，保持现有行为
2. **输入验证**：录制段数只能输入非负整数
3. **文件监控**：每5秒检查一次分段文件数量，可能存在轻微延迟
4. **自动停止**：达到设定段数后，设置 `should_stop = True` 触发停止流程
