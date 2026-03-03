from PyQt5.QtWidgets import QFrame, QHBoxLayout


def validate_path(path):
    return path and path.strip() != ""

def visualize_grid(grid_layout):
    """Wrap each widget in a QFrame to show cell boundaries"""
    # Store items to process (can't modify while iterating)
    items_to_wrap = []
    for i in range(grid_layout.count()):
        item = grid_layout.itemAt(i)
        if item and item.widget():
            items_to_wrap.append((i, item.widget()))

    # Wrap each widget in a frame
    for i, widget in items_to_wrap:
        # Get position
        index = grid_layout.indexOf(widget)
        if index == -1:
            continue

        row, col, row_span, col_span = grid_layout.getItemPosition(index)

        # Remove widget from layout
        grid_layout.removeWidget(widget)

        # Create frame container
        frame = QFrame()
        frame.setFrameStyle(QFrame.Box | QFrame.Plain)
        frame.setLineWidth(1)
        frame.setStyleSheet("border-color: red;")

        # Put widget inside frame
        frame_layout = QHBoxLayout(frame)
        frame_layout.setContentsMargins(0, 0, 0, 0)
        frame_layout.addWidget(widget)

        # Add frame back to grid
        grid_layout.addWidget(frame, row, col, row_span, col_span)

def set_property_and_update(field, property, value):
    field.setProperty(property, value)
    field.style().unpolish(field)
    field.style().polish(field)
    field.update()