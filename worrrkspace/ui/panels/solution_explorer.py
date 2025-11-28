"""Это ебанная заглушка"""



from PyQt6.QtWidgets import QTreeWidget, QTreeWidgetItem
from base_panel import DraggableDockWidget

class SolutionExplorer(DraggableDockWidget):
    def __init__(self, parent=None):
        super().__init__("Обозреватель решений", parent)
        tree = QTreeWidget()
        tree.setHeaderLabels(["Название", "Тип"])
        tree.setColumnCount(2)
        root = QTreeWidgetItem(["Workspace: Default", "Workspace"])
        child1 = QTreeWidgetItem(["Таблица товаров", "Таблица"])
        child2 = QTreeWidgetItem(["Заметка: Идеи", "Заметка"])
        child3 = QTreeWidgetItem(["Клиенты", "CRM"])
        root.addChild(child1)
        root.addChild(child2)
        root.addChild(child3)
        tree.addTopLevelItem(root)
        tree.expandAll()
        self.setWidget(tree)