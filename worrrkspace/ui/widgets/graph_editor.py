"""Я сам переделаю"""



import math
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QMenu, QInputDialog, QMessageBox, QDialog,
                             QDialogButtonBox, QFormLayout, QDoubleSpinBox)
from PyQt6.QtCore import Qt, QTimer, QPoint, QPointF
from PyQt6.QtGui import QPainter, QPen, QBrush, QColor, QRadialGradient, QFont, QPainterPath
from PyQt6 import QtWidgets


class EdgeWeightDialog(QDialog):
    def __init__(self, parent=None, default_weight=1.0):
        super().__init__(parent)
        self.setWindowTitle("Вес связи")
        self.setModal(True)

        layout = QFormLayout(self)

        self.weight_input = QDoubleSpinBox()
        self.weight_input.setRange(0.0, 1000.0)
        self.weight_input.setSingleStep(0.1)
        self.weight_input.setValue(default_weight)
        self.weight_input.setDecimals(2)

        layout.addRow("Вес связи (0.0-1000.0):", self.weight_input)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok |
                                   QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout.addRow(buttons)

    def get_weight(self):
        return self.weight_input.value()


class GraphWidget(QWidget):
    """Виджет для отрисовки графа с физикой"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.scale = 1.0
        self.offset_x = 0
        self.offset_y = 0
        self.dragging = False
        self.dragging_node = None
        self.last_mouse_pos = None
        self.edge_creation_mode = False
        self.edge_source = None
        self.temp_edge_target = None
        self.show_weights = True
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        # Параметры физики при перетаскивании
        self.drag_stiffness = 0.7
        self.physics_drag_multiplier = 0.3

        self.physics_timer = QTimer(self)
        self.physics_timer.timeout.connect(self.update_physics)
        self.physics_enabled = True
        self.physics_timer.start(16)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        painter.translate(self.offset_x, self.offset_y)
        painter.scale(self.scale, self.scale)

        graph_tab = self.parent()

        # Рисуем связи
        for edge in graph_tab.edges:
            source_node = graph_tab.nodes.get(edge["source"])
            target_node = graph_tab.nodes.get(edge["target"])

            if source_node and target_node:
                # Цвет связи в зависимости от веса
                weight = edge.get("weight", 1.0)
                color_intensity = max(50, min(200, int(weight * 25)))

                if source_node["id"] == target_node["id"]:
                    # Петля - рисуем эллипс
                    painter.setPen(QPen(QColor(color_intensity, color_intensity, 200, 200), 2))
                    self.draw_loop(painter, source_node, edge, graph_tab.edges)
                else:
                    # Обычная связь - определяем кривизну для множественных связей
                    painter.setPen(QPen(QColor(color_intensity, color_intensity, 200, 200), 2))
                    self.draw_curved_arrow(painter, source_node, target_node, edge, graph_tab.edges)

                # Рисуем вес связи
                if self.show_weights:
                    if source_node["id"] == target_node["id"]:
                        # Для петли - текст над узлом
                        mid_x = source_node["x"]
                        mid_y = source_node["y"] - 25
                    else:
                        # Для обычной связи - по середине с учетом кривизны
                        control_point = self.get_control_point(source_node, target_node, edge, graph_tab.edges)
                        t = 0.5
                        mid_x = (1 - t) ** 2 * source_node["x"] + 2 * (1 - t) * t * control_point.x() + t ** 2 * \
                                target_node["x"]
                        mid_y = (1 - t) ** 2 * source_node["y"] + 2 * (1 - t) * t * control_point.y() + t ** 2 * \
                                target_node["y"]

                    painter.setPen(QPen(QColor(0, 0, 0)))  # Черный текст для лучшей видимости
                    font = painter.font()
                    font.setPointSize(8)
                    font.setBold(True)
                    painter.setFont(font)

                    weight_text = f"{weight:.2f}"
                    text_rect = painter.boundingRect(0, 0, 30, 16, Qt.AlignmentFlag.AlignCenter, weight_text)

                    # Рисуем текст без фона
                    painter.drawText(int(mid_x - text_rect.width() / 2),
                                     int(mid_y - text_rect.height() / 2),
                                     text_rect.width(), text_rect.height(),
                                     Qt.AlignmentFlag.AlignCenter, weight_text)

        # Временная связь в режиме создания
        if self.edge_creation_mode and self.edge_source and self.temp_edge_target:
            source_node = graph_tab.nodes.get(self.edge_source)
            if source_node:
                painter.setPen(QPen(QColor(255, 100, 100, 200), 2))

                # Обрабатываем оба случая: когда temp_edge_target - QPoint и когда это ID узла
                if isinstance(self.temp_edge_target, QPoint) or isinstance(self.temp_edge_target, QPointF):
                    # Временная связь к точке (курсору)
                    self.draw_arrow(painter,
                                    int(source_node["x"]), int(source_node["y"]),
                                    int(self.temp_edge_target.x()), int(self.temp_edge_target.y()))
                else:
                    # Временная связь к узлу
                    target_node = graph_tab.nodes.get(self.temp_edge_target)
                    if target_node:
                        if source_node["id"] == target_node["id"]:
                            # Временная петля
                            self.draw_loop(painter, source_node)
                        else:
                            # Временная обычная связь
                            self.draw_arrow(painter,
                                            int(source_node["x"]), int(source_node["y"]),
                                            int(target_node["x"]), int(target_node["y"]))

        # Рисуем узлы
        for node_id, node in graph_tab.nodes.items():
            x, y = int(node["x"]), int(node["y"])

            # Градиент для узла
            if node_id == graph_tab.selected_node:
                if self.dragging_node == node_id:
                    gradient = QRadialGradient(x, y, 15)
                    gradient.setColorAt(0, QColor(255, 200, 100))
                    gradient.setColorAt(1, QColor(255, 140, 0))
                else:
                    gradient = QRadialGradient(x, y, 15)
                    gradient.setColorAt(0, QColor(100, 150, 255))
                    gradient.setColorAt(1, QColor(65, 105, 225))
            else:
                gradient = QRadialGradient(x, y, 15)
                gradient.setColorAt(0, QColor(120, 160, 230))
                gradient.setColorAt(1, QColor(70, 130, 180))

            painter.setPen(QPen(QColor(30, 30, 30), 1.5))
            painter.setBrush(QBrush(gradient))
            painter.drawEllipse(x - 12, y - 12, 24, 24)

            # Текст узла - увеличенный шрифт
            painter.setPen(QPen(QColor(255, 255, 255)))
            font = painter.font()
            font.setPointSize(9)
            font.setBold(True)
            painter.setFont(font)

            text = node["title"]
            if len(text) > 8:
                text = text[:6] + ".."

            text_rect = painter.boundingRect(0, 0, 22, 14, Qt.AlignmentFlag.AlignCenter, text)
            painter.drawText(x - text_rect.width() // 2, y - text_rect.height() // 2,
                             text_rect.width(), text_rect.height(),
                             Qt.AlignmentFlag.AlignCenter, text)

    def get_control_point(self, source, target, current_edge, all_edges):
        """Вычисляет контрольную точку для кривой Безье с учетом множественных связей"""
        dx = target["x"] - source["x"]
        dy = target["y"] - source["y"]
        distance = max(math.sqrt(dx * dx + dy * dy), 0.1)

        if distance == 0:
            return QPointF(source["x"], source["y"])

        # Нормализованный перпендикулярный вектор
        perp_x = -dy / distance
        perp_y = dx / distance

        source_id = source["id"]
        target_id = target["id"]

        # Собираем все связи между этими узлами (включая обратные)
        edges_between = []
        for edge in all_edges:
            s = edge["source"]
            t = edge["target"]
            if (s == source_id and t == target_id) or (s == target_id and t == source_id):
                edges_between.append(edge)

        # Разделяем связи на прямые и обратные
        forward_edges = [e for e in edges_between if e["source"] == source_id and e["target"] == target_id]
        backward_edges = [e for e in edges_between if e["source"] == target_id and e["target"] == source_id]

        # Определяем тип текущей связи
        if current_edge in forward_edges:
            edge_list = forward_edges
            direction = 1  # Прямое направление
        else:
            edge_list = backward_edges
            direction = -1  # Обратное направление

        # Находим индекс текущей связи в соответствующем списке
        try:
            edge_index = edge_list.index(current_edge)
        except ValueError:
            edge_index = 0

        total_in_direction = len(edge_list)

        # Для петель используем специальную логику
        if source_id == target_id:
            # Распределяем петли по кругу вокруг узла
            angle_step = 2 * math.pi / total_in_direction
            angle = edge_index * angle_step
            radius = 25 + edge_index * 8  # Увеличиваем радиус для каждой следующей петли

            control_x = source["x"] + radius * math.cos(angle)
            control_y = source["y"] + radius * math.sin(angle)
            return QPointF(control_x, control_y)

        # Для обычных связей - распределяем равномерно по обе стороны от прямой
        max_curvature = 120

        # Если связей в одном направлении больше 1, распределяем их равномерно
        if total_in_direction == 1:
            # Если связь единственная в своем направлении, рисуем ее с небольшой кривизной
            curvature = direction * max_curvature * 0.3
        else:
            # Распределяем связи равномерно в диапазоне от 0.2 до 1.0 от max_curvature
            curvature_range = max_curvature * 0.8
            step = curvature_range / (total_in_direction - 1) if total_in_direction > 1 else 0
            curvature = direction * (max_curvature * 0.2 + edge_index * step)

        mid_x = (source["x"] + target["x"]) / 2
        mid_y = (source["y"] + target["y"]) / 2

        control_x = mid_x + perp_x * curvature
        control_y = mid_y + perp_y * curvature

        return QPointF(control_x, control_y)

    def draw_curved_arrow(self, painter, source, target, current_edge, all_edges):
        """Рисует изогнутую стрелку для связи с учетом множественных связей"""
        control_point = self.get_control_point(source, target, current_edge, all_edges)

        # Рисуем квадратичную кривую Безье
        path = QPainterPath()
        path.moveTo(source["x"], source["y"])
        path.quadTo(control_point, QPointF(target["x"], target["y"]))
        painter.drawPath(path)

        # Вычисляем точку на кривой для стрелки (ближе к концу)
        t = 0.8
        arrow_x = (1 - t) ** 2 * source["x"] + 2 * (1 - t) * t * control_point.x() + t ** 2 * target["x"]
        arrow_y = (1 - t) ** 2 * source["y"] + 2 * (1 - t) * t * control_point.y() + t ** 2 * target["y"]

        # Вычисляем направление стрелки (касательная к кривой в точке arrow_x, arrow_y)
        tangent_x = 2 * (1 - t) * (control_point.x() - source["x"]) + 2 * t * (target["x"] - control_point.x())
        tangent_y = 2 * (1 - t) * (control_point.y() - source["y"]) + 2 * t * (target["y"] - control_point.y())

        angle = math.atan2(tangent_y, tangent_x)
        self.draw_arrowhead(painter, arrow_x, arrow_y, angle)

    def draw_arrowhead(self, painter, x, y, angle):
        """Рисует стрелку в заданной точке и направлении"""
        arrow_size = 12

        # Ограничиваем координаты для предотвращения переполнения
        def clamp_coord(coord):
            return max(-2147483647, min(2147483647, int(coord)))

        arrow_x1 = x - arrow_size * math.cos(angle - math.pi / 6)
        arrow_y1 = y - arrow_size * math.sin(angle - math.pi / 6)
        arrow_x2 = x - arrow_size * math.cos(angle + math.pi / 6)
        arrow_y2 = y - arrow_size * math.sin(angle + math.pi / 6)

        painter.drawLine(clamp_coord(x), clamp_coord(y),
                         clamp_coord(arrow_x1), clamp_coord(arrow_y1))
        painter.drawLine(clamp_coord(x), clamp_coord(y),
                         clamp_coord(arrow_x2), clamp_coord(arrow_y2))

    def draw_arrow(self, painter, x1, y1, x2, y2):
        """Рисует прямую стрелку (для временных связей)"""

        # Ограничиваем координаты для предотвращения переполнения
        def clamp_coord(coord):
            return max(-2147483647, min(2147483647, int(coord)))

        # Линия связи
        painter.drawLine(clamp_coord(x1), clamp_coord(y1), clamp_coord(x2), clamp_coord(y2))

        # Стрелка
        angle = math.atan2(y2 - y1, x2 - x1)
        arrow_size = 10

        arrow_x1 = x2 - arrow_size * math.cos(angle - math.pi / 6)
        arrow_y1 = y2 - arrow_size * math.sin(angle - math.pi / 6)
        arrow_x2 = x2 - arrow_size * math.cos(angle + math.pi / 6)
        arrow_y2 = y2 - arrow_size * math.sin(angle + math.pi / 6)

        painter.drawLine(clamp_coord(x2), clamp_coord(y2),
                         clamp_coord(arrow_x1), clamp_coord(arrow_y1))
        painter.drawLine(clamp_coord(x2), clamp_coord(y2),
                         clamp_coord(arrow_x2), clamp_coord(arrow_y2))

    def draw_loop(self, painter, node, current_edge=None, all_edges=None):
        """Рисует петлю (связь узла с самим собой) с учетом множественных петель"""

        # Ограничиваем координаты для предотвращения переполнения
        def clamp_coord(coord):
            return max(-2147483647, min(2147483647, int(coord)))

        x, y = node["x"], node["y"]

        # Определяем параметры петли в зависимости от количества петель
        if current_edge and all_edges:
            # Собираем все петли для этого узла
            loops = [edge for edge in all_edges if edge["source"] == node["id"] and edge["target"] == node["id"]]

            try:
                loop_index = loops.index(current_edge)
            except ValueError:
                loop_index = 0

            total_loops = len(loops)

            # Распределяем петли по разным радиусам и углам
            base_radius = 20
            radius = base_radius + loop_index * 12  # Увеличиваем радиус для каждой следующей петли

            # Распределяем углы равномерно по кругу
            angle_step = 2 * math.pi / total_loops
            start_angle = loop_index * angle_step

            # Рисуем эллипс с смещением
            ellipse_x = x - radius
            ellipse_y = y - radius - 10
            painter.drawEllipse(clamp_coord(ellipse_x), clamp_coord(ellipse_y),
                                radius * 2, radius * 2)

            # Рисуем стрелку на петле с учетом угла
            arrow_angle = start_angle + math.pi / 4
            arrow_x = x + radius * math.cos(arrow_angle)
            arrow_y = y + radius * math.sin(arrow_angle) - 10

        else:
            # Простая петля (для временных связей)
            radius = 20
            ellipse_x = x - radius
            ellipse_y = y - radius - 10
            painter.drawEllipse(clamp_coord(ellipse_x), clamp_coord(ellipse_y),
                                radius * 2, radius * 2)

            arrow_angle = math.pi / 4
            arrow_x = x + radius * math.cos(arrow_angle)
            arrow_y = y - radius * math.sin(arrow_angle) - 10

        # Стрелка
        arrow_size = 8
        arrow_x1 = arrow_x - arrow_size * math.cos(arrow_angle - math.pi / 6)
        arrow_y1 = arrow_y - arrow_size * math.sin(arrow_angle - math.pi / 6)
        arrow_x2 = arrow_x - arrow_size * math.cos(arrow_angle + math.pi / 6)
        arrow_y2 = arrow_y - arrow_size * math.sin(arrow_angle + math.pi / 6)

        painter.drawLine(clamp_coord(arrow_x), clamp_coord(arrow_y),
                         clamp_coord(arrow_x1), clamp_coord(arrow_y1))
        painter.drawLine(clamp_coord(arrow_x), clamp_coord(arrow_y),
                         clamp_coord(arrow_x2), clamp_coord(arrow_y2))

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            pos = self.transform_coordinates(event.pos())
            node_clicked = self.get_node_at_position(pos)
            if node_clicked:
                self.dragging_node = node_clicked
                self.dragging = True
                self.last_mouse_pos = event.pos()
                self.parent().handle_node_click(node_clicked, event)
            else:
                self.dragging = True
                self.last_mouse_pos = event.pos()

        elif event.button() == Qt.MouseButton.RightButton:
            pos = self.transform_coordinates(event.pos())
            node_clicked = self.get_node_at_position(pos)
            if node_clicked:
                self.parent().handle_node_click(node_clicked, event)
                self.show_node_context_menu(event.pos(), node_clicked)
            else:
                self.show_context_menu(event.pos())

    def mouseMoveEvent(self, event):
        pos = self.transform_coordinates(event.pos())

        if self.dragging and self.last_mouse_pos:
            if self.dragging_node:
                graph_tab = self.parent()
                node = graph_tab.nodes.get(self.dragging_node)
                if node:
                    delta = (event.pos() - self.last_mouse_pos) / self.scale
                    node["x"] += delta.x() * self.drag_stiffness
                    node["y"] += delta.y() * self.drag_stiffness
                    self.last_mouse_pos = event.pos()
                    self.update()
            else:
                delta = event.pos() - self.last_mouse_pos
                self.offset_x += delta.x()
                self.offset_y += delta.y()
                self.last_mouse_pos = event.pos()
                self.update()
        elif self.edge_creation_mode:
            # Всегда обновляем temp_edge_target как QPoint (позиция курсора)
            self.temp_edge_target = pos

            # Дополнительно проверяем, находится ли курсор над узлом
            node_under_cursor = self.get_node_at_position(pos)
            if node_under_cursor:
                # Если курсор над узлом, устанавливаем temp_edge_target как ID узла
                self.temp_edge_target = node_under_cursor

            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if self.edge_creation_mode and self.edge_source:
                pos = self.transform_coordinates(event.pos())
                node_clicked = self.get_node_at_position(pos)

                if node_clicked:
                    # Создаем связь (обычную или петлю)
                    self.parent().create_edge(self.edge_source, node_clicked)
                else:
                    # Отменяем создание связи, если кликнули не на узел
                    self.edge_creation_mode = False
                    self.edge_source = None
                    self.update()

            self.dragging = False
            self.dragging_node = None
            self.last_mouse_pos = None

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            pos = self.transform_coordinates(event.pos())
            node_clicked = self.get_node_at_position(pos)
            if node_clicked:
                self.parent().edit_node_title(node_clicked)

    def wheelEvent(self, event):
        zoom_factor = 1.1
        if event.angleDelta().y() > 0:
            self.scale *= zoom_factor
        else:
            self.scale /= zoom_factor

        self.scale = max(0.1, min(5.0, self.scale))
        self.update()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Delete:
            self.parent().delete_selected()
        elif event.key() == Qt.Key.Key_Escape:
            self.edge_creation_mode = False
            self.edge_source = None
            self.update()
        elif event.key() == Qt.Key.Key_Space:
            self.physics_enabled = not self.physics_enabled
            if hasattr(self, "parent") and hasattr(self.parent(), "status_bar"):
                status = "включена" if self.physics_enabled else "выключена"
                self.parent().status_bar.showMessage(f"Физика {status}", 1000)
        elif event.key() == Qt.Key.Key_W:
            self.toggle_weights_visibility()

    def toggle_weights_visibility(self):
        self.show_weights = not self.show_weights
        self.update()
        if hasattr(self, "parent") and hasattr(self.parent(), "status_bar"):
            status = "показаны" if self.show_weights else "скрыты"
            self.parent().status_bar.showMessage(f"Веса связей {status}", 1000)

    def update_physics(self):
        if not self.physics_enabled:
            return

        graph_tab = self.parent()
        if not graph_tab.nodes:
            return

        attraction_strength = graph_tab.attraction_strength
        repulsion_strength = graph_tab.repulsion_strength
        center_gravity = graph_tab.center_gravity
        edge_length = graph_tab.edge_length
        gravity_strength = graph_tab.gravity_strength

        physics_multiplier = self.physics_drag_multiplier if self.dragging_node else 1.0
        self.apply_forces(attraction_strength * physics_multiplier,
                          repulsion_strength * physics_multiplier,
                          center_gravity * physics_multiplier,
                          edge_length,
                          gravity_strength * physics_multiplier)
        self.update()

    def apply_forces(self, attraction, repulsion, center_gravity, edge_length, gravity_strength):
        graph_tab = self.parent()
        nodes = list(graph_tab.nodes.values())

        # Отталкивание между всеми узлами с учетом коллизий
        for i, node1 in enumerate(nodes):
            for j, node2 in enumerate(nodes[i + 1:], i + 1):
                dx = node2["x"] - node1["x"]
                dy = node2["y"] - node1["y"]
                distance = max(math.sqrt(dx * dx + dy * dy), 0.1)

                # Усиленное отталкивание при близком расстоянии (коллизии)
                collision_distance = 30
                if distance < collision_distance:
                    force = repulsion * 2 / (distance * distance)
                else:
                    force = repulsion / (distance * distance)

                if distance > 0:
                    fx = force * dx / distance
                    fy = force * dy / distance

                    if node1["id"] != self.dragging_node:
                        node1["x"] -= fx * 0.5
                        node1["y"] -= fy * 0.5
                    if node2["id"] != self.dragging_node:
                        node2["x"] += fx * 0.5
                        node2["y"] += fy * 0.5

        # Притяжение по связям с учетом весов
        for edge in graph_tab.edges:
            source = graph_tab.nodes.get(edge["source"])
            target = graph_tab.nodes.get(edge["target"])

            if source and target:
                # Для петель используем меньшую силу притяжения
                if source["id"] == target["id"]:
                    continue  # Петли не влияют на физику

                dx = target["x"] - source["x"]
                dy = target["y"] - source["y"]
                distance = max(math.sqrt(dx * dx + dy * dy), 0.1)

                desired_distance = edge_length
                weight = edge.get("weight", 1.0)
                # Корректная обработка нулевого веса
                if weight <= 0:
                    weight_factor = 10.0  # Максимальное притяжение для веса 0
                else:
                    # Чем меньше вес, тем сильнее притяжение
                    weight_factor = max(0.1, 1.0 / weight)

                force = attraction * (distance - desired_distance) * 0.01 * weight_factor

                if distance > 0:
                    fx = force * dx / distance
                    fy = force * dy / distance

                    if source["id"] != self.dragging_node:
                        source["x"] += fx * 0.5
                        source["y"] += fy * 0.5
                    if target["id"] != self.dragging_node:
                        target["x"] -= fx * 0.5
                        target["y"] -= fy * 0.5

        # Гравитация к центру
        center_x = self.width() / (2 * self.scale) - self.offset_x / self.scale
        center_y = self.height() / (2 * self.scale) - self.offset_y / self.scale

        for node in nodes:
            if node["id"] == self.dragging_node:
                continue

            dx = center_x - node["x"]
            dy = center_y - node["y"]
            distance = max(math.sqrt(dx * dx + dy * dy), 0.1)

            force = (center_gravity + gravity_strength) * distance * 0.001

            if distance > 0:
                node["x"] += force * dx / distance
                node["y"] += force * dy / distance

    def transform_coordinates(self, pos):
        return QPoint(
            int((pos.x() - self.offset_x) / self.scale),
            int((pos.y() - self.offset_y) / self.scale)
        )

    def get_node_at_position(self, pos):
        graph_tab = self.parent()
        for node_id, node in graph_tab.nodes.items():
            x, y = node["x"], node["y"]
            distance = ((pos.x() - x) ** 2 + (pos.y() - y) ** 2) ** 0.5
            if distance <= 15:
                return node_id
        return None

    def center_on_nodes(self):
        graph_tab = self.parent()
        if not graph_tab.nodes:
            return

        min_x = min(node["x"] for node in graph_tab.nodes.values())
        max_x = max(node["x"] for node in graph_tab.nodes.values())
        min_y = min(node["y"] for node in graph_tab.nodes.values())
        max_y = max(node["y"] for node in graph_tab.nodes.values())

        center_x = (min_x + max_x) / 2
        center_y = (min_y + max_y) / 2

        self.offset_x = self.width() / 2 - center_x * self.scale
        self.offset_y = self.height() / 2 - center_y * self.scale
        self.update()

    def show_context_menu(self, pos):
        menu = QMenu(self)

        add_node_action = menu.addAction("Добавить узел")
        add_edge_action = menu.addAction("Создать связь")
        center_action = menu.addAction("Центрировать граф")
        physics_action = menu.addAction("Включить/выключить физику")
        weights_action = menu.addAction("Скрыть/показать веса")

        action = menu.exec(self.mapToGlobal(pos))

        if action == add_node_action:
            self.parent().add_node()
        elif action == add_edge_action:
            self.parent().start_edge_creation()
        elif action == center_action:
            self.parent().center_graph()
        elif action == physics_action:
            self.physics_enabled = not self.physics_enabled
        elif action == weights_action:
            self.toggle_weights_visibility()

    def show_node_context_menu(self, pos, node_id):
        menu = QMenu(self)

        edit_action = menu.addAction("Редактировать заголовок")
        delete_action = menu.addAction("Удалить узел")
        menu.addSeparator()
        connect_action = menu.addAction("Создать связь от узла")
        menu.addSeparator()
        physics_action = menu.addAction("Включить/выключить физику")

        action = menu.exec(self.mapToGlobal(pos))

        if action == edit_action:
            self.parent().edit_node_title(node_id)
        elif action == delete_action:
            self.parent().selected_node = node_id
            self.parent().delete_selected()
        elif action == connect_action:
            self.parent().selected_node = node_id
            self.parent().start_edge_creation()
        elif action == physics_action:
            self.physics_enabled = not self.physics_enabled


class GraphTab(QWidget):
    """Вкладка для работы с графами с поддержкой направленных связей с весом"""

    def __init__(self, parent=None):
        super().__init__(parent)
        # Структура данных совместимая с будущей БД
        self.nodes = {}  # {node_id: {id, x, y, title, content, properties}}
        self.edges = []  # [{source, target, weight, properties}]
        self.selected_node = None

        # Параметры физики
        self.attraction_strength = 1.0
        self.repulsion_strength = 100.0
        self.center_gravity = 0.1
        self.gravity_strength = 0.05
        self.edge_length = 120.0

        self.physics_panel_visible = True

        self.setup_ui()
        self.create_sample_graph()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        toolbar = QHBoxLayout()
        toolbar.setSpacing(4)

        self.btn_add_node = QPushButton("➕ Узел")
        self.btn_add_edge = QPushButton("🔗 Связь")
        self.btn_delete = QPushButton("🗑️ Удалить")
        self.btn_center = QPushButton("🎯 Центр")
        self.btn_physics = QPushButton("⚙️ Физика")
        self.btn_weights = QPushButton("👁️ Веса")
        self.btn_save = QPushButton("💾 Сохранить")

        self.btn_add_node.setToolTip("Добавить новый узел")
        self.btn_add_edge.setToolTip("Создать связь между узлами")
        self.btn_delete.setToolTip("Удалить выбранный узел или связь")
        self.btn_center.setToolTip("Центрировать граф")
        self.btn_physics.setToolTip("Показать/скрыть настройки физики")
        self.btn_weights.setToolTip("Скрыть/показать веса связей (W)")
        self.btn_save.setToolTip("Сохранить граф")

        toolbar.addWidget(self.btn_add_node)
        toolbar.addWidget(self.btn_add_edge)
        toolbar.addWidget(self.btn_delete)
        toolbar.addStretch()
        toolbar.addWidget(self.btn_center)
        toolbar.addWidget(self.btn_physics)
        toolbar.addWidget(self.btn_weights)
        toolbar.addWidget(self.btn_save)

        # Панель настройки физики
        self.physics_layout = QVBoxLayout()
        self.physics_layout.setContentsMargins(5, 5, 5, 5)

        physics_row1 = QHBoxLayout()
        physics_row1.setSpacing(8)

        physics_row1.addWidget(QLabel("Притяжение:"))
        self.attraction_slider = QtWidgets.QSlider(Qt.Orientation.Horizontal)
        self.attraction_slider.setRange(0, 500)
        self.attraction_slider.setValue(int(self.attraction_strength * 100))
        self.attraction_slider.valueChanged.connect(self.update_attraction)
        physics_row1.addWidget(self.attraction_slider)
        self.attraction_label = QLabel(f"{self.attraction_strength:.2f}")
        physics_row1.addWidget(self.attraction_label)

        physics_row1.addWidget(QLabel("Отталкивание:"))
        self.repulsion_slider = QtWidgets.QSlider(Qt.Orientation.Horizontal)
        self.repulsion_slider.setRange(0, 1000)
        self.repulsion_slider.setValue(int(self.repulsion_strength))
        self.repulsion_slider.valueChanged.connect(self.update_repulsion)
        physics_row1.addWidget(self.repulsion_slider)
        self.repulsion_label = QLabel(f"{self.repulsion_strength:.0f}")
        physics_row1.addWidget(self.repulsion_label)

        physics_row2 = QHBoxLayout()
        physics_row2.setSpacing(8)

        physics_row2.addWidget(QLabel("Гравитация к центру:"))
        self.gravity_slider = QtWidgets.QSlider(Qt.Orientation.Horizontal)
        self.gravity_slider.setRange(0, 200)
        self.gravity_slider.setValue(int(self.center_gravity * 100))
        self.gravity_slider.valueChanged.connect(self.update_gravity)
        physics_row2.addWidget(self.gravity_slider)
        self.gravity_label = QLabel(f"{self.center_gravity:.2f}")
        physics_row2.addWidget(self.gravity_label)

        physics_row2.addWidget(QLabel("Общая гравитация:"))
        self.gravity_strength_slider = QtWidgets.QSlider(Qt.Orientation.Horizontal)
        self.gravity_strength_slider.setRange(0, 200)
        self.gravity_strength_slider.setValue(int(self.gravity_strength * 100))
        self.gravity_strength_slider.valueChanged.connect(self.update_gravity_strength)
        physics_row2.addWidget(self.gravity_strength_slider)
        self.gravity_strength_label = QLabel(f"{self.gravity_strength:.2f}")
        physics_row2.addWidget(self.gravity_strength_label)

        physics_row3 = QHBoxLayout()
        physics_row3.setSpacing(8)

        physics_row3.addWidget(QLabel("Длина связи:"))
        self.edge_length_slider = QtWidgets.QSlider(Qt.Orientation.Horizontal)
        self.edge_length_slider.setRange(50, 300)
        self.edge_length_slider.setValue(int(self.edge_length))
        self.edge_length_slider.valueChanged.connect(self.update_edge_length)
        physics_row3.addWidget(self.edge_length_slider)
        self.edge_length_label = QLabel(f"{self.edge_length:.0f}")
        physics_row3.addWidget(self.edge_length_label)

        physics_row3.addStretch()

        self.physics_layout.addLayout(physics_row1)
        self.physics_layout.addLayout(physics_row2)
        self.physics_layout.addLayout(physics_row3)

        # Информационная панель
        info_layout = QHBoxLayout()
        info_layout.setSpacing(8)

        self.graph_info_label = QLabel("Граф: 0 узлов, 0 связей")
        self.selected_info_label = QLabel("Выбрано: ничего")
        self.physics_info_label = QLabel("Физика: ВКЛ | Space - физика | W - веса")

        info_layout.addWidget(self.graph_info_label)
        info_layout.addStretch()
        info_layout.addWidget(self.selected_info_label)
        info_layout.addStretch()
        info_layout.addWidget(self.physics_info_label)

        # Виджет графа
        self.graph_widget = GraphWidget()
        self.graph_widget.setMinimumSize(600, 400)

        self.physics_container = QWidget()
        self.physics_container.setLayout(self.physics_layout)

        layout.addLayout(toolbar)
        layout.addWidget(self.physics_container)
        layout.addLayout(info_layout)
        layout.addWidget(self.graph_widget)

        self.setup_connections()

    def setup_connections(self):
        self.btn_add_node.clicked.connect(self.add_node)
        self.btn_add_edge.clicked.connect(self.start_edge_creation)
        self.btn_delete.clicked.connect(self.delete_selected)
        self.btn_center.clicked.connect(self.center_graph)
        self.btn_physics.clicked.connect(self.toggle_physics_panel)
        self.btn_weights.clicked.connect(self.toggle_weights)
        self.btn_save.clicked.connect(self.save_graph)

    def toggle_physics_panel(self):
        self.physics_panel_visible = not self.physics_panel_visible
        self.physics_container.setVisible(self.physics_panel_visible)

        if self.physics_panel_visible:
            self.btn_physics.setText("⚙️ Физика")
            self.btn_physics.setToolTip("Скрыть настройки физики")
        else:
            self.btn_physics.setText("⚙️")
            self.btn_physics.setToolTip("Показать настройки физики")

    def toggle_weights(self):
        self.graph_widget.toggle_weights_visibility()
        self.btn_weights.setText("👁️ Веса" if self.graph_widget.show_weights else "🚫 Веса")

    def create_sample_graph(self):
        # Пример графа с совместимой структурой
        nodes_data = [
            {"id": "1", "x": 100, "y": 100, "title": "Идея", "content": "Основная идея",
             "properties": {"type": "concept"}},
            {"id": "2", "x": 250, "y": 50, "title": "Функция А", "content": "Первая функция",
             "properties": {"type": "function"}},
            {"id": "3", "x": 250, "y": 150, "title": "Функция Б", "content": "Вторая функция",
             "properties": {"type": "function"}},
            {"id": "4", "x": 400, "y": 50, "title": "Деталь А", "content": "Детали А",
             "properties": {"type": "detail"}},
            {"id": "5", "x": 400, "y": 150, "title": "Деталь Б", "content": "Детали Б",
             "properties": {"type": "detail"}},
        ]

        for node_data in nodes_data:
            self.add_node_at_position(node_data)

        # Связи с весами, включая петлю и множественные связи
        edges_data = [
            ("1", "2", 1.0), ("1", "3", 1.5),
            ("2", "4", 0.8), ("3", "5", 0.7),
            ("4", "5", 2.0), ("5", "4", 1.2),  # Две связи между 4 и 5
            ("4", "5", 0.5),  # Третья связь между 4 и 5
            ("1", "1", 0.5)  # Петля на узле 1
        ]

        for source, target, weight in edges_data:
            self.add_edge(source, target, weight)

        self.update_graph_info()

    def add_node(self):
        node_id = str(len(self.nodes) + 1)
        x = 200 + (len(self.nodes) % 5) * 40
        y = 150 + (len(self.nodes) % 3) * 40

        node_data = {
            "id": node_id,
            "x": x,
            "y": y,
            "title": f"Узел {node_id}",
            "content": f"Содержимое узла {node_id}",
            "properties": {"type": "generic", "created": "auto"}
        }

        self.add_node_at_position(node_data)
        self.update_graph_info()

    def add_node_at_position(self, node_data):
        node_id = node_data["id"]
        self.nodes[node_id] = node_data
        self.graph_widget.update()

    def start_edge_creation(self):
        if self.selected_node:
            self.graph_widget.edge_creation_mode = True
            self.graph_widget.edge_source = self.selected_node
            self.selected_info_label.setText("Выбрано: режим создания связи - выберите целевой узел")

    def create_edge(self, source_id, target_id):
        """Создает связь с запросом веса"""
        dialog = EdgeWeightDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            weight = dialog.get_weight()
            self.add_edge(source_id, target_id, weight)

        # Сбрасываем режим создания связи
        self.graph_widget.edge_creation_mode = False
        self.graph_widget.edge_source = None

    def add_edge(self, source_id, target_id, weight=1.0):
        if source_id in self.nodes and target_id in self.nodes:
            edge = {
                "source": source_id,
                "target": target_id,
                "weight": weight,
                "properties": {"type": "directed", "created": "manual"}
            }

            # Всегда добавляем новую связь, даже если такая уже существует
            self.edges.append(edge)

            self.graph_widget.update()
            self.update_graph_info()

    def delete_selected(self):
        if self.selected_node:
            if self.selected_node in self.nodes:
                # Удаляем узел и все связанные с ним связи
                del self.nodes[self.selected_node]
                self.edges = [edge for edge in self.edges
                              if edge["source"] != self.selected_node and edge["target"] != self.selected_node]
                self.selected_node = None
                self.graph_widget.update()
                self.update_graph_info()

    def center_graph(self):
        self.graph_widget.center_on_nodes()
        self.graph_widget.update()

    def save_graph(self):
        # Заглушка для будущей интеграции с БД
        print("Сохранение графа в БД...")
        print(f"Узлы: {len(self.nodes)}, Связи: {len(self.edges)}")

        # Здесь будет код для сохранения в БД согласно структуре:
        # graph_entity и graph_relationship

        if hasattr(self, "parent") and hasattr(self.parent(), "status_bar"):
            self.parent().status_bar.showMessage("Граф сохранен", 2000)

    def edit_node_title(self, node_id):
        node = self.nodes.get(node_id)
        if node:
            new_title, ok = QInputDialog.getText(
                self, "Редактирование узла", "Введите новый заголовок:",
                text=node["title"]
            )
            if ok and new_title.strip():
                node["title"] = new_title.strip()
                self.graph_widget.update()

    def handle_node_click(self, node_id, event):
        self.selected_node = node_id
        node = self.nodes.get(node_id)
        if node:
            self.selected_info_label.setText(f"Выбрано: {node['title']}")

        self.graph_widget.update()

    def update_attraction(self, value):
        self.attraction_strength = value / 100.0
        self.attraction_label.setText(f"{self.attraction_strength:.2f}")

    def update_repulsion(self, value):
        self.repulsion_strength = value
        self.repulsion_label.setText(f"{self.repulsion_strength:.0f}")

    def update_gravity(self, value):
        self.center_gravity = value / 100.0
        self.gravity_label.setText(f"{self.center_gravity:.2f}")

    def update_gravity_strength(self, value):
        self.gravity_strength = value / 100.0
        self.gravity_strength_label.setText(f"{self.gravity_strength:.2f}")

    def update_edge_length(self, value):
        self.edge_length = value
        self.edge_length_label.setText(f"{self.edge_length:.0f}")

    def update_graph_info(self):
        self.graph_info_label.setText(f"Граф: {len(self.nodes)} узлов, {len(self.edges)} связей")