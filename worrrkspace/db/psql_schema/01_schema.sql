-- =============================================
-- WORRRKSPACE ULTIMATE SCHEMA (Merged & Synchronized)
-- =============================================

-- 1. EXTENSIONS
CREATE EXTENSION IF NOT EXISTS "uuid-ossp"; -- Для ID
CREATE EXTENSION IF NOT EXISTS "pgcrypto";  -- Для криптографии
CREATE EXTENSION IF NOT EXISTS "ltree";     -- Для путей (Файловая система)

-- 2. ENUM TYPES
CREATE TYPE node_status AS ENUM ('pending', 'running', 'completed', 'failed', 'cancelled');
CREATE TYPE execution_environment AS ENUM ('python', 'javascript', 'docker', 'api', 'cpp', 'rust');
CREATE TYPE data_serialization AS ENUM ('json', 'pickle', 'parquet', 'csv', 'arrow', 'binary');
CREATE TYPE storage_strategy AS ENUM ('database', 'filesystem', 'p2p_network');
-- Полный список сущностей для полиморфных связей
CREATE TYPE entity_type AS ENUM ('workspace', 'user', 'folder', 'table', 'note', 'media', 'workflow', 'task', 'graph', 'comment', 'node', 'chart', 'notebook', 'presentation');

-- =============================================
-- CORE & IDENTITY (UUID + Rich Profile)
-- =============================================

