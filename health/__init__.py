"""`Health` bounded-context package.

Provides health monitoring functionality following the Domain-Driven Design
(DDD) approach, structured into domain, application, infrastructure, and
interface layers, with a context integration layer for interactions with
other bounded contexts.

- **domain**: Core entities (``HealthRecord``) and domain services that
  encapsulate health-recording business rules.
- **application**: Orchestrates use-cases by coordinating domain services
  with infrastructure repositories.
- **infrastructure**: Peewee ORM models and repository implementations for
  persisting health records.
- **integration**: Anti-corruption layers that translate external bounded
  context concepts into Health's domain language.
- **interfaces**: Flask Blueprint exposing the REST API endpoints for this
  bounded context.
"""
