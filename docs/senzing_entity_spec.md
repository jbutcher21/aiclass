---

## title: "Senzing Entity Specification" linkTitle: "Entity Specification" weight: 15 no\_list: true

This document describes how to map your entity records to Senzing for the purpose of Entity Resolution. Senzing comes pre-configured with a set of attributes you can map to to resolve persons and organizations.

## Key terms



*Diagram: How Senzing uses labels (e.g., PRIMARY, SECONDARY) to group related attributes like multiple addresses or names.*

- **Entity** — Records of real-life persons, organizations, or things in your data sources.
- **Features** — Details that describe an entity, such as a name, phone number, or address.
- **Attributes** — Specific components of features. For instance, a name feature might include first and last name. Addresses can have multiple lines, a city, and a state. Even driver’s licenses and passports include a number and an issuing authority.
- **Labels** — User-friendly names that make features easier to understand, especially when there are multiple. For instance, a person may have both a home address and a mailing address.  

