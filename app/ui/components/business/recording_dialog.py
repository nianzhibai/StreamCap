import re

import flet as ft

from ....core.platforms.platform_handlers import get_platform_info
from ....models.media.audio_format_model import AudioFormat
from ....models.media.video_format_model import VideoFormat
from ....models.media.video_quality_model import VideoQuality
from ....utils import utils
from ....utils.douyin_url_normalizer import (
    DouyinNormalizationError,
    looks_like_douyin_input,
    normalize_douyin_input,
)
from ....utils.logger import logger


class RecordingDialog:
    def __init__(self, app, on_confirm_callback=None, recording=None):
        self.app = app
        self.page = self.app.page
        self.on_confirm_callback = on_confirm_callback
        self.recording = recording
        self.app.language_manager.add_observer(self)
        self._ = {}
        self.load()

    def load(self):
        language = self.app.language_manager.language
        for key in ("recording_dialog", "recordings_page", "base", "video_quality"):
            self._.update(language.get(key, {}))

    def _get_resolution_proxy(self):
        user_config = self.app.settings.user_config
        if not user_config.get("enable_proxy"):
            return None
        return utils.handle_proxy_addr(user_config.get("proxy_address"))

    async def _normalize_url_if_douyin(self, raw_url: str) -> str:
        live_url = raw_url.strip()
        if not looks_like_douyin_input(live_url):
            return live_url
        return await normalize_douyin_input(live_url, proxy=self._get_resolution_proxy())

    async def _get_normalized_existing_urls(self, existing_recordings):
        normalized_existing_urls = set()
        for existing_recording in existing_recordings:
            existing_url = existing_recording.strip()
            try:
                normalized_existing_urls.add(await self._normalize_url_if_douyin(existing_url))
            except DouyinNormalizationError:
                logger.warning(f"Failed to normalize existing Douyin URL for dedup: {existing_url}")
                normalized_existing_urls.add(existing_url)
        return normalized_existing_urls

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
        segment_count_value,
        scheduled_recording_enabled,
        scheduled_start_time_values,
        monitor_hours_values,
        message_push_enabled,
        only_notify_no_record,
        flv_use_direct_download,
        rec_id,
        initial_values,
    ):
        quality_info = self._[quality_value]

        if not streamer_name_value:
            anchor_name = self._["live_room"]
            title = f"{anchor_name} - {quality_info}"
        else:
            anchor_name = streamer_name_value.strip()
            title = f"{anchor_name} - {quality_info}"

        display_title = title
        live_url = await self._normalize_url_if_douyin(url_value)
        platform, platform_key = get_platform_info(live_url)
        if not platform:
            raise ValueError(live_url)

        return [
            {
                "rec_id": rec_id,
                "url": live_url,
                "streamer_name": anchor_name,
                "record_format": record_format_value,
                "quality": quality_value,
                "quality_info": quality_info,
                "title": title,
                "speed": "X KB/s",
                "segment_record": segment_visible,
                "segment_time": segment_time_value,
                "segment_count": segment_count_value,
                "monitor_status": initial_values.get("monitor_status", True),
                "display_title": display_title,
                "scheduled_recording": scheduled_recording_enabled,
                "scheduled_start_time": ",".join(str(value) for value in scheduled_start_time_values),
                "monitor_hours": ",".join(str(value) for value in monitor_hours_values),
                "recording_dir": recording_dir_value,
                "enabled_message_push": message_push_enabled,
                "only_notify_no_record": only_notify_no_record,
                "flv_use_direct_download": flv_use_direct_download,
                }
        ]

    async def _build_batch_recording_payloads(self, *, batch_input_value, existing_recordings):
        lines = batch_input_value.splitlines()
        recordings_info = []
        batch_url_list = []
        quality_dict = {"0": "OD", "1": "UHD", "2": "HD", "3": "SD", "4": "LD"}
        unsupported_urls = []
        normalized_existing_urls = await self._get_normalized_existing_urls(existing_recordings)

        for line in lines:
            if "http" not in line:
                continue

            streamer_name = ""
            quality = "OD"
            raw_line = line.strip()
            remaining = raw_line

            quality_split = re.split(r"[，,]", raw_line, maxsplit=1)
            if len(quality_split) == 2 and quality_split[0].strip() in quality_dict:
                quality = quality_split[0].strip()
                remaining = quality_split[1].strip()

            streamer_split = re.split(r"[，,](?!.*[，,])", remaining, maxsplit=1)
            if len(streamer_split) == 2 and "http" not in streamer_split[1]:
                url = streamer_split[0].strip()
                streamer_name = streamer_split[1].strip()
            else:
                url = remaining.strip()

            live_url = await self._normalize_url_if_douyin(url)
            platform, platform_key = get_platform_info(live_url)
            if not platform:
                unsupported_urls.append(live_url)
                continue

            normalized_url = live_url.strip()
            existing_urls = set(batch_url_list) | normalized_existing_urls
            if normalized_url in existing_urls:
                logger.info(f"Skip {normalized_url}, the live room URL already exists.")
                continue

            quality = quality_dict.get(quality, "OD")
            title = f"{streamer_name} - {self._[quality]}"
            display_title = title
            if not streamer_name:
                streamer_name = self._["live_room"]
                display_title = streamer_name + normalized_url.split("?")[0] + "... - " + self._[quality]

            recording_info = {
                "url": normalized_url,
                "streamer_name": streamer_name,
                "quality": quality,
                "quality_info": self._[VideoQuality.OD],
                "title": title,
                "display_title": display_title,
            }
            batch_url_list.append(normalized_url)
            recordings_info.append(recording_info)

        return recordings_info, unsupported_urls

    async def show_dialog(self):
        """Show a dialog for adding or editing a recording."""
        initial_values = self.recording.to_dict() if self.recording else {}

        config = RecordingConfig(initial_values, self.app.settings.user_config)
        default_record_format = config.get_value("record_format", "video_format", VideoFormat.MP4)
        default_record_type = "video" if default_record_format in VideoFormat.get_formats() else "audio"
        default_record_quality = config.get_value("quality", "record_quality", VideoQuality.OD)
        segment_record = config.get_value("segment_record", "segmented_recording_enabled", False)
        segment_time = config.get_value("segment_time", "video_segment_time", 1800)
        segment_count = config.get_value("segment_count", "segment_count", 2)
        only_notify_no_record = config.get_value("only_notify_no_record", default=False)
        flv_use_direct_download = config.get_value("flv_use_direct_download", default=False)

        async def on_url_change(_):
            """Enable or disable the submit button based on whether the URL field is filled."""
            single_input_value = url_field.value.strip()
            is_active = (
                utils.is_valid_url(single_input_value)
                or looks_like_douyin_input(single_input_value)
                or utils.contains_url(batch_input.value.strip())
            )
            dialog.actions[1].disabled = not is_active
            self.page.update()

        async def update_format_options(e):
            if e.control.value == "video":
                record_format_field.options = [ft.dropdown.Option(i) for i in VideoFormat.get_formats()]
            else:
                record_format_field.options = [ft.dropdown.Option(i) for i in AudioFormat.get_formats()]
            record_format_field.value = record_format_field.options[0].key
            record_format_field.update()

        url_field = ft.TextField(
            label=self._["input_live_link"],
            hint_text=self._["example"] + "：https://www.example.com/xxxxxx",
            border_radius=5,
            filled=False,
            value=initial_values.get("url"),
            on_change=on_url_change,
        )

        streamer_name_field = ft.TextField(
            label=self._["input_anchor_name"],
            hint_text=self._["default_input"],
            border_radius=5,
            filled=False,
            value=initial_values.get("streamer_name", ""),
        )
        media_type_dropdown = ft.Dropdown(
            label=self._["select_media_type"],
            options=[
                ft.dropdown.Option("video", text=self._["video"]),
                ft.dropdown.Option("audio", text=self._["audio"])
            ],
            width=245,
            value=default_record_type,
            on_change=update_format_options
        )

        if default_record_type == "video":
            record_formats = VideoFormat.get_formats()
        else:
            record_formats = AudioFormat.get_formats()
        record_format_field = ft.Dropdown(
            label=self._["select_record_format"],
            options=[ft.dropdown.Option(i) for i in record_formats],
            border_radius=5,
            filled=False,
            value=default_record_format,
            width=245,
            menu_height=200
        )

        quality_dropdown = ft.Dropdown(
            label=self._["select_resolution"],
            options=[ft.dropdown.Option(i, text=self._[i]) for i in VideoQuality.get_qualities()],
            border_radius=5,
            filled=False,
            value=default_record_quality,
            width=245,
        )

        flv_use_direct_download_dropdown = ft.Dropdown(
            label=self._["flv_use_direct_download"],
            options=[
                ft.dropdown.Option("true", self._["yes"]),
                ft.dropdown.Option("false", self._["no"]),
            ],
            border_radius=5,
            filled=False,
            value="true" if flv_use_direct_download else "false",
            width=245,
            tooltip=self._["flv_use_direct_download_tip"]
        )

        if self.app.is_mobile:
            media_type_dropdown.width = 500
            record_format_field.width = 500
            flv_use_direct_download_dropdown.width = 500
            quality_dropdown.width = 500
            format_row = ft.Column([media_type_dropdown, record_format_field], expand=True)
            quality_row = ft.Column([quality_dropdown, flv_use_direct_download_dropdown], expand=True)
        else:
            format_row = ft.Row([media_type_dropdown, record_format_field], expand=True)
            quality_row = ft.Row([quality_dropdown, flv_use_direct_download_dropdown], expand=True)

        recording_dir_field = ft.TextField(
            label=self._["input_save_path"],
            hint_text=self._["default_input"],
            border_radius=5,
            filled=False,
            value=initial_values.get("recording_dir"),
        )

        async def on_segment_setting_change(e):
            selected_value = e.control.value
            segment_input.visible = selected_value == self._["yes"]
            segment_count_input.visible = selected_value == self._["yes"]
            self.page.update()

        segment_setting_dropdown = ft.Dropdown(
            label=self._["is_segment_enabled"],
            options=[
                ft.dropdown.Option(self._["yes"]),
                ft.dropdown.Option(self._["no"]),
            ],
            border_radius=5,
            filled=False,
            value=self._["yes"] if segment_record else self._["no"],
            on_change=on_segment_setting_change,
            width=500,
        )

        segment_input = ft.TextField(
            label=self._["segment_record_time"],
            hint_text=self._["input_segment_time"],
            border_radius=5,
            filled=False,
            value=segment_time,
            visible=segment_record,
        )

        segment_count_input = ft.TextField(
            label=self._["segment_count"],
            hint_text=self._["input_segment_count"],
            border_radius=5,
            filled=False,
            value=segment_count,
            visible=segment_record,
            keyboard_type=ft.KeyboardType.NUMBER,
            input_filter=ft.NumbersOnlyInputFilter(),
        )

        scheduled_recording = initial_values.get("scheduled_recording", False)
        scheduled_start_time = initial_values.get("scheduled_start_time", '')
        monitor_hours = initial_values.get("monitor_hours", '5')
        message_push_enabled = initial_values.get('enabled_message_push', True)

        time_slots = 2
        time_inputs = []
        hour_inputs = []
        time_buttons = []
        time_picker_handlers = []
        
        time_values = scheduled_start_time.split(",")
        time_values = (time_values + [""] * time_slots)[:time_slots]

        hour_values = str(monitor_hours).split(",")
        hour_values = (hour_values + [""] * time_slots)[:time_slots]

        def create_time_picker_handler(index):
            async def pick_time(_):
                async def handle_change(_):
                    time_inputs[index].value = time_picker.value
                    time_inputs[index].update()

                time_picker = ft.TimePicker(
                    confirm_text=self._['confirm'],
                    cancel_text=self._['cancel'],
                    error_invalid_text=self._['time_out_of_range'],
                    help_text=self._['pick_time_slot'],
                    hour_label_text=self._['hour_label_text'],
                    minute_label_text=self._['minute_label_text'],
                    on_change=handle_change
                )
                self.page.open(time_picker)
            return pick_time
        
        for i in range(time_slots):
            time_input = ft.TextField(
                label=self._["scheduled_start_time"],
                hint_text=self._["example"] + "：18:30:00",
                border_radius=5,
                filled=False,
                value=time_values[i],
            )
            time_inputs.append(time_input)
            
            hour_input = ft.TextField(
                label=self._["monitor_hours"],
                hint_text=self._["example"] + "：5",
                border_radius=5,
                filled=False,
                value=hour_values[i],
                keyboard_type=ft.KeyboardType.NUMBER,
                visible=scheduled_recording,
            )
            hour_inputs.append(hour_input)
            
            handler = create_time_picker_handler(i)
            time_picker_handlers.append(handler)
            
            button = ft.ElevatedButton(
                self._['pick_time'],
                icon=ft.Icons.TIME_TO_LEAVE,
                on_click=handler,
                tooltip=self._['pick_time_tip']
            )
            time_buttons.append(button)
        
        async def on_scheduled_setting_change(e):
            selected_value = e.control.value
            for i in range(time_slots):
                time_rows[i].visible = selected_value == "true"
                hour_inputs[i].visible = selected_value == "true"
            self.page.update()

        scheduled_setting_dropdown = ft.Dropdown(
            label=self._["scheduled_recording"],
            options=[
                ft.dropdown.Option("true", self._["yes"]),
                ft.dropdown.Option("false", self._["no"]),
            ],
            border_radius=5,
            filled=False,
            value="true" if scheduled_recording else "false",
            on_change=on_scheduled_setting_change,
            width=500,
        )

        time_rows = []
        for i in range(time_slots):
            row = ft.Row(
                [
                    ft.Container(content=time_inputs[i], expand=True),
                    ft.Container(content=hour_inputs[i], expand=True),
                    ft.Container(content=time_buttons[i]),
                ],
                spacing=10,
                visible=scheduled_recording,
            )
            time_rows.append(row)

        message_push_dropdown = ft.Dropdown(
            label=self._["enable_message_push"],
            options=[
                ft.dropdown.Option("true", self._["yes"]),
                ft.dropdown.Option("false", self._["no"]),
            ],
            border_radius=5,
            filled=False,
            value="true" if message_push_enabled else "false",
            width=500,
        )

        no_record_dropdown = ft.Dropdown(
            label=self._["only_notify_no_record"],
            options=[
                ft.dropdown.Option("true", self._["yes"]),
                ft.dropdown.Option("false", self._["no"]),
            ],
            border_radius=5,
            filled=False,
            value="true" if only_notify_no_record else "false",
            width=500,
        )

        hint_text_dict = {
            "en": "Example:\n0，https://v.douyin.com/AbcdE，nickname1\n0，https://v.douyin.com/EfghI，nickname2\n\nPS: "
            "0=original image or Blu ray, 1=ultra clear, 2=high-definition, 3=standard definition, 4=smooth\n",
            "zh_CN": "示例:\n0，https://v.douyin.com/AbcdE，主播名1\n0，https://v.douyin.com/EfghI，主播名2"
            "\n\n其中0=原画或者蓝光，1=超清，2=高清，3=标清，4=流畅",
        }

        # Batch input field
        batch_input = ft.TextField(
            label=self._["batch_input_tip"],
            multiline=True,
            min_lines=15,
            max_lines=20,
            border_radius=5,
            filled=False,
            visible=True,
            hint_style=ft.TextStyle(
                size=14,
                color=ft.Colors.GREY_500,
                font_family="Arial",
            ),
            on_change=on_url_change,
            hint_text=hint_text_dict.get(self.app.language_code, hint_text_dict["zh_CN"]),
        )

        tabs = ft.Tabs(
            selected_index=0,
            animation_duration=300,
            height=500,
            tabs=[
                ft.Tab(
                    text=self._["single_input"],
                    content=ft.Container(
                        content=ft.Column(
                            [
                                ft.Container(margin=ft.margin.only(top=10)),
                                url_field,
                                streamer_name_field,
                                format_row,
                                quality_row,
                                recording_dir_field,
                                segment_setting_dropdown,
                                segment_input,
                                segment_count_input,
                                scheduled_setting_dropdown,
                                *time_rows,
                                message_push_dropdown,
                                no_record_dropdown
                            ],
                            tight=True,
                            spacing=10,
                            scroll=ft.ScrollMode.AUTO,
                        )
                    ),
                ),
                ft.Tab(
                    text=self._["batch_input"], content=ft.Container(content=batch_input, margin=ft.margin.only(top=15))
                ),
            ],
        )

        async def not_supported(url):
            logger.warning(f"This platform does not support recording: {url}")
            await self.app.snack_bar.show_snack_bar(self._["platform_not_supported_tip"], duration=3000)

        def get_existing_recordings():
            existing_recordings = [rec.url for rec in self.app.record_manager.recordings]
            return existing_recordings

        async def on_confirm(e):

            existing_recordings = get_existing_recordings()

            if tabs.selected_index == 0:
                rec_id = self.recording.rec_id if self.recording else None
                try:
                    recordings_info = await self._build_single_recording_payload(
                        url_value=url_field.value,
                        streamer_name_value=streamer_name_field.value,
                        quality_value=quality_dropdown.value,
                        record_format_value=record_format_field.value,
                        recording_dir_value=recording_dir_field.value,
                        segment_visible=segment_input.visible,
                        segment_time_value=segment_input.value,
                        segment_count_value=segment_count_input.value,
                        scheduled_recording_enabled=scheduled_setting_dropdown.value == "true",
                        scheduled_start_time_values=[i.value for i in time_inputs],
                        monitor_hours_values=[i.value for i in hour_inputs],
                        message_push_enabled=message_push_dropdown.value == "true",
                        only_notify_no_record=no_record_dropdown.value == "true",
                        flv_use_direct_download=flv_use_direct_download_dropdown.value == "true",
                        rec_id=rec_id,
                        initial_values=initial_values,
                    )
                except DouyinNormalizationError:
                    await self.app.snack_bar.show_snack_bar(self._["douyin_parse_failed_tip"], duration=3000)
                    return
                except ValueError as exc:
                    await not_supported(str(exc))
                    await close_dialog(e)
                    return

                live_url = recordings_info[0]["url"]
                normalized_existing_urls = await self._get_normalized_existing_urls(existing_recordings)

                if live_url in normalized_existing_urls and not rec_id:
                    async def confirm_duplicate():
                        async def close_duplicate_dialog(_):
                            self.url_duplicate_confirm_dialog.open = False
                            self.page.update()
                            await close_dialog(e)

                        async def proceed_with_add(_):
                            await close_duplicate_dialog(e)
                            await self.on_confirm_callback(recordings_info)

                        duplicate_confirm_dialog = ft.AlertDialog(
                            modal=True,
                            title=ft.Text(self._["duplicate_url_title"]),
                            content=ft.Text(self._["duplicate_url_content"]),
                            actions=[
                                ft.TextButton(self._["cancel"], on_click=close_duplicate_dialog),
                                ft.TextButton(self._["sure"], on_click=proceed_with_add),
                            ],
                            actions_alignment=ft.MainAxisAlignment.END,
                        )

                        self.url_duplicate_confirm_dialog = duplicate_confirm_dialog
                        self.url_duplicate_confirm_dialog.open = True
                        self.page.overlay.append(duplicate_confirm_dialog)
                        self.page.update()

                    await confirm_duplicate()
                    return
                else:
                    await self.on_confirm_callback(recordings_info)

            elif tabs.selected_index == 1:  # Batch entry
                try:
                    recordings_info, unsupported_urls = await self._build_batch_recording_payloads(
                        batch_input_value=batch_input.value,
                        existing_recordings=existing_recordings,
                    )
                except DouyinNormalizationError:
                    await self.app.snack_bar.show_snack_bar(self._["douyin_parse_failed_tip"], duration=3000)
                    return

                for unsupported_url in unsupported_urls:
                    await not_supported(unsupported_url)

                await self.on_confirm_callback(recordings_info)

            await close_dialog(e)

        async def close_dialog(_):
            dialog.open = False
            self.page.update()

        close_button = ft.IconButton(icon=ft.Icons.CLOSE, tooltip=self._["close"], on_click=close_dialog)

        title_text = self._["edit_record"] if self.recording else self._["add_record"]
        dialog = ft.AlertDialog(
            open=True,
            modal=True,
            title=ft.Row(
                [
                    ft.Text(title_text, size=16, theme_style=ft.TextThemeStyle.TITLE_LARGE),
                    ft.Container(width=10),
                    close_button,
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                width=500
            ),
            content=tabs,
            actions=[
                ft.TextButton(text=self._["cancel"], on_click=close_dialog),
                ft.TextButton(text=self._["sure"], on_click=on_confirm, disabled=self.recording is None),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            shape=ft.RoundedRectangleBorder(radius=10)
        )

        self.page.overlay.append(dialog)
        self.page.update()


class RecordingConfig:
    def __init__(self, initial_values, user_config):
        self.initial_values = initial_values
        self.user_config = user_config

    def get_value(self, key, user_config_key=None, default=None):
        return self.initial_values.get(key, self.user_config.get(user_config_key or key, default))
