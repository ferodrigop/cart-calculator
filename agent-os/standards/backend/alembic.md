# Alembic Standards

Conventions for database migrations.

1. **Wire `target_metadata` to SQLModel.** In `alembic/env.py`, import every model module
   (or `app.models`) so autogenerate sees all tables, then set
   `target_metadata = SQLModel.metadata`.
2. **Stable naming convention.** Set
   `SQLModel.metadata.naming_convention = {"ix": "ix_%(column_0_label)s", "uq": "uq_%(table_name)s_%(column_0_name)s", "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s", "pk": "pk_%(table_name)s"}`
   so constraint names stay stable across autogenerate runs.
3. **Autogenerate against Postgres, never SQLite.** Type and constraint differences
   between dialects produce wrong migrations. Run autogenerate against a real Postgres
   instance, even if your tests use SQLite.
4. **Timestamped, slugged filenames.** Configure
   `file_template = %%(year)d%%(month).2d%%(day).2d_%%(hour).2d%%(minute).2d_%%(slug)s`
   in `alembic.ini`. Always run `alembic revision --autogenerate -m "descriptive_slug"`
   and review the diff manually before committing.
5. **Migrate on startup, but only once.** Run `alembic upgrade head` from an entrypoint
   script or a one-shot init job, never concurrently from both FastAPI replicas. In
   `docker-compose`, prefer a dedicated `migrator` service that the API services
   `depends_on: { migrator: { condition: service_completed_successfully } }`.
