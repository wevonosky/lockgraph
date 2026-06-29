# lockgraph

> ⚠️ Early development. The interface described below is the design target, not yet fully implemented.

**lockgraph** reads a [uv](https://docs.astral.sh/uv/) workspace's `uv.lock` and exposes the *internal* dependency graph — the member→member edges, with third-party packages filtered out. It turns that graph into things you actually want:

- **Inspect** the workspace architecture as a tree, instead of digging it out of `uv tree`'s hundreds of third-party nodes.
- **Generate and verify** the Docker `COPY` lines needed to build a single workspace member — the hand-maintained "COPY dance" that silently rots when a member's dependencies change.

## Why

In a uv workspace monorepo, a member's Dockerfile must `COPY` exactly the directories in that member's transitive workspace closure — no more (wasted cache invalidation), no less (broken build). Today that list is maintained by hand and drifts. lockgraph derives it from the lock and can fail CI when the Dockerfile no longer matches.

## Install

```sh
uvx lockgraph --help        # run without installing
uv tool install lockgraph   # or install it
```

## Usage (design target)

```sh
# Inspect the internal graph
lockgraph tree                      # forest of member→member edges
lockgraph tree --invert             # who depends on what (impact analysis)
lockgraph tree apps/api             # subtree rooted at one member

# Flatten a member's workspace closure
lockgraph closure apps/api

# Docker COPY lines for one member, into marker-delimited managed blocks
lockgraph copy gen apps/api/Dockerfile     # write/refresh the managed blocks
lockgraph copy check apps/api/Dockerfile   # CI: exit 1 if the blocks are stale
```

## Important: lockgraph reflects the lock

Every projection is computed from `uv.lock`. If the lock is stale relative to the `pyproject.toml` files, lockgraph's output is stale too. In CI, pair `lockgraph copy check` with `uv lock --check` so both hops of `pyproject → lock → Dockerfile` are guarded.

## License

MIT
