# GitHub hosts the Vault

Git is the system of record (ADR-0001) and the deployment target is Google Cloud, but Google
no longer offers a general-purpose Git host: Cloud Source Repositories is closed to new
customers and Secure Source Manager is priced for enterprises. The Vault is therefore hosted
on GitHub — the one deliberate non-Google dependency in the stack.

It also provides a free fallback runner for the pipeline via GitHub Actions, should Cloud Run
Jobs prove awkward, and a well-supported API for the mobile capture write path.
