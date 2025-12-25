from PyQt5.QtWidgets import QTableWidget

def clear_table(table: QTableWidget) -> None:
    table.setRowCount(0)


def set_table_row(table: QTableWidget, row_index: int, values: list[str]) -> None:
    table.insertRow(row_index)
    for col, value in enumerate(values):
        item = table.item(row_index, col)
        if item is None:
            from PyQt5.QtWidgets import QTableWidgetItem

            item = QTableWidgetItem()
            table.setItem(row_index, col, item)
        item.setText(value)