"""
CodeLens AI — Backend Application Package
==========================================

Root package for the FastAPI backend. All sub-modules are organized as:

- ``core/``     — Configuration, database, security, Redis
- ``models/``   — SQLAlchemy ORM models
- ``schemas/``  — Pydantic request / response schemas
- ``services/`` — Business-logic layer
- ``workers/``  — ARQ background-job definitions
- ``api/``      — HTTP route handlers
"""
