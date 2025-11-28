"""Хз будет ли это в итоговом варианте"""

import json
from datetime import datetime, date
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QComboBox, QLineEdit, QTableWidget,
                             QTableWidgetItem, QHeaderView, QFileDialog,
                             QMessageBox, QDialog, QTextEdit, QDateEdit,
                             QCheckBox, QListWidget, QListWidgetItem)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QColor

class TaskDialog(QDialog):
    """Диалог для создания/редактирования задачи"""

    def __init__(self, task_data=None, parent=None):
        super().__init__(parent)
        self.task_data = task_data or {}
        self.setup_ui()
        self.load_task_data()

    def setup_ui(self):
        self.setWindowTitle("Редактирование задачи")
        self.setMinimumSize(500, 600)

        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Заголовок:"))
        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("Введите заголовок задачи...")
        layout.addWidget(self.title_edit)

        layout.addWidget(QLabel("Описание:"))
        self.description_edit = QTextEdit()
        self.description_edit.setPlaceholderText("Введите описание задачи...")
        self.description_edit.setMaximumHeight(120)
        layout.addWidget(self.description_edit)

        status_priority_layout = QHBoxLayout()

        status_priority_layout.addWidget(QLabel("Статус:"))
        self.status_combo = QComboBox()
        self.status_combo.addItems(["К выполнению", "В процессе", "На проверке", "Выполнено"])
        status_priority_layout.addWidget(self.status_combo)

        status_priority_layout.addWidget(QLabel("Приоритет:"))
        self.priority_combo = QComboBox()
        self.priority_combo.addItems(["Низкий", "Средний", "Высокий", "Критический"])
        status_priority_layout.addWidget(self.priority_combo)

        layout.addLayout(status_priority_layout)

        due_date_layout = QHBoxLayout()
        due_date_layout.addWidget(QLabel("Срок выполнения:"))
        self.due_date_edit = QDateEdit()
        self.due_date_edit.setDate(QDate.currentDate().addDays(7))
        self.due_date_edit.setCalendarPopup(True)
        due_date_layout.addWidget(self.due_date_edit)

        self.completed_check = QCheckBox("Выполнено")
        due_date_layout.addWidget(self.completed_check)

        layout.addLayout(due_date_layout)

        time_layout = QHBoxLayout()
        time_layout.addWidget(QLabel("Оценка часов:"))
        self.estimated_hours_edit = QLineEdit()
        self.estimated_hours_edit.setPlaceholderText("0.0")
        time_layout.addWidget(self.estimated_hours_edit)

        time_layout.addWidget(QLabel("Факт часов:"))
        self.actual_hours_edit = QLineEdit()
        self.actual_hours_edit.setPlaceholderText("0.0")
        time_layout.addWidget(self.actual_hours_edit)

        layout.addLayout(time_layout)

        layout.addWidget(QLabel("Подзадачи:"))
        subtasks_layout = QHBoxLayout()

        self.subtask_edit = QLineEdit()
        self.subtask_edit.setPlaceholderText("Введите подзадачу...")
        subtasks_layout.addWidget(self.subtask_edit)

        self.add_subtask_btn = QPushButton("➕")
        self.add_subtask_btn.setToolTip("Добавить подзадачу")
        self.add_subtask_btn.clicked.connect(self.add_subtask)
        subtasks_layout.addWidget(self.add_subtask_btn)

        layout.addLayout(subtasks_layout)

        self.subtasks_list = QListWidget()
        layout.addWidget(self.subtasks_list)

        subtask_buttons_layout = QHBoxLayout()
        self.remove_subtask_btn = QPushButton("Удалить подзадачу")
        self.remove_subtask_btn.clicked.connect(self.remove_subtask)
        subtask_buttons_layout.addWidget(self.remove_subtask_btn)

        self.toggle_subtask_btn = QPushButton("Переключить выполнение")
        self.toggle_subtask_btn.clicked.connect(self.toggle_subtask)
        subtask_buttons_layout.addWidget(self.toggle_subtask_btn)

        layout.addLayout(subtask_buttons_layout)

        button_layout = QHBoxLayout()
        self.save_btn = QPushButton("💾 Сохранить")
        self.save_btn.clicked.connect(self.accept)

        self.cancel_btn = QPushButton("❌ Отмена")
        self.cancel_btn.clicked.connect(self.reject)

        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(self.cancel_btn)
        layout.addLayout(button_layout)

    def load_task_data(self):
        if self.task_data:
            self.title_edit.setText(self.task_data.get('title', ''))
            self.description_edit.setPlainText(self.task_data.get('description', ''))

            status = self.task_data.get('status', 'К выполнению')
            index = self.status_combo.findText(status)
            if index >= 0:
                self.status_combo.setCurrentIndex(index)

            priority = self.task_data.get('priority', 'Средний')
            index = self.priority_combo.findText(priority)
            if index >= 0:
                self.priority_combo.setCurrentIndex(index)

            due_date = self.task_data.get('due_date')
            if due_date:
                self.due_date_edit.setDate(QDate.fromString(due_date, 'yyyy-MM-dd'))

            completed = self.task_data.get('completed', False)
            self.completed_check.setChecked(completed)

            self.estimated_hours_edit.setText(str(self.task_data.get('estimated_hours', 0)))
            self.actual_hours_edit.setText(str(self.task_data.get('actual_hours', 0)))

            for subtask in self.task_data.get('subtasks', []):
                item = QListWidgetItem(subtask['title'])
                item.setData(Qt.ItemDataRole.UserRole, subtask)
                if subtask.get('completed', False):
                    item.setCheckState(Qt.CheckState.Checked)
                    item.setForeground(QColor(100, 100, 100))
                else:
                    item.setCheckState(Qt.CheckState.Unchecked)
                self.subtasks_list.addItem(item)

    def add_subtask(self):
        title = self.subtask_edit.text().strip()
        if title:
            item = QListWidgetItem(title)
            item.setCheckState(Qt.CheckState.Unchecked)
            self.subtasks_list.addItem(item)
            self.subtask_edit.clear()

    def remove_subtask(self):
        current_row = self.subtasks_list.currentRow()
        if current_row >= 0:
            self.subtasks_list.takeItem(current_row)

    def toggle_subtask(self):
        current_item = self.subtasks_list.currentItem()
        if current_item:
            if current_item.checkState() == Qt.CheckState.Checked:
                current_item.setCheckState(Qt.CheckState.Unchecked)
                current_item.setForeground(QColor(0, 0, 0))
            else:
                current_item.setCheckState(Qt.CheckState.Checked)
                current_item.setForeground(QColor(100, 100, 100))

    def get_task_data(self):
        subtasks = []
        for i in range(self.subtasks_list.count()):
            item = self.subtasks_list.item(i)
            subtasks.append({
                'title': item.text(),
                'completed': item.checkState() == Qt.CheckState.Checked
            })

        return {
            'title': self.title_edit.text(),
            'description': self.description_edit.toPlainText(),
            'status': self.status_combo.currentText(),
            'priority': self.priority_combo.currentText(),
            'due_date': self.due_date_edit.date().toString('yyyy-MM-dd'),
            'completed': self.completed_check.isChecked(),
            'estimated_hours': float(self.estimated_hours_edit.text() or 0),
            'actual_hours': float(self.actual_hours_edit.text() or 0),
            'subtasks': subtasks,
            'created_at': self.task_data.get('created_at', datetime.now().isoformat()),
            'updated_at': datetime.now().isoformat()
        }


