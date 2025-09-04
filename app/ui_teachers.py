"""UI management module for teacher-related functionality.

This module handles the display and updates of teacher information in the UI,
particularly focusing on the teacher table widget.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHeaderView, QTableWidget, QTableWidgetItem, QWidget

from app.config.logging_config import get_logger
from app.utils import get_translations

logger = get_logger(__name__)


def refresh_teacher_table(window: QWidget, data: dict) -> None:
    """Refresh the teacher table with updated data.

    Args:
        window: Main application window instance
        data (dict): Application data containing teacher information
    """
    table = window.findChild(QTableWidget, "tableTeachers")
    if data:
        teachers = data.get("teachers", {})
    else:
        teachers = {}

    table.setRowCount(len(teachers))
    table.setColumnCount(2)
    table.setHorizontalHeaderLabels([get_translations("name"), get_translations("availability")])
    table.horizontalHeader().setStretchLastSection(True)
    table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

    for row, (name, info) in enumerate(teachers.items()):
        availability = info.get("availability", {})
        avail_text = []
        for day, slots in availability.items():
            slot_text = ", ".join(f"{start}–{end}" for start, end in slots)
            avail_text.append(f"{day}: {slot_text}")

        table.setItem(row, 0, QTableWidgetItem(name))
        item = QTableWidgetItem("\n".join(avail_text))
        item.setTextAlignment(Qt.AlignTop)
        table.setItem(row, 1, item)

    table.setWordWrap(False)
    table.resizeRowsToContents()


def refresh_children_table(window: QWidget, data: dict) -> None:
    """Refresh the children table with updated data.

    Args:
        window: Main application window instance
        data (dict): Application data containing children information
    """
    table = window.findChild(QTableWidget, "tableChildren")
    if data:
        children = data.get("children", {})
    else:
        children = {}

    table.setRowCount(len(children))
    table.setColumnCount(4)
    table.setHorizontalHeaderLabels(
        [
            get_translations("name"),
            get_translations("early_preference"),
            get_translations("preferred_teachers"),
            get_translations("availability"),
        ]
    )
    table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

    for row, (name, info) in enumerate(children.items()):
        # Name
        table.setItem(row, 0, QTableWidgetItem(name))

        # Early preference
        early_pref = get_translations("yes") if info.get("early_preference", False) else get_translations("no")
        table.setItem(row, 1, QTableWidgetItem(early_pref))

        # Preferred teachers
        preferred = ", ".join(info.get("preferred_teachers", []))
        table.setItem(row, 2, QTableWidgetItem(preferred))

        # Availability
        availability = info.get("availability", {})
        avail_text = []
        for day, slots in availability.items():
            slot_text = ", ".join(f"{start}–{end}" for start, end in slots)
            avail_text.append(f"{day}: {slot_text}")

        item = QTableWidgetItem("\n".join(avail_text))
        item.setTextAlignment(Qt.AlignTop)
        table.setItem(row, 3, item)

    table.resizeRowsToContents()


def refresh_tandems_table(window: QWidget, data: dict) -> None:
    """Refresh the tandems table with updated data.

    Args:
        window: Main application window instance
        data (dict): Application data containing tandems information
    """
    table = window.findChild(QTableWidget, "tableTandems")
    if data:
        tandems = data.get("tandems", {})
    else:
        tandems = {}

    table.setRowCount(len(tandems))
    table.setColumnCount(4)
    table.setHorizontalHeaderLabels(
        [
            get_translations("tandem_name"),
            get_translations("child_1"),
            get_translations("child_2"),
            get_translations("priority"),
        ]
    )
    table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

    for row, (name, info) in enumerate(tandems.items()):
        # Tandem name
        table.setItem(row, 0, QTableWidgetItem(name))

        # Child 1
        table.setItem(row, 1, QTableWidgetItem(info.get("child1", "")))

        # Child 2
        table.setItem(row, 2, QTableWidgetItem(info.get("child2", "")))

        # Priority
        priority = str(info.get("priority", 5))
        table.setItem(row, 3, QTableWidgetItem(priority))

    table.resizeRowsToContents()
