New projects now require a successful version check before being added.
Projects whose backend cannot retrieve any versions are rejected with a
descriptive error message, preventing broken entries from consuming
resources in the periodic check service.