class TaskTab(QWidget):
    """Вкладка для управления задачами"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.tasks = []
        self.setup_ui()
        self.load_sample_tasks()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        toolbar = QHBoxLayout()
        toolbar.setSpacing(4)

        self.btn_add_task = QPushButton("➕ Задача")
        self.btn_edit_task = QPushButton("✏️ Редактировать")
        self.btn_delete_task = QPushButton("🗑️ Удалить")
        self.btn_toggle_complete = QPushButton("✅ Выполнено")
        self.btn_export = QPushButton("📁 Экспорт")
        self.btn_save = QPushButton("💾 Сохранить")

        self.btn_add_task.setToolTip("Добавить новую задачу")
        self.btn_edit_task.setToolTip("Редактировать выбранную задачу")
        self.btn_delete_task.setToolTip("Удалить выбранную задачу")
        self.btn_toggle_complete.setToolTip("Переключить статус выполнения")
        self.btn_export.setToolTip("Экспортировать задачи")
        self.btn_save.setToolTip("Сохранить задачи")

        toolbar.addWidget(self.btn_add_task)
        toolbar.addWidget(self.btn_edit_task)
        toolbar.addWidget(self.btn_delete_task)
        toolbar.addWidget(self.btn_toggle_complete)
        toolbar.addStretch()
        toolbar.addWidget(self.btn_export)
        toolbar.addWidget(self.btn_save)

        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(8)

        filter_layout.addWidget(QLabel("Статус:"))
        self.status_filter = QComboBox()
        self.status_filter.addItems(["Все", "К выполнению", "В процессе", "На проверке", "Выполнено"])
        filter_layout.addWidget(self.status_filter)

        filter_layout.addWidget(QLabel("Приоритет:"))
        self.priority_filter = QComboBox()
        self.priority_filter.addItems(["Все", "Низкий", "Средний", "Высокий", "Критический"])
        filter_layout.addWidget(self.priority_filter)

        filter_layout.addWidget(QLabel("Поиск:"))
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Поиск по задачам...")
        filter_layout.addWidget(self.search_edit)

        self.btn_apply_filters = QPushButton("Применить")
        filter_layout.addWidget(self.btn_apply_filters)

        self.tasks_table = QTableWidget()
        self.setup_table()

        layout.addLayout(toolbar)
        layout.addLayout(filter_layout)
        layout.addWidget(self.tasks_table)

        self.setup_connections()

    def setup_table(self):
        self.tasks_table.setColumnCount(7)
        self.tasks_table.setHorizontalHeaderLabels([
            "✓", "Заголовок", "Статус", "Приоритет", "Срок", "Подзадачи", "Часы"
        ])

        header = self.tasks_table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)

        self.tasks_table.setAlternatingRowColors(True)

    def setup_connections(self):
        self.btn_add_task.clicked.connect(self.add_task)
        self.btn_edit_task.clicked.connect(self.edit_task)
        self.btn_delete_task.clicked.connect(self.delete_task)
        self.btn_toggle_complete.clicked.connect(self.toggle_task_completion)
        self.btn_export.clicked.connect(self.export_tasks)
        self.btn_save.clicked.connect(self.save_tasks)
        self.btn_apply_filters.clicked.connect(self.apply_filters)
        self.search_edit.textChanged.connect(self.apply_filters)

        self.tasks_table.cellDoubleClicked.connect(self.on_cell_double_click)

    def load_sample_tasks(self):
        sample_tasks = [
            {
                'id': 1,
                'title': 'Разработать архитектуру приложения',
                'description': 'Спроектировать основную архитектуру и модули',
                'status': 'В процессе',
                'priority': 'Высокий',
                'due_date': '2024-02-15',
                'completed': False,
                'estimated_hours': 8.0,
                'actual_hours': 6.5,
                'subtasks': [
                    {'title': 'Определить основные модули', 'completed': True},
                    {'title': 'Спроектировать базу данных', 'completed': True},
                    {'title': 'Определить API', 'completed': False}
                ],
                'created_at': '2024-01-20T10:00:00',
                'updated_at': '2024-01-25T14:30:00'
            },
            {
                'id': 2,
                'title': 'Реализовать систему аутентификации',
                'description': 'Создать модуль регистрации и входа',
                'status': 'К выполнению',
                'priority': 'Высокий',
                'due_date': '2024-02-28',
                'completed': False,
                'estimated_hours': 12.0,
                'actual_hours': 0.0,
                'subtasks': [],
                'created_at': '2024-01-22T09:15:00',
                'updated_at': '2024-01-22T09:15:00'
            }
        ]

        self.tasks = sample_tasks
        self.refresh_table()

    def refresh_table(self):
        self.tasks_table.setRowCount(0)

        for task in self.tasks:
            row = self.tasks_table.rowCount()
            self.tasks_table.insertRow(row)

            completed_item = QTableWidgetItem()
            completed_item.setCheckState(Qt.CheckState.Checked if task['completed'] else Qt.CheckState.Unchecked)
            self.tasks_table.setItem(row, 0, completed_item)

            title_item = QTableWidgetItem(task['title'])
            if task['completed']:
                title_item.setForeground(QColor(100, 100, 100))
            self.tasks_table.setItem(row, 1, title_item)

            self.tasks_table.setItem(row, 2, QTableWidgetItem(task['status']))

            priority_item = QTableWidgetItem(task['priority'])
            if task['priority'] == 'Критический':
                priority_item.setForeground(QColor(220, 50, 50))
            elif task['priority'] == 'Высокий':
                priority_item.setForeground(QColor(220, 120, 50))
            elif task['priority'] == 'Средний':
                priority_item.setForeground(QColor(50, 120, 220))
            else:
                priority_item.setForeground(QColor(100, 160, 100))
            self.tasks_table.setItem(row, 3, priority_item)

            due_date = task.get('due_date', '')
            due_item = QTableWidgetItem(due_date)

            if due_date and not task['completed']:
                due_date_obj = datetime.strptime(due_date, '%Y-%m-%d').date()
                if due_date_obj < date.today():
                    due_item.setForeground(QColor(220, 50, 50))

            self.tasks_table.setItem(row, 4, due_item)

            subtasks = task.get('subtasks', [])
            completed_subtasks = sum(1 for st in subtasks if st.get('completed', False))
            subtasks_text = f"{completed_subtasks}/{len(subtasks)}"
            self.tasks_table.setItem(row, 5, QTableWidgetItem(subtasks_text))

            hours_text = f"{task.get('actual_hours', 0)}/{task.get('estimated_hours', 0)}"
            self.tasks_table.setItem(row, 6, QTableWidgetItem(hours_text))

    def get_selected_task_id(self):
        current_row = self.tasks_table.currentRow()
        if current_row >= 0 and current_row < len(self.tasks):
            return self.tasks[current_row]['id']
        return None

    def add_task(self):
        dialog = TaskDialog(parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            task_data = dialog.get_task_data()
            task_data['id'] = max([task['id'] for task in self.tasks], default=0) + 1
            task_data['created_at'] = datetime.now().isoformat()
            self.tasks.append(task_data)
            self.refresh_table()

            if hasattr(self, "parent") and hasattr(self.parent(), "status_bar"):
                self.parent().status_bar.showMessage("Задача добавлена", 2000)

    def edit_task(self):
        task_id = self.get_selected_task_id()
        if task_id is None:
            QMessageBox.warning(self, "Предупреждение", "Выберите задачу для редактирования")
            return

        task_data = next((task for task in self.tasks if task['id'] == task_id), None)
        if task_data:
            dialog = TaskDialog(task_data, self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                updated_data = dialog.get_task_data()
                updated_data['id'] = task_data['id']
                updated_data['created_at'] = task_data['created_at']

                index = next(i for i, task in enumerate(self.tasks) if task['id'] == task_id)
                self.tasks[index] = updated_data
                self.refresh_table()

                if hasattr(self, "parent") and hasattr(self.parent(), "status_bar"):
                    self.parent().status_bar.showMessage("Задача обновлена", 2000)

    def delete_task(self):
        task_id = self.get_selected_task_id()
        if task_id is None:
            QMessageBox.warning(self, "Предупреждение", "Выберите задачу для удаления")
            return

        reply = QMessageBox.question(
            self, "Подтверждение удаления",
            "Вы уверены, что хотите удалить выбранную задачу?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.tasks = [task for task in self.tasks if task['id'] != task_id]
            self.refresh_table()

            if hasattr(self, "parent") and hasattr(self.parent(), "status_bar"):
                self.parent().status_bar.showMessage("Задача удалена", 2000)

    def toggle_task_completion(self):
        task_id = self.get_selected_task_id()
        if task_id is None:
            QMessageBox.warning(self, "Предупреждение", "Выберите задачу")
            return

        task_data = next((task for task in self.tasks if task['id'] == task_id), None)
        if task_data:
            task_data['completed'] = not task_data['completed']
            task_data['updated_at'] = datetime.now().isoformat()

            if task_data['completed']:
                task_data['status'] = 'Выполнено'
            else:
                task_data['status'] = 'К выполнению'

            self.refresh_table()

    def on_cell_double_click(self, row, column):
        if column != 0:
            self.edit_task()

    def apply_filters(self):
        self.refresh_table()

    def export_tasks(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Экспорт задач", "", "JSON Files (*.json)"
        )

        if file_path:
            if not file_path.endswith('.json'):
                file_path += '.json'

            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(self.tasks, f, ensure_ascii=False, indent=2)

                if hasattr(self, "parent") and hasattr(self.parent(), "status_bar"):
                    self.parent().status_bar.showMessage(f"Задачи экспортированы в {os.path.basename(file_path)}", 3000)
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Ошибка экспорта: {str(e)}")

    def save_tasks(self):
        print("Сохранение задач в БД...")
        if hasattr(self, "parent") and hasattr(self.parent(), "status_bar"):
            self.parent().status_bar.showMessage("Задачи сохранены", 2000)