# Contributing to AgentCraft

Thank you for your interest in contributing to AgentCraft! This guide explains how to get your changes into the repository.

## Prerequisites

- A [GitHub account](https://github.com/join)
- [Git](https://git-scm.com/downloads) installed locally
- Node.js 20+ (for website changes)

## How to Contribute

### 1. Fork the Repository

Click the **Fork** button at the top-right of the [repository page](https://github.com/CamelCod/agentcraft) to create your own copy.

### 2. Clone Your Fork

```bash
git clone https://github.com/<your-username>/agentcraft.git
cd agentcraft
```

### 3. Add the Upstream Remote

Keep your fork in sync with the original repository:

```bash
git remote add upstream https://github.com/CamelCod/agentcraft.git
```

### 4. Create a Feature Branch

Always work on a dedicated branch — never commit directly to `main`:

```bash
git checkout -b feature/your-feature-name
```

Use a descriptive branch name, for example:
- `feature/add-new-agent`
- `fix/broken-notion-sync`
- `docs/update-setup-guide`

### 5. Make Your Changes

Edit files, add new agents, update docs, etc. For website changes, follow the [website README](website/README.md) for local development instructions.

### 6. Commit Your Changes

```bash
git add .
git commit -m "feat: describe what your change does"
```

Use clear, concise commit messages. Common prefixes:
- `feat:` – new feature
- `fix:` – bug fix
- `docs:` – documentation update
- `chore:` – maintenance / tooling

### 7. Sync with Upstream (Optional but Recommended)

Before pushing, pull in any changes that landed on `main` while you were working:

```bash
git fetch upstream
git rebase upstream/main
```

### 8. Push to Your Fork

```bash
git push origin feature/your-feature-name
```

### 9. Open a Pull Request

1. Go to your fork on GitHub.
2. Click **Compare & pull request**.
3. Fill in a clear title and description explaining *what* you changed and *why*.
4. Submit the pull request against the `main` branch of `CamelCod/agentcraft`.

A maintainer will review your PR and may leave feedback. Once approved it will be merged.

## Code Style

- Follow the existing code style in the files you edit.
- For TypeScript/JavaScript, the project uses the configuration in `website/tsconfig.json` and `website/tailwind.config.mjs`.

## Reporting Bugs or Requesting Features

Open an [issue](https://github.com/CamelCod/agentcraft/issues) with a clear description of the bug or feature request.

## Questions?

Feel free to open an issue or reach out via [@CamelCod](https://github.com/CamelCod).
