-- =============================================
-- 1. ТРИГГЕРЫ ОБНОВЛЕНИЯ ВРЕМЕНИ (UPDATED_AT)
-- =============================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Применяем только к существующим в новой схеме таблицам
CREATE TRIGGER update_app_user_modtime BEFORE UPDATE ON app_user FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_workspace_modtime BEFORE UPDATE ON workspace FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_data_table_modtime BEFORE UPDATE ON data_table FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_note_modtime BEFORE UPDATE ON note FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_task_modtime BEFORE UPDATE ON task FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_workflow_modtime BEFORE UPDATE ON workflow FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_data_chart_modtime BEFORE UPDATE ON data_chart FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_notebook_modtime BEFORE UPDATE ON jupyter_notebook FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_folder_modtime BEFORE UPDATE ON project_folder FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =============================================
-- 2. УПРАВЛЕНИЕ КВОТАМИ ХРАНИЛИЩА (STORAGE QUOTA)
-- =============================================
CREATE OR REPLACE FUNCTION update_workspace_storage_usage()
RETURNS TRIGGER AS $$
BEGIN
    -- Логика для единой таблицы media_file (UUID)
    IF TG_OP = 'INSERT' THEN
        UPDATE workspace 
        SET used_storage_mb = used_storage_mb + (COALESCE(NEW.size_bytes, 0) / 1048576)
        WHERE id = NEW.workspace_id;
    ELSIF TG_OP = 'DELETE' THEN
        UPDATE workspace 
        SET used_storage_mb = used_storage_mb - (COALESCE(OLD.size_bytes, 0) / 1048576)
        WHERE id = OLD.workspace_id;
    ELSIF TG_OP = 'UPDATE' AND NEW.size_bytes != OLD.size_bytes THEN
        UPDATE workspace 
        SET used_storage_mb = used_storage_mb - (COALESCE(OLD.size_bytes, 0) / 1048576) + (COALESCE(NEW.size_bytes, 0) / 1048576)
        WHERE id = NEW.workspace_id;
    END IF;
    RETURN NULL;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_storage_media 
    AFTER INSERT OR UPDATE OR DELETE ON media_file
    FOR EACH ROW EXECUTE FUNCTION update_workspace_storage_usage();

-- Также учитываем размер таблиц (data_table)
CREATE TRIGGER update_storage_tables
    AFTER INSERT OR UPDATE OR DELETE ON data_table
    FOR EACH ROW EXECUTE FUNCTION update_workspace_storage_usage();

-- =============================================
-- 3. ФАЙЛОВАЯ СИСТЕМА (LTREE PATH AUTOMATION)
-- =============================================

-- А. Обновление пути для ПАПОК (project_folder)
CREATE OR REPLACE FUNCTION update_folder_path()
RETURNS TRIGGER AS $$
DECLARE
    parent_path ltree;
BEGIN
    IF NEW.parent_id IS NULL THEN
        NEW.path = text2ltree(REPLACE(NEW.id::text, '-', '_'));
        NEW.depth = 0;
    ELSE
        SELECT path INTO parent_path FROM project_folder WHERE id = NEW.parent_id;
        IF parent_path IS NULL THEN
            RAISE EXCEPTION 'Parent folder % not found', NEW.parent_id;
        END IF;
        NEW.path = parent_path || text2ltree(REPLACE(NEW.id::text, '-', '_'));
        NEW.depth = nlevel(NEW.path);
    END IF;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER trg_folder_path
    BEFORE INSERT OR UPDATE OF parent_id ON project_folder
    FOR EACH ROW EXECUTE FUNCTION update_folder_path();

-- Б. Универсальная функция для АССЕТОВ (Note, Table, Workflow, Chart)
-- Автоматически ставит путь на основе папки (folder_id)
CREATE OR REPLACE FUNCTION update_asset_path()
RETURNS TRIGGER AS $$
DECLARE
    folder_path_val ltree;
BEGIN
    IF NEW.folder_id IS NOT NULL THEN
        SELECT path INTO folder_path_val FROM project_folder WHERE id = NEW.folder_id;
        -- Путь ассета = Путь папки + ID ассета
        NEW.path = folder_path_val || text2ltree(REPLACE(NEW.id::text, '-', '_'));
    ELSE
        -- Если папки нет, кидаем в корень (или оставляем NULL, зависит от логики)
        NEW.path = text2ltree('root') || text2ltree(REPLACE(NEW.id::text, '-', '_'));
    END IF;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Применяем ко всем сущностям
