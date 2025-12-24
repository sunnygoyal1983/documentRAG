# Database Context

This directory is used to provide the **AI Codebase Assistant** with information about your database structure.

## How it works
The assistant indexes all `.sql` files in this directory. If you want the AI to understand your tables, relationships, and data models, please:
1. Export your schema as a `.sql` file (e.g., `schema.sql`).
2. Place it in this directory.
3. The AI will automatically include this context in its code generation process.

## Supported Formats
- `.sql` (DDL/DML)
- `.prisma` (Prisma schemas)
- `.dbml` (Database Markup Language)
- `.json` / `.yaml` (If used for data modeling)
