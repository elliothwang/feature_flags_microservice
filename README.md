# Feature Flag Microservice

A lightweight Flask-based microservice that manages feature flags for your application.

The primary flag used by the main program is:

- `environment_mode` – controls whether the system runs in **Test Mode** or **Production Mode**.

In **Test Mode**, the main program will *not* trigger expensive operations such as report compilation or plot generation.  
In **Production Mode**, the main program will call the Report Compiler and Data Plot Visualizer microservices normally.

This service is designed to be called **programmatically** over HTTP, not imported as a library.

---

## Table of Contents

1. [Overview](#overview)
2. [Endpoints](#endpoints)
3. [Data Model](#data-model)
4. [Running the Service](#running-the-service)
5. [Environment Variables](#environment-variables)
6. [Testing](#testing)
7. [Example Usage](#example-usage)
8. [Integration with the Main Program](#integration-with-the-main-program)
9. [Relation to User Stories](#relation-to-user-stories)

---

## Overview

The Feature Flag Microservice exposes a simple HTTP API that lets other programs:

- Retrieve the current set of feature flags.
- Create or update feature flags.
- Read or modify the current `environment_mode` (`test` or `production`).

The main program uses this microservice to decide whether it should generate plots and reports or skip them (for test/demo runs).

- In **Test Mode**, report and plot generation are skipped.
- In **Production Mode**, the main program calls the Report Compiler and Data Plot Visualizer microservices.

---

## Endpoints

All endpoints return JSON.

### `GET /health`

Health check for the service.

**Response (200)**

```json
{
  "status": "ok",
  "service": "feature-flag",
  "mode": "test"
}
