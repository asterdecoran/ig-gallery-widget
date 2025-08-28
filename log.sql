/*
    $ sqlite3 notion.db
    $ .schema
*/

CREATE TABLE users (
    id INTEGER,
    username TEXT NOT NULL,
    hash TEXT NOT NULL,
    PRIMARY KEY(id)
);
CREATE UNIQUE INDEX username ON users (username);

CREATE TABLE widgets (
    id INTEGER,
    widget_id TEXT NOT NULL,
    notion_token TEXT NOT NULL,
    database_url TEXT NOT NULL,
    username TEXT NOT NULL,
    PRIMARY KEY(id)
);
CREATE UNIQUE INDEX widget_id ON widgets (widget_id);
