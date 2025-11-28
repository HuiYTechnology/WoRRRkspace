"""Переделать!!!"""

import os
import csv
import json
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
                             QTableWidgetItem, QPushButton, QLineEdit, QLabel,
                             QHeaderView, QFileDialog, QMessageBox)
from PyQt6.QtCore import Qt

class TableEditorTab(QWidget):
    """Вкладка для редактирования таблиц"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        toolbar = QHBoxLayout()
        toolbar.setSpacing(4)

        self.btn_add_row = QPushButton("➕ Строка")
        self.btn_add_col = QPushButton("➕ Столбец")
        self.btn_del_row = QPushButton("➖ Строка")
        self.btn_del_col = QPushButton("➖ Столбец")
        self.btn_import = QPushButton("📁 Импорт")
        self.btn_export = QPushButton("💾 Экспорт")
        self.btn_save = QPushButton("💾 Сохранить")

        self.btn_add_row.setToolTip("Добавить строку")
        self.btn_add_col.setToolTip("Добавить столбец")
        self.btn_del_row.setToolTip("Удалить строку")
        self.btn_del_col.setToolTip("Удалить столбец")
        self.btn_import.setToolTip("Импорт из CSV/JSON")
        self.btn_export.setToolTip("Экспорт в CSV/JSON")
        self.btn_save.setToolTip("Сохранить таблицу")

        toolbar.addWidget(self.btn_add_row)
        toolbar.addWidget(self.btn_add_col)
        toolbar.addWidget(self.btn_del_row)
        toolbar.addWidget(self.btn_del_col)
        toolbar.addWidget(self.btn_import)
        toolbar.addWidget(self.btn_export)
        toolbar.addStretch()
        toolbar.addWidget(self.btn_save)

        cell_info_layout = QHBoxLayout()
        cell_info_layout.setSpacing(8)

        self.cell_info_label = QLabel("Выбранная ячейка:")
        self.cell_position_label = QLabel("A1")
        self.cell_value_input = QLineEdit()
        self.cell_value_input.setPlaceholderText("Значение ячейки...")

        cell_info_layout.addWidget(self.cell_info_label)
        cell_info_layout.addWidget(self.cell_position_label)
        cell_info_layout.addWidget(self.cell_value_input, 1)

        self.table = QTableWidget()
        self.table.setRowCount(10)
        self.table.setColumnCount(5)

        self.update_column_headers()

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        header.setMinimumSectionSize(120)

        self.table.verticalHeader().setDefaultSectionSize(30)
        self.table.setAlternatingRowColors(True)

        layout.addLayout(toolbar)
        layout.addLayout(cell_info_layout)
        layout.addWidget(self.table)

        self.setup_connections()

    def number_to_excel_column(self, n):
        result = ""
        while n > 0:
            n, remainder = divmod(n - 1, 26)
            result = chr(65 + remainder) + result
        return result

    def update_column_headers(self):
        column_count = self.table.columnCount()
        headers = []
        for i in range(column_count):
            headers.append(self.number_to_excel_column(i + 1))
        self.table.setHorizontalHeaderLabels(headers)

    def get_cell_position(self, row, column):
        col_name = self.number_to_excel_column(column + 1)
        return f"{col_name}{row + 1}"

    def setup_connections(self):
        self.btn_add_row.clicked.connect(self.add_row)
        self.btn_add_col.clicked.connect(self.add_column)
        self.btn_del_row.clicked.connect(self.delete_row)
        self.btn_del_col.clicked.connect(self.delete_column)
        self.btn_import.clicked.connect(self.import_data)
        self.btn_export.clicked.connect(self.export_data)
        self.btn_save.clicked.connect(self.save_table)

        self.table.currentCellChanged.connect(self.on_cell_changed)
        self.table.cellChanged.connect(self.on_cell_edited)
        self.cell_value_input.textChanged.connect(self.on_cell_value_changed)
        self.cell_value_input.returnPressed.connect(self.apply_cell_value)

    def on_cell_changed(self, current_row, current_column, previous_row, previous_column):
        if current_row >= 0 and current_column >= 0:
            cell_position = self.get_cell_position(current_row, current_column)
            self.cell_position_label.setText(cell_position)

            item = self.table.item(current_row, current_column)
            self.cell_value_input.blockSignals(True)
            self.cell_value_input.setText(item.text() if item else "")
            self.cell_value_input.blockSignals(False)

    def on_cell_edited(self, row, column):
        current_row = self.table.currentRow()
        current_column = self.table.currentColumn()

        if row == current_row and column == current_column:
            item = self.table.item(row, column)
            if item:
                self.cell_value_input.blockSignals(True)
                self.cell_value_input.setText(item.text())
                self.cell_value_input.blockSignals(False)

    def on_cell_value_changed(self, text):
        self.table.blockSignals(True)

        current_row = self.table.currentRow()
        current_column = self.table.currentColumn()

        if current_row >= 0 and current_column >= 0:
            item = self.table.item(current_row, current_column)
            if item:
                item.setText(text)
            else:
                new_item = QTableWidgetItem(text)
                self.table.setItem(current_row, current_column, new_item)

        self.table.blockSignals(False)

    def apply_cell_value(self):
        text = self.cell_value_input.text()
        self.on_cell_value_changed(text)

    def add_row(self):
        current_row_count = self.table.rowCount()
        self.table.insertRow(current_row_count)

    def add_column(self):
        current_col_count = self.table.columnCount()
        self.table.insertColumn(current_col_count)
        self.update_column_headers()

    def delete_row(self):
        current_row = self.table.currentRow()
        if current_row >= 0:
            self.table.removeRow(current_row)
        else:
            self.show_warning("Выберите строку для удаления")

    def delete_column(self):
        current_col = self.table.currentColumn()
        if current_col >= 0:
            self.table.removeColumn(current_col)
            self.update_column_headers()
        else:
            self.show_warning("Выберите столбец для удаления")

    def import_data(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Импорт данных", "", "CSV Files (*.csv);;JSON Files (*.json)"
        )

        if file_path:
            try:
                if file_path.endswith('.csv'):
                    self.import_csv(file_path)
                elif file_path.endswith('.json'):
                    self.import_json(file_path)

                self.update_column_headers()

                if hasattr(self, "parent") and hasattr(self.parent(), "status_bar"):
                    self.parent().status_bar.showMessage(f"Данные импортированы из {os.path.basename(file_path)}", 3000)
            except Exception as e:
                self.show_error(f"Ошибка импорта: {str(e)}")

    def import_csv(self, file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            reader = csv.reader(file)
            data = list(reader)

        if data:
            self.table.setRowCount(0)
            self.table.setColumnCount(len(data[0]))

            for row_idx, row in enumerate(data):
                self.table.insertRow(row_idx)
                for col_idx, value in enumerate(row):
                    self.table.setItem(row_idx, col_idx, QTableWidgetItem(value))

    def import_json(self, file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)

        if isinstance(data, list) and data:
            self.table.setRowCount(0)
            first_row = data[0]
            if isinstance(first_row, dict):
                columns = list(first_row.keys())
                self.table.setColumnCount(len(columns))

                for row_idx, row_data in enumerate(data):
                    self.table.insertRow(row_idx)
                    for col_idx, key in enumerate(columns):
                        value = str(row_data.get(key, ""))
                        self.table.setItem(row_idx, col_idx, QTableWidgetItem(value))

    def export_data(self):
        file_path, selected_filter = QFileDialog.getSaveFileName(
            self, "Экспорт данных", "", "CSV Files (*.csv);;JSON Files (*.json)"
        )

        if file_path:
            try:
                if selected_filter == "CSV Files (*.csv)":
                    if not file_path.endswith('.csv'):
                        file_path += '.csv'
                    self.export_csv(file_path)
                elif selected_filter == "JSON Files (*.json)":
                    if not file_path.endswith('.json'):
                        file_path += '.json'
                    self.export_json(file_path)

                if hasattr(self, "parent") and hasattr(self.parent(), "status_bar"):
                    self.parent().status_bar.showMessage(f"Данные экспортированы в {os.path.basename(file_path)}", 3000)
            except Exception as e:
                self.show_error(f"Ошибка экспорта: {str(e)}")

    def export_csv(self, file_path):
        with open(file_path, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)

            for row in range(self.table.rowCount()):
                row_data = []
                for col in range(self.table.columnCount()):
                    item = self.table.item(row, col)
                    row_data.append(item.text() if item else "")
                writer.writerow(row_data)

    def export_json(self, file_path):
        data = []
        headers = []
        for col in range(self.table.columnCount()):
            headers.append(self.table.horizontalHeaderItem(col).text() if self.table.horizontalHeaderItem(
                col) else f"Column_{col}")

        for row in range(self.table.rowCount()):
            row_data = {}
            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                row_data[headers[col]] = item.text() if item else ""
            data.append(row_data)

        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=2)

    def save_table(self):
        print("Сохранение таблицы в БД...")
        if hasattr(self, "parent") and hasattr(self.parent(), "status_bar"):
            self.parent().status_bar.showMessage("Таблица сохранена", 2000)

    def show_warning(self, message):
        QMessageBox.warning(self, "Предупреждение", message)

    def show_error(self, message):
        QMessageBox.critical(self, "Ошибка", message)