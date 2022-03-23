# News publisher

From twitter or sqlite3 to discord and telegram.

All keys and settings provided from `config.json` (look config_samole.json for example)

## Sqlite table:
```
CREATE TABLE "nft_news" (
	"id"	INTEGER NOT NULL UNIQUE,
	"text"	TEXT,
	"publish"	INTEGER NOT NULL DEFAULT 0,
	"published_date"	TEXT,
	PRIMARY KEY("id" AUTOINCREMENT)
);
```

When `published = 1` and `published_date is NULL`, then news will be posted and `published_date` updated

Default sqlite3 pool delay 15 sec