DO $$
DECLARE
    -- ID переменных для связей
    v_user_id UUID;
    v_ws_id UUID;
    v_root_folder_id UUID;
    v_folder_data_id UUID;
    v_folder_ai_id UUID;
    v_folder_docs_id UUID;
    v_status_new_id UUID;
    v_status_progress_id UUID;
    v_status_done_id UUID;
    v_table_id UUID;
    v_task_id UUID;
    v_workflow_id UUID;
    v_node_summarizer_id UUID;
    v_node_chat_id UUID;
    
BEGIN

    -- =============================================
    -- 1. ПОЛЬЗОВАТЕЛЬ (ADMIN)
    -- =============================================
    INSERT INTO app_user (
        username, 
        email, 
        password_hash, -- Оставляем для гибридного входа
        public_key,    -- Новое поле для P2P
        full_name, 
        is_active, 
        is_superuser, 
        can_delete_workspaces,
        user_data
    ) VALUES (
        'admin', 
        'admin@worrrkspace.local', 
        '$2a$12$VcCDp2dFpz8C1kMD5q1zB.fKdkS3DxYI9Q2tUYVl7HpL9bQY1cGvO', -- "admin123"
        'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQC...', -- Fake public key
        'Администратор системы', 
        TRUE, 
        TRUE, 
        TRUE,
        '{"theme": "dark", "language": "ru"}'
    ) RETURNING id INTO v_user_id;

    -- =============================================
    -- 2. РАБОЧЕЕ ПРОСТРАНСТВО
    -- =============================================
    INSERT INTO workspace (
        name, 
        slug, 
        description, 
        owner_id, 
        sync_key, -- Новое поле для DHT
        is_encrypted,
        is_template, 
        settings
    ) VALUES (
        'Моё рабочее пространство', 
        'my-workspace', 
        'Основное пространство для аналитики и ML', 
        v_user_id, 
        'dht_key_example_12345',
        TRUE,
        FALSE, 
        '{"autoSave": true, "defaultLanguage": "ru"}'
    ) RETURNING id INTO v_ws_id;

    -- Права доступа
    INSERT INTO workspace_permission (
        user_id, workspace_id, 
        can_read, can_edit, can_create, can_delete, 
        can_comment, can_invite, can_execute_workflows, can_manage_ai_models
    ) VALUES (
        v_user_id, v_ws_id, 
        TRUE, TRUE, TRUE, TRUE, 
        TRUE, TRUE, TRUE, TRUE
    );

    -- =============================================
    -- 3. ФАЙЛОВАЯ СИСТЕМА (FOLDERS & LTREE)
    -- =============================================
    -- Корневая папка (виртуальная или реальная)
    INSERT INTO project_folder (workspace_id, parent_id, name, path, is_system)
    VALUES (v_ws_id, NULL, 'Root', 'root', TRUE)
    RETURNING id INTO v_root_folder_id;

    -- Папка "Данные"
    INSERT INTO project_folder (workspace_id, parent_id, name, path, icon, color)
    VALUES (v_ws_id, v_root_folder_id, 'Data', 'root.data', 'database', '#4CAF50')
    RETURNING id INTO v_folder_data_id;

    -- Папка "AI Пайплайны"
    INSERT INTO project_folder (workspace_id, parent_id, name, path, icon, color)
    VALUES (v_ws_id, v_root_folder_id, 'Workflows', 'root.workflows', 'brain', '#9C27B0')
    RETURNING id INTO v_folder_ai_id;
    
    -- Папка "Документы"
    INSERT INTO project_folder (workspace_id, parent_id, name, path, icon, color)
    VALUES (v_ws_id, v_root_folder_id, 'Docs', 'root.docs', 'file-text', '#2196F3')
    RETURNING id INTO v_folder_docs_id;

    -- =============================================
    -- 4. СТАТУСЫ ЗАДАЧ (KANBAN)
    -- =============================================
    INSERT INTO task_status (workspace_id, name, color, is_completed_state, sort_order) VALUES 
    (v_ws_id, 'Новая', '#FF6B6B', FALSE, 1) RETURNING id INTO v_status_new_id;
    
    INSERT INTO task_status (workspace_id, name, color, is_completed_state, sort_order) VALUES 
    (v_ws_id, 'В работе', '#4ECDC4', FALSE, 2) RETURNING id INTO v_status_progress_id;
    
    INSERT INTO task_status (workspace_id, name, color, is_completed_state, sort_order) VALUES 
    (v_ws_id, 'Завершена', '#06D6A0', TRUE, 3) RETURNING id INTO v_status_done_id;

    -- =============================================
    -- 5. ТИПЫ НОД (NODE TYPES)
    -- =============================================
    -- AI Чат
    INSERT INTO node_type (name, version, code_snippet, python_module, execution_env, input_schema, output_schema, is_system_node)
    VALUES (
        'ai_chat', '1.0.0', 
        NULL, 'worrrkspace.nodes.ai_processing.AIChatNode', 'python',
        '{"type": "object", "required": ["message"], "properties": {"message": {"type": "string"}, "history": {"type": "array"}}}',
        '{"type": "object", "properties": {"response": {"type": "string"}}}',
        TRUE
    ) RETURNING id INTO v_node_chat_id;

    -- Суммаризатор
    INSERT INTO node_type (name, version, python_module, execution_env, input_schema, output_schema, is_system_node)
    VALUES (
        'text_summarizer', '1.0.0', 
        'worrrkspace.nodes.ai_processing.TextSummarizerNode', 'python',
        '{"type": "object", "required": ["text"], "properties": {"text": {"type": "string"}}}',
        '{"type": "object", "properties": {"summary": {"type": "string"}}}',
        TRUE
    ) RETURNING id INTO v_node_summarizer_id;

    -- Magic Node
    INSERT INTO node_type (name, version, python_module, execution_env, input_schema, output_schema, is_system_node)
    VALUES (
        'magic_node', '1.0.0', 
        'worrrkspace.nodes.ai_processing.MagicNode', 'python',
        '{"type": "object", "required": ["prompt", "input"], "properties": {"prompt": {"type": "string"}, "input": {"type": "any"}}}',
        '{"type": "object", "properties": {"output": {"type": "any"}}}',
        TRUE
    );

    -- =============================================
    -- 6. AI КОНФИГУРАЦИЯ
    -- =============================================
    INSERT INTO ai_model_config (
        workspace_id, name, provider, model_name,
        inference_config, context_window
    ) VALUES (
        v_ws_id, 'GPT-3.5 Turbo', 'openai', 'gpt-3.5-turbo',
        '{"temperature": 0.7, "max_tokens": 2000}', 4096
    );

    INSERT INTO ai_model_config (
        workspace_id, name, provider, model_name,
        inference_config, context_window
    ) VALUES (
        v_ws_id, 'Llama-3-8B-Local', 'local', 'llama-3-8b-instruct.gguf',
        '{"gpu_layers": 32, "context": 8192}', 8192
    );

    -- =============================================
    -- 7. ДАННЫЕ (ТАБЛИЦА)
    -- =============================================
    INSERT INTO data_table (
        workspace_id, folder_id, path, -- Привязка к файловой системе
        name, description, columns_schema, created_by
    ) VALUES (
        v_ws_id, v_folder_data_id, 'root.data.projects', 
        'Пример данных проектов', 'Демонстрационная таблица',
        '[
            {"name": "id", "type": "integer", "primary_key": true},
            {"name": "project_name", "type": "utf8"},
            {"name": "budget", "type": "float64"},
            {"name": "status", "type": "utf8"}
        ]', 
        v_user_id
    ) RETURNING id INTO v_table_id;

    -- Чанк данных (Hybrid Storage)
    INSERT INTO table_chunk (
        table_id, chunk_index, chunk_x, chunk_y,
        data_hash, -- P2P CAS hash
        cells_data, -- Fallback storage
        row_count
    ) VALUES (
        v_table_id, 0, 0, 0,
        'sha256_hash_of_chunk_content_12345',
        '{
            "0": {"id": 1, "project_name": "WoRRRkspace Dev", "budget": 500000.0, "status": "active"},
            "1": {"id": 2, "project_name": "Marketing Q1", "budget": 150000.0, "status": "planning"}
        }',
        2
    );

    -- =============================================
    -- 8. КОНТЕНТ (ЗАМЕТКА)
    -- =============================================
    INSERT INTO note (
        workspace_id, folder_id, path,
        title, content_markdown, author_id, tags
    ) VALUES (
        v_ws_id, v_folder_docs_id, 'root.docs.welcome',
        '🎯 Добро пожаловать в WoRRRkspace!',
        '# Привет! Это ваш новый P2P офис.\n\nЗдесь данные принадлежат только вам.',
        v_user_id, '["welcome", "guide"]'
    );

    -- =============================================
    -- 9. ПАЙПЛАЙН (WORKFLOW)
    -- =============================================
    INSERT INTO workflow (
        workspace_id, folder_id, path,
        name, graph_json, is_active, created_by
    ) VALUES (
        v_ws_id, v_folder_ai_id, 'root.workflows.summarizer',
        'Суммаризатор текста',
        '{
            "nodes": [
                {"id": "1", "type": "text_input", "position": {"x": 100, "y": 100}},
                {"id": "2", "type": "text_summarizer", "position": {"x": 300, "y": 100}}
            ],
            "edges": [
                {"id": "e1", "source": "1", "target": "2"}
            ]
        }',
        TRUE, v_user_id
    ) RETURNING id INTO v_workflow_id;

    -- =============================================
    -- 10. ЗАДАЧИ
    -- =============================================
    INSERT INTO task (
        workspace_id, title, description, 
        status_id, assignee_id, priority, due_date
    ) VALUES (
        v_ws_id, 'Изучить AI-ноды', 'Попробовать запустить Llama локально',
        v_status_new_id, v_user_id, 2, NOW() + INTERVAL '7 days'
    ) RETURNING id INTO v_task_id;

    INSERT INTO subtask (task_id, title, is_completed)
    VALUES (v_task_id, 'Скачать веса модели', FALSE);

    -- =============================================
    -- 11. ГРАФИК (CHART)
    -- =============================================
    INSERT INTO data_chart (
        workspace_id, folder_id, path,
        name, chart_type, render_engine,
        data_source_type, data_source_id,
        chart_config, plotly_config
    ) VALUES (
        v_ws_id, v_folder_data_id, 'root.data.budget_chart',
        'Бюджет проектов', 'bar', 'plotly',
        'table', v_table_id,
        '{"x": "project_name", "y": "budget"}',
        '{"title": "Распределение бюджета"}'
    );

END $$;