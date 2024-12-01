-- Parent Issues Table
CREATE TABLE issues (
    id SERIAL PRIMARY KEY,
    issue_id VARCHAR(255) UNIQUE NOT NULL,
    key VARCHAR(255) NOT NULL,
    summary TEXT NOT NULL,
    owner VARCHAR(255) NOT NULL,
    issue_type VARCHAR(50) NOT NULL
);

-- Stories Table
CREATE TABLE stories (
    id SERIAL PRIMARY KEY,
    issue_id VARCHAR(255) UNIQUE NOT NULL,
    story_points INTEGER,
    status VARCHAR(255),
    assignee VARCHAR(255),
    code_reviewer VARCHAR(255),
    code_review_status VARCHAR(255),
    code_review_result VARCHAR(255)
);

-- Bugs Table
CREATE TABLE bugs (
    id SERIAL PRIMARY KEY,
    issue_id VARCHAR(255) UNIQUE NOT NULL,
    status VARCHAR(255),
    assignee VARCHAR(255),
    bug_root_cause TEXT
);

-- Status History Table
CREATE TABLE status_history (
    id SERIAL PRIMARY KEY,
    issue_id VARCHAR(255) NOT NULL,
    changed_at TIMESTAMP NOT NULL,
    from_status VARCHAR(255),
    to_status VARCHAR(255)
);

-- Assignee History Table
CREATE TABLE assignee_history (
    id SERIAL PRIMARY KEY,
    issue_id VARCHAR(255) NOT NULL,
    changed_at TIMESTAMP NOT NULL,
    from_assignee VARCHAR(255),
    to_assignee VARCHAR(255)
);

-- Code Review History Table
CREATE TABLE code_review_history (
    id SERIAL PRIMARY KEY,
    issue_id VARCHAR(255) NOT NULL,
    changed_at TIMESTAMP NOT NULL,
    code_reviewer VARCHAR(255),
    code_review_status VARCHAR(255),
    code_review_result VARCHAR(255)
);
