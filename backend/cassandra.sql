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