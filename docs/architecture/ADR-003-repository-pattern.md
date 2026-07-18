# ADR-003: Repository pattern with Unit of Work

- Status: Accepted
- Date: 2026-07-18

## Context

Authentication operations span users and refresh sessions. Letting services create SQLAlchemy queries would couple business rules to persistence and make transaction boundaries inconsistent.

## Decision

Routers call services. Services call repository protocols through a Unit of Work. SQLAlchemy queries live only in concrete repositories. The Unit of Work owns the `AsyncSession`, commits atomically, rolls back on failures, and translates database integrity conflicts into application exceptions.

## Alternatives

1. Commit inside each repository method: simple, but register and token rotation cannot be atomic across repositories.
2. Inject `AsyncSession` into services: fewer classes, but leaks persistence mechanics into application logic.
3. Generic repository for every entity: reduces repetition but hides domain-specific query intent and often becomes an untyped abstraction.

## Consequences

There is additional interface code and fake repositories for tests. Transaction ownership is explicit, multi-repository workflows are safe, and services remain independent of SQLAlchemy query construction.
