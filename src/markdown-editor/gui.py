import sys
import subprocess
from pathlib import Path
from PySide6.QtWidgets import QApplication, QMainWindow, QFileDialog, QMessageBox
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEnginePage, QWebEngineSettings
from PySide6.QtCore import QUrl, Qt
from PySide6.QtGui import QTextCursor, QDesktopServices, QFont, QFontDatabase

from ui.ui_mainwindow import Ui_MainWindow
from lexer import tokenize
from parser import parse_blocks
from renderer import render_html


def is_wsl():
    try:
        with open('/proc/version', 'r') as f:
            return 'microsoft' in f.read().lower()
    except:
        return False


class WebEnginePage(QWebEnginePage):
    def acceptNavigationRequest(self, url, nav_type, is_main_frame):
        if nav_type == QWebEnginePage.NavigationType.NavigationTypeTyped:
            return True

        if nav_type == QWebEnginePage.NavigationType.NavigationTypeLinkClicked:
            url_string = url.toString()

            if is_wsl():
                try:
                    subprocess.run(['/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe',
                                  '-Command', f'Start-Process "{url_string}"'],
                                 stdout=subprocess.DEVNULL,
                                 stderr=subprocess.DEVNULL)
                except:
                    pass
            else:
                QDesktopServices.openUrl(url)

            return False

        return True


class MarkdownEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.current_file = None
        self.is_modified = False

        old_preview = self.ui.htmlPreview
        self.ui.htmlPreview = QWebEngineView(self)

        custom_page = WebEnginePage(self.ui.htmlPreview)
        self.ui.htmlPreview.setPage(custom_page)

        settings = self.ui.htmlPreview.settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, True)

        self.ui.splitter.replaceWidget(1, self.ui.htmlPreview)
        old_preview.deleteLater()

        self.ui.splitter.setSizes([600, 600])

        font_path = Path(__file__).parent / "fonts" / "JetBrainsMono-Regular.ttf"
        font_id = QFontDatabase.addApplicationFont(str(font_path))
        font_families = QFontDatabase.applicationFontFamilies(font_id)
        font = QFont(font_families[0], 11)
        font.setFixedPitch(True)
        font.setStyleHint(QFont.StyleHint.Monospace)
        self.ui.markdownEditor.setFont(font)

        self.ui.markdownEditor.textChanged.connect(self.on_text_changed)

        self.ui.actionNew.triggered.connect(self.new_file)
        self.ui.actionOpen.triggered.connect(self.open_file)
        self.ui.actionSave.triggered.connect(self.save_file)
        self.ui.actionSaveAs.triggered.connect(self.save_file_as)
        self.ui.actionExit.triggered.connect(self.close)

        self.ui.actionUndo.triggered.connect(self.ui.markdownEditor.undo)
        self.ui.actionRedo.triggered.connect(self.ui.markdownEditor.redo)
        self.ui.actionCut.triggered.connect(self.ui.markdownEditor.cut)
        self.ui.actionCopy.triggered.connect(self.ui.markdownEditor.copy)
        self.ui.actionPaste.triggered.connect(self.ui.markdownEditor.paste)

        self.ui.actionBold.triggered.connect(lambda: self.insert_formatting('**', '**'))
        self.ui.actionItalic.triggered.connect(lambda: self.insert_formatting('*', '*'))
        self.ui.actionStrikethrough.triggered.connect(lambda: self.insert_formatting('~~', '~~'))
        self.ui.actionHeading.triggered.connect(lambda: self.insert_formatting('## ', ''))
        self.ui.actionLink.triggered.connect(lambda: self.insert_formatting('[', '](url)'))
        self.ui.actionImage.triggered.connect(lambda: self.insert_formatting('![', '](url)'))
        self.ui.actionCode.triggered.connect(lambda: self.insert_formatting('`', '`'))

        self.setup_preview_css()

        initial_html = self.preview_css + self.preview_css_footer
        self.ui.htmlPreview.setHtml(initial_html)
        self.ui.htmlPreview.loadFinished.connect(self.on_initial_load, Qt.ConnectionType.SingleShotConnection)

    def on_initial_load(self):
        self.load_example()

    def setup_preview_css(self):
        font_base64_path = Path(__file__).parent / "assets" / "jetbrains-mono-base64.txt"
        with open(font_base64_path, 'r') as f:
            font_base64 = f.read().strip()

        hljs_css_path = Path(__file__).parent / "assets" / "github.min.css"
        hljs_js_path = Path(__file__).parent / "assets" / "highlight.min.js"

        with open(hljs_css_path, 'r') as f:
            hljs_css = f.read()

        with open(hljs_js_path, 'r') as f:
            hljs_js = f.read()

        self.preview_css = f"""
        <!DOCTYPE html>
        <html>
        <head>
        <meta charset="UTF-8">
        <style>
            @font-face {{
                font-family: 'JetBrains Mono';
                src: url(data:font/ttf;base64,{font_base64}) format('truetype');
                font-weight: normal;
                font-style: normal;
            }}

            {hljs_css}
        </style>
        <script>
            {hljs_js}
        </script>
        <script>
            document.addEventListener('DOMContentLoaded', (event) => {{
                document.querySelectorAll('pre code').forEach((el) => {{
                    hljs.highlightElement(el);
                }});
            }});
        </script>
        <style>
            body {{
                font-family: 'JetBrains Mono', monospace;
                line-height: 1.6;
                padding: 20px;
                max-width: 900px;
                margin: 0 auto;
            }}
            h1, h2, h3, h4, h5, h6 {{
                margin-top: 24px;
                margin-bottom: 16px;
                font-weight: 600;
                line-height: 1.25;
            }}
            h1 {{ font-size: 2em; }}
            h2 {{ font-size: 1.5em; }}
            h3 {{ font-size: 1.25em; }}
            code {{
                background-color: #f6f8fa;
                padding: 2px 6px;
                border-radius: 3px;
                font-family: 'JetBrains Mono', monospace;
            }}
            pre {{
                background-color: #f6f8fa;
                padding: 16px;
                border-radius: 6px;
                overflow: auto;
            }}
            pre code {{
                background-color: transparent;
                padding: 0;
            }}
            blockquote {{
                margin: 0;
                padding-left: 1em;
                border-left: 4px solid #ddd;
                color: #666;
            }}
            table {{
                border-collapse: collapse;
                width: 100%;
                margin: 16px 0;
            }}
            th, td {{
                border: 1px solid #ddd;
                padding: 8px 12px;
            }}
            th {{
                background-color: #f6f8fa;
                font-weight: 600;
            }}
            img {{
                max-width: 100%;
            }}
            hr {{
                border: none;
                border-top: 2px solid #eee;
                margin: 24px 0;
            }}
            a {{
                color: #0366d6;
                text-decoration: none;
            }}
            a:hover {{
                text-decoration: underline;
            }}
        </style>
        </head>
        <body>
        """
        self.preview_css_footer = """
        </body>
        </html>
        """

    def on_text_changed(self):
        self.is_modified = True
        self.update_window_title()
        self.update_preview()

    def update_preview(self):
        markdown_text = self.ui.markdownEditor.toPlainText()

        if not markdown_text:
            html_body = "<p>Preview will appear here...</p>"
        else:
            try:
                tokens = tokenize(markdown_text)
                blocks = parse_blocks(tokens)
                html_body = render_html(blocks)
            except Exception as e:
                html_body = f"<p style='color: red;'>Error rendering markdown: {str(e)}</p>"

        escaped_html = html_body.replace('\\', '\\\\').replace('`', '\\`').replace('${', '\\${')

        js_update_content = f"""
        (function() {{
            document.body.innerHTML = `{escaped_html}`;
            document.querySelectorAll('pre code').forEach((el) => {{
                hljs.highlightElement(el);
            }});
        }})()
        """
        self.ui.htmlPreview.page().runJavaScript(js_update_content)

    def insert_formatting(self, prefix: str, suffix: str):
        cursor = self.ui.markdownEditor.textCursor()

        if cursor.hasSelection():
            selected_text = cursor.selectedText()
            cursor.insertText(prefix + selected_text + suffix)
        else:
            cursor.insertText(prefix + suffix)
            cursor.movePosition(QTextCursor.MoveOperation.Left, n=len(suffix))
        self.ui.markdownEditor.setTextCursor(cursor)

    def new_file(self):
        if self.is_modified and not self.confirm_discard_changes():
            return

        self.ui.markdownEditor.clear()
        self.current_file = None
        self.is_modified = False
        self.update_window_title()

    def open_file(self):
        if self.is_modified and not self.confirm_discard_changes():
            return

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Markdown File",
            "",
            "Markdown Files (*.md);;All Files (*)"
        )

        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                self.ui.markdownEditor.setPlainText(content)
                self.current_file = file_path
                self.is_modified = False
                self.update_window_title()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not open file: {str(e)}")

    def save_file(self):
        if self.current_file:
            return self.save_to_file(self.current_file)
        else:
            return self.save_file_as()

    def save_file_as(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Markdown File",
            "",
            "Markdown Files (*.md);;All Files (*)"
        )

        if file_path:
            return self.save_to_file(file_path)
        return False

    def save_to_file(self, file_path: str):
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(self.ui.markdownEditor.toPlainText())

            self.current_file = file_path
            self.is_modified = False
            self.update_window_title()
            self.ui.statusbar.showMessage(f"Saved to {file_path}", 3000)
            return True
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not save file: {str(e)}")
            return False

    def load_example(self):
        example_path = Path(__file__).parent.parent.parent / "examples" / "example.md"

        if example_path.exists():
            try:
                with open(example_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.ui.markdownEditor.setPlainText(content)
                self.current_file = None
                self.is_modified = False
                self.update_window_title()
            except:
                pass

    def confirm_discard_changes(self):
        reply = QMessageBox.question(
            self,
            "Unsaved Changes",
            "You have unsaved changes. Do you want to discard them?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        return reply == QMessageBox.StandardButton.Yes

    def update_window_title(self):
        title = "Markdown Editor"

        if self.current_file:
            title = f"{Path(self.current_file).name} - {title}"
        else:
            title = f"Untitled - {title}"

        if self.is_modified:
            title = f"*{title}"

        self.setWindowTitle(title)

    def closeEvent(self, event):
        if self.is_modified and not self.confirm_discard_changes():
            event.ignore()
        else:
            event.accept()


def main():
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts)
    app = QApplication(sys.argv)
    window = MarkdownEditor()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
