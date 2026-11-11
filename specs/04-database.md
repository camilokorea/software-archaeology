---
id: database
version: 1.0.0
title: Data, schema and business rules in the database
order: 40
areas: [database]
inputs: [database, inventory]
files:
  globs: ["**/*.sql", "**/*Context.cs", "**/*Repository*", "**/*Mapper.xml", "**/*.hbm.xml", "**/migrations/**", "**/models.py"]
  keywords: [repository, dao, context, mapper, entity, model, schema, migration]
  content: "SELECT\\s|INSERT\\s+INTO|UPDATE\\s+\\w+\\s+SET|ExecuteReader|ExecuteNonQuery|createQuery|jdbcTemplate"
---
## Purpose
Understand where data lives, how the code reaches it, and which business rules are hidden in the database.

## Look for
- Stored procedures, triggers and functions that decide business outcomes (prices, approvals, statuses). Name the
  rule each one implements.
- SQL built by string concatenation (also a security issue: report it here with the rule, and it will be linked).
- N+1 query patterns, queries inside loops, missing transactions around multi-step writes.
- More than one way of accessing the same data (raw SQL in some places, ORM in others).
- Schema smells visible in scripts: no primary or foreign keys, wide tables, columns reused for several meanings.
- Data that other systems read directly (shared database integration).

## Evidence rules
Cite the routine or query line. For a business rule, quote the condition that implements it.

## Business translation
Say which business rules live in the database and what it means to move or change them.

## Out of scope
Performance tuning without evidence of a problem.
