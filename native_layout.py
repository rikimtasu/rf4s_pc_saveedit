"""Small-window Qt layout helpers. Reflow never replaces editor controls."""
from PySide6.QtCore import QEvent, QSize, Qt
from PySide6.QtWidgets import QWidget, QBoxLayout, QCheckBox, QLabel, QHBoxLayout, QSizePolicy


class ResponsiveRow(QWidget):
    """Stack a row when its captions/controls no longer fit side by side."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.box = QBoxLayout(QBoxLayout.Direction.LeftToRight, self)
        self.box.setContentsMargins(0, 0, 0, 0)
        self.box.setSpacing(8)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)

    def addWidget(self, widget, stretch=0):
        self.box.addWidget(widget, stretch)

    def minimumSizeHint(self):
        size = super().minimumSizeHint()
        return QSize(0, size.height())

    def reflow(self):
        if not hasattr(self, 'box'): return
        needed = sum(self.box.itemAt(index).widget().sizeHint().width() for index in range(self.box.count())) + max(0, self.box.count() - 1) * self.box.spacing()
        direction = QBoxLayout.Direction.LeftToRight if self.width() >= needed else QBoxLayout.Direction.TopToBottom
        if self.box.direction() != direction: self.box.setDirection(direction)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.reflow()

    def event(self, event):
        result = super().event(event)
        if event.type() in (QEvent.Type.LayoutRequest, QEvent.Type.FontChange): self.reflow()
        return result


class CheckCaption(QLabel):
    def __init__(self, text, checkbox):
        super().__init__(text)
        self.checkbox = checkbox
        self.setWordWrap(True)
        self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        self.setBuddy(checkbox)
        checkbox.setAccessibleName(text)

    def setText(self, text):
        super().setText(text)
        if hasattr(self, 'checkbox'): self.checkbox.setAccessibleName(text)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.checkbox.isEnabled():
            self.checkbox.setFocus()
            self.checkbox.click()
            event.accept()
        else: super().mouseReleaseEvent(event)


def wrapping_checkbox(text):
    checkbox = QCheckBox()
    row = QWidget()
    layout = QHBoxLayout(row)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.addWidget(checkbox, 0, Qt.AlignmentFlag.AlignTop)
    layout.addWidget(CheckCaption(text, checkbox), 1)
    return checkbox, row