CREATE TABLE app_user (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    
    -- Auth (Hybrid: Password + Crypto Key)
    password_hash VARCHAR(255),
    public_key TEXT, -- Для P2P подписей
    
    -- Profile
    full_name VARCHAR(255),
    user_data JSONB DEFAULT '{}', -- Настройки UI
    avatar_url VARCHAR(500),
    
    -- Permissions & State
    is_active BOOLEAN DEFAULT TRUE,
    is_superuser BOOLEAN DEFAULT FALSE,
    can_delete_workspaces BOOLEAN DEFAULT FALSE,
    last_login TIMESTAMP,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_app_user_pubkey ON app_user(public_key);

CREATE TABLE workspace (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL, -- Красивые URL
    description TEXT,
    owner_id UUID REFERENCES app_user(id) ON DELETE CASCADE,
    
    -- P2P & Sync
    sync_key VARCHAR(255), 
    is_encrypted BOOLEAN DEFAULT TRUE,
    
    -- Configs
    is_public BOOLEAN DEFAULT FALSE,
    is_template BOOLEAN DEFAULT FALSE,
    tags JSONB DEFAULT '[]',
    settings JSONB DEFAULT '{}',
    
    -- Quotas
    storage_quota_mb INTEGER DEFAULT 10240,
    used_storage_mb INTEGER DEFAULT 0,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE workspace_permission (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES app_user(id) ON DELETE CASCADE,
    workspace_id UUID NOT NULL REFERENCES workspace(id) ON DELETE CASCADE,
    
    -- Granular Permissions (Сохраняем детализацию)
    can_read BOOLEAN DEFAULT FALSE,
    can_edit BOOLEAN DEFAULT FALSE,
    can_create BOOLEAN DEFAULT FALSE,
    can_delete BOOLEAN DEFAULT FALSE,
    can_comment BOOLEAN DEFAULT FALSE,
    can_invite BOOLEAN DEFAULT FALSE,
    can_execute_workflows BOOLEAN DEFAULT FALSE,
    can_manage_ai_models BOOLEAN DEFAULT FALSE,
    
    invited_by UUID REFERENCES app_user(id),
    expires_at TIMESTAMP,
    UNIQUE(user_id, workspace_id)
);

-- =============================================
-- FILE SYSTEM STRUCTURE (FOLDERS)
-- =============================================

-- Эта таблица нужна для хранения структуры папок. 
-- Сами файлы (Note, Table) будут ссылаться сюда или иметь свой path.
CREATE TABLE project_folder (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES workspace(id) ON DELETE CASCADE,
    parent_id UUID REFERENCES project_folder(id) ON DELETE CASCADE,
    
    name VARCHAR(255) NOT NULL,
    
    -- LTREE PATH: Прямая навигация по папкам
    path ltree NOT NULL, 
    depth INTEGER DEFAULT 0,
    
    is_system BOOLEAN DEFAULT FALSE,
    icon VARCHAR(50),
    color VARCHAR(7),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_folder_path ON project_folder USING GIST(path);

-- =============================================
-- DATA ASSETS (Tables & Hybrid Storage)
-- =============================================

CREATE TABLE data_table (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES workspace(id) ON DELETE CASCADE,
    
    -- FILE SYSTEM SIMULATION
    folder_id UUID REFERENCES project_folder(id) ON DELETE SET NULL,
    path ltree, -- Прямой путь к таблице как к файлу (напр. "root.data.finance.Q1")
    
    name VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- Schemas
    columns_schema JSONB DEFAULT '[]', -- New Arrow schema
    table_schema JSONB DEFAULT '{}',   -- Old format fallback
    
    -- Stats
    row_count BIGINT DEFAULT 0,
    chunk_size INTEGER DEFAULT 1000,
    file_size_bytes BIGINT DEFAULT 0,
    
    -- Versioning Link
    current_head_hash VARCHAR(64),
    
    -- Search
    is_indexed BOOLEAN DEFAULT FALSE,
    search_vector tsvector GENERATED ALWAYS AS (
        to_tsvector('english', COALESCE(name, '') || ' ' || COALESCE(description, ''))
    ) STORED,
    
    created_by UUID REFERENCES app_user(id),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_accessed TIMESTAMP
);

CREATE INDEX idx_table_path ON data_table USING GIST(path);

CREATE TABLE table_chunk (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    table_id UUID NOT NULL REFERENCES data_table(id) ON DELETE CASCADE,
    
    -- Coordinates (Merging Grid & Linear)
    chunk_index INTEGER, 
    chunk_x INTEGER,
    chunk_y INTEGER,
    
    -- Data Content (Hybrid)
    data_hash VARCHAR(64) NOT NULL, -- P2P CAS Hash
    binary_data BYTEA, -- Small data
    external_path VARCHAR(500), -- Large data (FS/IPFS)
    
    -- Format info
    cells_data JSONB, -- Fallback for JSON storage
    is_compressed BOOLEAN DEFAULT TRUE,
    compression_ratio DECIMAL(5,2),
    
    row_count INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(table_id, chunk_x, chunk_y)
);

-- =============================================
-- CONTENT (Notes & Media)
-- =============================================

CREATE TABLE note (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES workspace(id) ON DELETE CASCADE,
    
    -- FILE SYSTEM SIMULATION
    folder_id UUID REFERENCES project_folder(id) ON DELETE SET NULL,
    path ltree, -- "root.docs.meeting_notes.monday"
    
    title VARCHAR(500) NOT NULL,
    
    -- Content
    content_json JSONB, -- Block editor
    content_html TEXT,
    content_markdown TEXT,
    
    -- Meta
    tags JSONB DEFAULT '[]',
    is_favorite BOOLEAN DEFAULT FALSE,
    is_archived BOOLEAN DEFAULT FALSE,
    version INTEGER DEFAULT 1,
    
    author_id UUID REFERENCES app_user(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_note_path ON note USING GIST(path);
CREATE INDEX idx_note_search ON note USING GIN(to_tsvector('english', title));

CREATE TABLE media_file (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES workspace(id) ON DELETE CASCADE,
    
    -- FILE SYSTEM SIMULATION
    folder_id UUID REFERENCES project_folder(id) ON DELETE SET NULL,
    path ltree,
    
    filename VARCHAR(255) NOT NULL,
    mime_type VARCHAR(100) NOT NULL,
    size_bytes BIGINT NOT NULL,
    
    -- Storage
    file_checksum VARCHAR(64) NOT NULL,
    storage_strategy storage_strategy DEFAULT 'database',
    storage_path VARCHAR(1000),
    binary_data BYTEA,
    
    metadata JSONB DEFAULT '{}', -- dimensions, duration
    uploaded_by UUID REFERENCES app_user(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_media_path ON media_file USING GIST(path);

-- =============================================
-- AI & COMPUTE (Merged)
-- =============================================

CREATE TABLE ai_model_config (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID REFERENCES workspace(id) ON DELETE CASCADE,
    
    name VARCHAR(255) NOT NULL,
    provider VARCHAR(100) NOT NULL, -- local, openai, huggingface
    source_path VARCHAR(500), -- Repo ID or Local Path
    
    -- Inference Details (From Old Script)
    inference_config JSONB DEFAULT '{"temperature": 0.7}',
    context_window INTEGER DEFAULT 4096,
    is_downloaded BOOLEAN DEFAULT FALSE,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE compute_node (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID REFERENCES workspace(id),
    owner_id UUID REFERENCES app_user(id),
    
    name VARCHAR(255) NOT NULL,
    status node_status DEFAULT 'pending',
    
    -- P2P Info
    p2p_address VARCHAR(500),
    hardware_info JSONB NOT NULL,
    
    last_heartbeat TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =============================================
-- WORKFLOWS & NODES
-- =============================================

CREATE TABLE node_type (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    version VARCHAR(50) DEFAULT '1.0.0',
    
    -- Execution Logic
    code_snippet TEXT, 
    python_module VARCHAR(500),
    execution_env execution_environment DEFAULT 'python',
    
    input_schema JSONB,
    output_schema JSONB,
    
    is_system_node BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(name, version)
);

CREATE TABLE workflow (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES workspace(id) ON DELETE CASCADE,
    
    -- FILE SYSTEM SIMULATION
    folder_id UUID REFERENCES project_folder(id) ON DELETE SET NULL,
    path ltree,
    
    name VARCHAR(255) NOT NULL,
    graph_json JSONB NOT NULL, -- Full graph structure
    
    triggers JSONB DEFAULT '[]',
    schedule_config JSONB,
    is_active BOOLEAN DEFAULT TRUE,
    
    created_by UUID REFERENCES app_user(id),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_workflow_path ON workflow USING GIST(path);

CREATE TABLE workflow_execution (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id UUID NOT NULL REFERENCES workflow(id) ON DELETE CASCADE,
    
    status node_status DEFAULT 'pending',
    triggered_by UUID REFERENCES app_user(id),
    
    input_data JSONB,
    output_data JSONB,
    
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    total_duration_ms INTEGER,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE execution_cache (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    node_type_id UUID REFERENCES node_type(id),
    input_hash VARCHAR(64) NOT NULL,
    
    output_data JSONB,
    output_blob_path VARCHAR(500),
    
    execution_time_ms INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(node_type_id, input_hash)
);

-- =============================================
-- VISUALIZATION (Charts & Notebooks)
-- =============================================

CREATE TABLE data_chart (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES workspace(id) ON DELETE CASCADE,
    
    -- FILE SYSTEM SIMULATION
    folder_id UUID REFERENCES project_folder(id) ON DELETE SET NULL,
    path ltree,
    
    name VARCHAR(255) NOT NULL,
    chart_type VARCHAR(100) NOT NULL,
    render_engine VARCHAR(50) DEFAULT 'plotly',
    
    -- Configs (Rich)
    chart_config JSONB NOT NULL,
    plotly_config JSONB DEFAULT '{}',
    
    -- Data Source Binding
    data_source_type VARCHAR(50), -- 'table', 'node', 'query'
    data_source_id UUID, 
    data_snapshot JSONB,
    
    is_public BOOLEAN DEFAULT FALSE,
    share_token VARCHAR(100),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_chart_path ON data_chart USING GIST(path);

CREATE TABLE jupyter_notebook (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES workspace(id) ON DELETE CASCADE,
    
    -- FILE SYSTEM SIMULATION
    folder_id UUID REFERENCES project_folder(id) ON DELETE SET NULL,
    path ltree,
    
    name VARCHAR(255) NOT NULL,
    content_json JSONB NOT NULL, -- .ipynb structure
    kernel_spec JSONB DEFAULT '{"name": "python3"}',
    
    last_executed TIMESTAMP,
    created_by UUID REFERENCES app_user(id),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_notebook_path ON jupyter_notebook USING GIST(path);

-- =============================================
-- VCS (Version Control System)
-- =============================================

CREATE TABLE project_commit (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES workspace(id) ON DELETE CASCADE,
    
    message TEXT NOT NULL,
    author_id UUID REFERENCES app_user(id),
    
    tree_hash VARCHAR(64) NOT NULL, -- Merkle Root Hash
    snapshot_data JSONB, -- Ссылки на версии файлов
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE branch (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES workspace(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    head_commit_id UUID REFERENCES project_commit(id),
    is_default BOOLEAN DEFAULT FALSE,
    UNIQUE(workspace_id, name)
);

-- =============================================
-- TASKS & COLLABORATION
-- =============================================

CREATE TABLE task_status (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID REFERENCES workspace(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    color VARCHAR(7),
    is_completed_state BOOLEAN DEFAULT FALSE,
    sort_order INTEGER DEFAULT 0,
    UNIQUE(name, workspace_id)
);

CREATE TABLE task (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES workspace(id) ON DELETE CASCADE,
    
    title VARCHAR(500) NOT NULL,
    description TEXT,
    
    status_id UUID NOT NULL REFERENCES task_status(id),
    assignee_id UUID REFERENCES app_user(id),
    priority INTEGER DEFAULT 3,
    
    due_date TIMESTAMP,
    start_date TIMESTAMP,
    
    -- Relations
    parent_task_id UUID REFERENCES task(id),
    related_entity_type entity_type,
    related_entity_id UUID,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE subtask (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID NOT NULL REFERENCES task(id) ON DELETE CASCADE,
    title VARCHAR(500) NOT NULL,
    is_completed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE comment_thread (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES workspace(id) ON DELETE CASCADE,
    
    entity_type entity_type NOT NULL,
    entity_id UUID NOT NULL,
    entity_specific_data JSONB, -- Например координаты на графике
    
    is_resolved BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE comment (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    thread_id UUID NOT NULL REFERENCES comment_thread(id) ON DELETE CASCADE,
    author_id UUID REFERENCES app_user(id),
    
    content TEXT NOT NULL,
    attachments JSONB DEFAULT '[]',
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =============================================
-- LOGGING & EVENTS
-- =============================================

CREATE TABLE system_event (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID REFERENCES workspace(id),
    event_type VARCHAR(100) NOT NULL,
    
    actor_id UUID REFERENCES app_user(id),
    details JSONB NOT NULL,
    
    ip_address INET,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_event_workspace ON system_event(workspace_id);
CREATE INDEX idx_event_type ON system_event(event_type);