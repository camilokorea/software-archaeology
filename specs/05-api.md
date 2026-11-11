---
id: api
version: 1.0.0
title: Entry points, APIs and contracts
order: 50
areas: [api]
inputs: [api, externals]
files:
  keywords: [controller, api, service, endpoint, route, resource, servlet, actionbean, handler, .asmx, .svc]
  content: "\\[Http(Get|Post|Put|Delete)|@(Get|Post|Put|Delete|Request)Mapping|@Path\\(|app\\.(get|post)\\(|Route::|@UrlBinding"
---
## Purpose
Describe how the outside world uses the system: endpoints, pages, services, and the contracts others may depend on.

## Look for
- Public contracts that other systems may call (SOAP/WCF/ASMX, REST, file drops, queues): these constrain any rewrite.
- Inconsistent conventions (naming, error formats, status codes), and endpoints that return internal errors or stack traces.
- Missing input validation at the boundary.
- Versioning (or the lack of it) and undocumented endpoints.
- Endpoints that look unused or duplicated.

## Evidence rules
Cite the route declaration line. For "may be used by other systems", say what suggests it (a WSDL, a public route, a
config entry).

## Business translation
List what other systems or partners could break if this system changes, in plain words.

## Out of scope
Authentication details (security spec).
