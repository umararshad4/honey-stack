# CONTEXT.md and ADR formats

## CONTEXT.md

```md
# {Context name}

{One or two sentences: what this context is and why it exists.}

## Language

### Ordering

**Order**:
A Customer's request to purchase one or more items.
_Avoid_: Purchase, transaction

**Invoice**:
A request for payment sent to a Customer after a Shipment is dispatched.
_Avoid_: Bill, payment request

### People

**Customer**:
A person or organization that places Orders.
_Avoid_: Client, buyer, account

**User**:
An authentication identity. May or may not represent a Customer.
_Avoid_: Login, account

## Relationships

- An **Order** produces one or more **Invoices**, one per **Shipment**.
- An **Invoice** belongs to exactly one **Customer**.

## Flagged ambiguities

- "account" meant both **Customer** and **User**. They are distinct: a Customer places Orders; a User signs in.
```

Use glossary terms inside other definitions once they exist; that is how the language compounds.

## CONTEXT-MAP.md (several contexts)

```md
# Context map

## Contexts

- [Ordering](./src/ordering/CONTEXT.md): receives and tracks customer orders
- [Billing](./src/billing/CONTEXT.md): generates invoices and takes payments

## Relationships

- **Ordering → Billing**: Ordering emits `OrderPlaced`; Billing consumes it to open an invoice.
```

System-wide ADRs live in root `docs/adr/`; context-specific ones in that context's `docs/adr/`.

## ADR

Path: `docs/adr/0007-<slug>.md`, one past the highest existing number.

```md
# Ordering and Billing talk through events, not HTTP

Billing must keep working when Ordering is down for deploys, and synchronous calls coupled their release trains. We publish domain events on the existing queue and Billing consumes them. We accept eventual consistency on invoice creation (seconds) in exchange for independent deploys.
```

Optional, only when they carry information:
- `Status:` frontmatter: `proposed | accepted | deprecated | superseded by ADR-NNNN`.
- **Considered options**: when a rejected alternative will be proposed again.
- **Consequences**: when downstream effects are not obvious.
