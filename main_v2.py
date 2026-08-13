import sys
import os
from pathlib import Path

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QKeySequence, QShortcut, QIcon
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QListWidget, QListWidgetItem,
    QFileDialog, QComboBox, QSlider, QMessageBox, QSplitter,
    QFrame
)

import pygame

AUDIO_EXTENSIONS = {
    ".wav", ".mp3", ".ogg", ".flac", ".aac", ".m4a", ".wma"
}


class Scanner(QThread):
    found = Signal(str, str, str)  # full path, relative path, category
    finished = Signal(int)

    def __init__(self, root):
        super().__init__()
        self.root = Path(root)

    def run(self):
        count = 0
        try:
            for path in self.root.rglob("*"):
                if path.is_file() and path.suffix.lower() in AUDIO_EXTENSIONS:
                    try:
                        relative = path.relative_to(self.root)
                        parts = relative.parts
                        category = parts[0] if len(parts) > 1 else "Root"
                        self.found.emit(str(path), str(relative), category)
                        count += 1
                    except (OSError, ValueError):
                        pass
        finally:
            self.finished.emit(count)


class AudioLibrary(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Audio Library Browser")
        self.resize(1100, 700)

        self.root_folder = None
        self.sounds = []
        self.current_path = None
        self.current_index = -1
        self.visible_sounds = []

        pygame.mixer.init()

        self.build_ui()
        self.setup_shortcuts()

    def build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main = QVBoxLayout(central)
        main.setContentsMargins(14, 14, 14, 14)
        main.setSpacing(10)

        # Top bar
        top = QHBoxLayout()
        title = QLabel("🔊  Audio Library Browser")
        title.setStyleSheet("font-size: 20px; font-weight: 700;")
        top.addWidget(title)

        top.addStretch()

        self.folder_label = QLabel("No folder selected")
        self.folder_label.setStyleSheet("color: #888;")
        top.addWidget(self.folder_label)

        choose = QPushButton("Choose Library")
        choose.clicked.connect(self.choose_folder)
        top.addWidget(choose)

        main.addLayout(top)

        # Search/filter row
        filters = QHBoxLayout()

        self.search = QLineEdit()
        self.search.setPlaceholderText("Search sounds...")
        self.search.textChanged.connect(self.refresh_list)
        filters.addWidget(self.search, 2)

        self.category = QComboBox()
        self.category.addItem("All Categories")
        self.category.currentTextChanged.connect(self.refresh_list)
        filters.addWidget(self.category, 1)

        main.addLayout(filters)

        # Main content
        splitter = QSplitter(Qt.Horizontal)

        left = QFrame()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(8, 8, 8, 8)

        self.count_label = QLabel("0 sounds")
        self.count_label.setStyleSheet("font-weight: 600;")
        left_layout.addWidget(self.count_label)

        self.list = QListWidget()
        self.list.setAlternatingRowColors(True)
        self.list.itemDoubleClicked.connect(self.play_selected)
        self.list.currentRowChanged.connect(self.selection_changed)
        left_layout.addWidget(self.list)

        splitter.addWidget(left)

        # Right details/player panel
        right = QFrame()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(20, 20, 20, 20)

        self.name_label = QLabel("Select a sound")
        self.name_label.setWordWrap(True)
        self.name_label.setStyleSheet("font-size: 22px; font-weight: 700;")
        right_layout.addWidget(self.name_label)

        self.path_label = QLabel("")
        self.path_label.setWordWrap(True)
        self.path_label.setStyleSheet("color: #888;")
        right_layout.addWidget(self.path_label)

        right_layout.addStretch()

        controls = QHBoxLayout()

        self.prev_btn = QPushButton("◀ Previous")
        self.prev_btn.clicked.connect(self.previous_sound)
        controls.addWidget(self.prev_btn)

        self.play_btn = QPushButton("▶ Play")
        self.play_btn.clicked.connect(self.toggle_play)
        self.play_btn.setMinimumHeight(42)
        controls.addWidget(self.play_btn)

        self.stop_btn = QPushButton("■ Stop")
        self.stop_btn.clicked.connect(self.stop)
        controls.addWidget(self.stop_btn)

        self.next_btn = QPushButton("Next ▶")
        self.next_btn.clicked.connect(self.next_sound)
        controls.addWidget(self.next_btn)

        right_layout.addLayout(controls)

        volume_row = QHBoxLayout()
        volume_row.addWidget(QLabel("Volume"))
        self.volume = QSlider(Qt.Horizontal)
        self.volume.setRange(0, 100)
        self.volume.setValue(80)
        self.volume.valueChanged.connect(self.set_volume)
        volume_row.addWidget(self.volume)
        right_layout.addLayout(volume_row)

        hint = QLabel("Space: play/pause   ↑/↓: navigate   Enter: play   Esc: stop")
        hint.setStyleSheet("color: #888;")
        right_layout.addWidget(hint)

        splitter.addWidget(right)
        splitter.setSizes([650, 350])

        main.addWidget(splitter, 1)

        self.status = QLabel("Choose your audio collection folder to begin.")
        self.status.setStyleSheet("color: #888;")
        main.addWidget(self.status)

    def setup_shortcuts(self):
        QShortcut(QKeySequence(Qt.Key_Space), self, activated=self.toggle_play)
        QShortcut(QKeySequence(Qt.Key_Return), self, activated=self.play_selected)
        QShortcut(QKeySequence(Qt.Key_Enter), self, activated=self.play_selected)
        QShortcut(QKeySequence(Qt.Key_Escape), self, activated=self.stop)
        QShortcut(QKeySequence(Qt.Key_Up), self, activated=self.previous_sound)
        QShortcut(QKeySequence(Qt.Key_Down), self, activated=self.next_sound)

    def choose_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self, "Choose Audio Library Folder"
        )
        if not folder:
            return

        self.root_folder = folder
        self.folder_label.setText(folder)
        self.sounds.clear()
        self.category.blockSignals(True)
        self.category.clear()
        self.category.addItem("All Categories")
        self.category.blockSignals(False)
        self.list.clear()
        self.status.setText("Scanning audio files...")
        self.search.clear()

        self.scanner = Scanner(folder)
        self.scanner.found.connect(self.add_sound)
        self.scanner.finished.connect(self.scan_finished)
        self.scanner.start()

    def add_sound(self, full_path, relative, category):
        self.sounds.append({
            "path": full_path,
            "relative": relative,
            "category": category,
        })

    def scan_finished(self, count):
        categories = sorted({s["category"] for s in self.sounds}, key=str.lower)
        self.category.blockSignals(True)
        self.category.clear()
        self.category.addItem("All Categories")
        self.category.addItems(categories)
        self.category.blockSignals(False)

        self.sounds.sort(key=lambda x: x["relative"].lower())
        self.refresh_list()
        self.status.setText(f"Ready — scanned {count:,} audio files.")

    def refresh_list(self):
        if not hasattr(self, "list"):
            return

        query = self.search.text().strip().lower()
        selected_category = self.category.currentText()

        self.list.blockSignals(True)
        self.list.clear()
        self.visible_sounds = []

        shown = 0
        current_folder = None

        for sound in self.sounds:
            if selected_category != "All Categories" and sound["category"] != selected_category:
                continue

            if query and query not in sound["relative"].lower():
                continue

            relative = Path(sound["relative"])
            folder = str(relative.parent)

            # Keep the root-level files together under a clear heading.
            if folder == ".":
                folder = "Root"

            if folder != current_folder:
                current_folder = folder

                heading = QListWidgetItem(f"📁  {folder}")
                heading.setFlags(Qt.ItemIsEnabled)
                heading.setData(Qt.UserRole, None)
                heading.setToolTip(folder)
                self.list.addItem(heading)

            item = QListWidgetItem(f"▶  {relative.name}")
            item.setToolTip(sound["relative"])
            item.setData(Qt.UserRole, sound["path"])
            self.list.addItem(item)
            self.visible_sounds.append(sound)
            shown += 1

        self.list.blockSignals(False)
        self.count_label.setText(f"{shown:,} sounds")

        if shown == 0:
            self.current_path = None
            self.name_label.setText("No sounds found")
            self.path_label.setText("")

    def selection_changed(self, row):
        if row < 0:
            return
        item = self.list.item(row)
        if not item:
            return

        path = item.data(Qt.UserRole)

        # Folder heading — nothing to select.
        if not path:
            return

        self.current_path = path

        self.name_label.setText(Path(path).name)
        try:
            rel = str(Path(path).relative_to(self.root_folder))
        except Exception:
            rel = path
        self.path_label.setText(rel)

    def play_selected(self):
        item = self.list.currentItem()
        if not item:
            return

        path = item.data(Qt.UserRole)

        # Folder heading — nothing to play.
        if not path:
            return

        self.current_path = path

        try:
            pygame.mixer.music.load(path)
            pygame.mixer.music.play()
            self.play_btn.setText("❚❚ Pause")
            self.status.setText(f"Playing: {Path(path).name}")
        except Exception as e:
            QMessageBox.warning(
                self,
                "Can't play this file",
                f"Could not play:\n{path}\n\n{e}"
            )

    def toggle_play(self):
        if not self.current_path:
            self.play_selected()
            return

        if pygame.mixer.music.get_busy():
            pygame.mixer.music.pause()
            self.play_btn.setText("▶ Resume")
        else:
            # pygame cannot reliably tell whether the track is paused,
            # so restart if no channel is active.
            self.play_selected()

    def stop(self):
        pygame.mixer.music.stop()
        self.play_btn.setText("▶ Play")

    def previous_sound(self):
        row = self.list.currentRow()

        while row > 0:
            row -= 1
            item = self.list.item(row)
            if item and item.data(Qt.UserRole):
                self.list.setCurrentRow(row)
                self.play_selected()
                return

    def next_sound(self):
        row = self.list.currentRow()

        while row < self.list.count() - 1:
            row += 1
            item = self.list.item(row)
            if item and item.data(Qt.UserRole):
                self.list.setCurrentRow(row)
                self.play_selected()
                return

    def set_volume(self, value):
        pygame.mixer.music.set_volume(value / 100.0)

    def closeEvent(self, event):
        try:
            pygame.mixer.music.stop()
            pygame.mixer.quit()
        finally:
            event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("Audio Library Browser")

    window = AudioLibrary()
    window.show()

    sys.exit(app.exec())
