CREATE TABLE
    users (
        id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
        username TEXT NOT NULL,
        hash TEXT NOT NULL,
        cash NUMERIC NOT NULL DEFAULT 10000.00
    );

CREATE TABLE
    transactions (
        id INTEGER PRIMARY key AUTOINCREMENT,
        user_id INTEGER NOT NULL REFERENCES users (id),
        symbol CHAR(4) NOT NULL,
        shares INTEGER NOT NULL,
        price REAL NOT NULL,
        log_time TIME DEFAULT CURRENT_TIME
    );

CREATE TABLE
    shares (
        user_id INTEGER NOT NULL REFERENCES users (id),
        symbol CHAR(6) NOT NULL,
        shares INTEGER NOT NULL DEFAULT 0 CHECK (shares >= 0),
        PRIMARY key (user_id, symbol)
    );

UPDATE shares
SET
    shares = shares + ?
WHERE
    user_id = ?
    AND symbol = ?;

SELECT
    id,
    symbols,
    shares,
    price,
    logtime
FROM
    transactions
WHERE
    user_id = ?;