CREATE TRIGGER set_note_path BEFORE INSERT OR UPDATE OF folder_id ON note FOR EACH ROW EXECUTE FUNCTION update_asset_path();
CREATE TRIGGER set_table_path BEFORE INSERT OR UPDATE OF folder_id ON data_table FOR EACH ROW EXECUTE FUNCTION update_asset_path();
CREATE TRIGGER set_workflow_path BEFORE INSERT OR UPDATE OF folder_id ON workflow FOR EACH ROW EXECUTE FUNCTION update_asset_path();
CREATE TRIGGER set_chart_path BEFORE INSERT OR UPDATE OF folder_id ON data_chart FOR EACH ROW EXECUTE FUNCTION update_asset_path();
CREATE TRIGGER set_media_path BEFORE INSERT OR UPDATE OF folder_id ON media_file FOR EACH ROW EXECUTE FUNCTION update_asset_path();

-- =============================================
-- 4. ОПЕРАЦИИ С ВОРКСПЕЙСОМ (COPY)
-- =============================================
CREATE OR REPLACE FUNCTION copy_workspace(
    source_workspace_id UUID,
    new_workspace_name VARCHAR(255),
    new_owner_id UUID
) 
RETURNS UUID AS $$
DECLARE
    new_workspace_id UUID;
BEGIN
    -- 1. Копируем сам воркспейс
    INSERT INTO workspace (
        name, slug, description, owner_id, 
        settings, storage_quota_mb
    ) 
    SELECT 
        new_workspace_name,
        LOWER(REPLACE(new_workspace_name, ' ', '-')) || '-' || EXTRACT(EPOCH FROM NOW())::INTEGER,
        description || ' (Копия)',
        new_owner_id,
        settings, storage_quota_mb
    FROM workspace WHERE id = source_workspace_id
    RETURNING id INTO new_workspace_id;
    
    -- 2. Выдаем права владельцу
    INSERT INTO workspace_permission (
        user_id, workspace_id, can_read, can_edit, can_create,
        can_delete, can_comment, can_invite, can_execute_workflows,
        invited_by
    )
    VALUES (
        new_owner_id, new_workspace_id, TRUE, TRUE, TRUE,
        TRUE, TRUE, TRUE, TRUE, new_owner_id
    );

    -- ВНИМАНИЕ: Глубокое копирование папок и файлов (recursive) здесь пропущено
    -- так как требует сложной рекурсии для восстановления иерархии folder_id.
    -- В P2P системах обычно копируется только "head" указатель.
    
    RETURN new_workspace_id;
END;
$$ language 'plpgsql';

-- =============================================
-- 5. АНАЛИТИКА И СТАТИСТИКА
-- =============================================

-- Обновление статистики пайплайнов
CREATE OR REPLACE FUNCTION update_workflow_statistics()
RETURNS TRIGGER AS $$
DECLARE
    total_executions INTEGER;
    success_count INTEGER;
BEGIN
    IF NEW.status = 'completed' OR NEW.status = 'failed' THEN
        SELECT 
            COUNT(*),
            SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END)
        INTO total_executions, success_count
        FROM workflow_execution
        WHERE workflow_id = NEW.workflow_id;
        
        -- В новой схеме нет estimated_run_time в таблице workflow (убрали лишнее),
        -- но если нужно, можно писать в JSONB metadata или вернуть поле.
        -- Здесь просто пример логики.
    END IF;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_stats_on_exec
    AFTER UPDATE ON workflow_execution
    FOR EACH ROW EXECUTE FUNCTION update_workflow_statistics();

-- Очистка кэша (UUID version)
CREATE OR REPLACE FUNCTION cleanup_old_cache(cutoff_days INTEGER DEFAULT 30)
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    -- В новой схеме нет expires_at в execution_cache (убрали),
    -- используем created_at
    DELETE FROM execution_cache 
    WHERE created_at < CURRENT_TIMESTAMP - (cutoff_days || ' days')::INTERVAL;
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    -- Очистка логов
    DELETE FROM system_event 
    WHERE created_at < CURRENT_TIMESTAMP - (cutoff_days * 2 || ' days')::INTERVAL;
    
    RETURN deleted_count;
END;
$$ language 'plpgsql';

-- =============================================
-- 6. ПОИСК (FULL TEXT SEARCH)
-- =============================================
CREATE OR REPLACE FUNCTION update_search_vector()
RETURNS TRIGGER AS $$
BEGIN
    -- Для Note
    IF TG_TABLE_NAME = 'note' THEN
        NEW.search_vector = to_tsvector('english', 
            COALESCE(NEW.title, '') || ' ' || 
            COALESCE(NEW.content_markdown, '')
        );
    -- Для Table
    ELSIF TG_TABLE_NAME = 'data_table' THEN
        NEW.search_vector = to_tsvector('english', 
            COALESCE(NEW.name, '') || ' ' || 
            COALESCE(NEW.description, '')
        );
    END IF;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_note_ts BEFORE INSERT OR UPDATE ON note FOR EACH ROW EXECUTE FUNCTION update_search_vector();
CREATE TRIGGER update_table_ts BEFORE INSERT OR UPDATE ON data_table FOR EACH ROW EXECUTE FUNCTION update_search_vector();

-- =============================================
-- 7. ГРАФИКИ И ВИЗУАЛИЗАЦИЯ (ADAPTED)
-- =============================================

