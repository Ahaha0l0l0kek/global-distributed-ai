CREATE KEYSPACE agent_data
WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1};

USE agent_data;

CREATE TABLE agent_memory (
    agent_id TEXT,
    timestamp TIMESTAMP,
    observation TEXT,
    plan TEXT,
    result TEXT,
    PRIMARY KEY (agent_id, timestamp)
) WITH CLUSTERING ORDER BY (timestamp DESC);

CREATE TABLE agent_tasks (
    task_id TEXT PRIMARY KEY,
    agent_id TEXT,
    task TEXT,
    reply_host TEXT,
    reply_port INT,
    status TEXT,
    result TEXT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);