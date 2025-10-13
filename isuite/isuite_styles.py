# Copyright (c) 2025 Andrzej Mazur, Berlin
# Email: info@isuite.org
# Licensed under the Isuite-TTS Non-Commercial License. See LICENSE for details.

class GuiStyles:
    @staticmethod
    def create_textedit_styles():
        return """
        QTextEdit {
            background-color: #FFFFFF;
            color: #111111;
            border: 1px solid #888888;
            border-radius: 8px;
            padding: 8px;
            selection-background-color: #3F51B5;
            margin: 10px;
            font-size: 11pt;
        }
        """

    @staticmethod
    def create_groupbox_styles(title_bg_color="#EEEEEE", title_text_color="#333333"):
        return f"""
        QGroupBox {{
            font-weight: bold;
            border: 1px solid #CCCCCC;
            border-radius: 8px;
            margin-top: 12px;
            padding-top: 14px;
            background-color: #ECECEC;      /* transparent */
            color: #E0E0E0;
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            subcontrol-position: top center;
            padding: 4px 10px;
            background-color: {title_bg_color};
            border-radius: 6px;
            color: {title_text_color};
            font-size: 13px;
            font-weight: normal;
        }}
        """

    @staticmethod
    def create_progressbar_styles():
        return """
        QProgressBar {
            border: 1px solid #CCCCCC;
            border-radius: 5px;
            background-color: #F0F0F0;
        }
        QProgressBar::chunk {
            background-color: #4CAF50;
            border-radius: 5px;
        }
        """