-- Инвалидация кэша графика при обновлении данных
-- Теперь слушаем table_chunk
CREATE OR REPLACE FUNCTION invalidate_chart_cache_on_data_change()
RETURNS TRIGGER AS $$
BEGIN
    -- Если изменился чанк таблицы, сбрасываем хеш связанных графиков
    -- data_source_id в data_chart теперь UUID
    UPDATE data_chart
    SET data_snapshot = NULL -- Сбрасываем кэш данных
    WHERE data_source_type = 'table' 
      AND data_source_id = NEW.table_id;
    
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER trigger_invalidate_charts
    AFTER INSERT OR UPDATE OR DELETE ON table_chunk
    FOR EACH ROW EXECUTE FUNCTION invalidate_chart_cache_on_data_change();

-- Рендеринг графика в изображение (Теперь сохраняем в media_file)
CREATE OR REPLACE FUNCTION render_chart_to_image(
    p_chart_id UUID,
    p_user_id UUID,
    p_format VARCHAR(10) DEFAULT 'png'
)
RETURNS UUID AS $$
DECLARE
    v_chart_record RECORD;
    v_image_id UUID;
    v_folder_id UUID;
BEGIN
    SELECT * INTO v_chart_record FROM data_chart WHERE id = p_chart_id;
    
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Chart not found';
    END IF;
    
    -- Сохраняем результат рендера в media_file (Chart Image -> Media)
    INSERT INTO media_file (
        workspace_id, folder_id, filename, 
        mime_type, size_bytes, file_checksum,
        storage_strategy, uploaded_by, metadata
    )
    VALUES (
        v_chart_record.workspace_id, 
        v_chart_record.folder_id, -- Кладем в ту же папку
        'chart_' || v_chart_record.name || '.' || p_format,
        'image/' || p_format,
        0, -- Размер обновится после записи блоба
        'temp_hash_' || gen_random_uuid()::text,
        'database',
        p_user_id,
        jsonb_build_object('source_chart_id', p_chart_id)
    )
    RETURNING id INTO v_image_id;
    
    RETURN v_image_id;
END;
$$ language 'plpgsql';

-- =============================================
-- 8. ГИБРИДНОЕ ХРАНЕНИЕ ФАЙЛОВ (MEDIA FILE)
-- =============================================

-- Поиск дубликатов (UUID + Checksum)
CREATE OR REPLACE FUNCTION find_file_duplicates()
RETURNS TABLE(
    file_checksum VARCHAR(64),
    duplicate_count BIGINT,
    total_size_mb DECIMAL(10,2),
    file_ids UUID[]
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        m.file_checksum,
        COUNT(*) as duplicate_count,
        SUM(m.size_bytes) / 1048576.0 as total_size_mb,
        ARRAY_AGG(m.id) as file_ids
    FROM media_file m
    GROUP BY m.file_checksum
    HAVING COUNT(*) > 1
    ORDER BY duplicate_count DESC;
END;
$$ language 'plpgsql';

-- Оптимизация хранилища (Перенос Database -> Filesystem)
CREATE OR REPLACE FUNCTION optimize_file_storage(
    p_workspace_id UUID DEFAULT NULL,
    p_threshold_mb INTEGER DEFAULT 10
)
RETURNS TABLE(
    file_id UUID,
    filename VARCHAR(255),
    action_taken VARCHAR(100)
) AS $$
DECLARE
    rec RECORD;
BEGIN
    FOR rec IN 
        SELECT id, filename, storage_strategy, size_bytes
        FROM media_file
        WHERE (p_workspace_id IS NULL OR workspace_id = p_workspace_id)
          AND storage_strategy = 'database'
          AND size_bytes > (p_threshold_mb * 1048576)
    LOOP
        -- Эмуляция переноса (реальный перенос делает приложение, БД только меняет флаг)
        UPDATE media_file 
        SET 
            storage_strategy = 'filesystem',
            binary_data = NULL, -- Очищаем блоб из базы
            storage_path = '/blob_storage/' || rec.id::text
        WHERE id = rec.id;
        
        file_id := rec.id;
        filename := rec.filename;
        action_taken := 'moved_to_filesystem';
        RETURN NEXT;
    END LOOP;
END;
$$ language 'plpgsql';

-- Экспорт файла в Base64
CREATE OR REPLACE FUNCTION export_file_base64(p_file_id UUID)
RETURNS TABLE(
    filename VARCHAR(255),
    mime_type VARCHAR(100),
    data_base64 TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        m.filename,
        m.mime_type,
        CASE 
            WHEN m.storage_strategy = 'database' AND m.binary_data IS NOT NULL THEN
                encode(m.binary_data, 'base64')
            ELSE NULL -- Если файл в FS, БД не может его вернуть, это делает бэкенд
        END as data_base64
    FROM media_file m
    WHERE m.id = p_file_id;
END;
$$ language 'plpgsql';