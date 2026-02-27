# claude-remote

A tool for running Claude AI sessions remotely, enabling seamless interaction with Claude from any environment.

## Overview

`claude-remote` provides a lightweight interface for connecting to and managing Claude AI sessions from remote machines or CI/CD pipelines. It allows you to leverage Claude's capabilities without requiring a local setup beyond the client itself.

## Features

- Remote execution of Claude AI sessions
- Simple command-line interface
- Configurable connection settings
- Support for automated workflows and scripting

## Installation

```bash
# Clone the repository
git clone https://github.com/va2ai/claude-remote.git
cd claude-remote

# Install dependencies
npm install
```

## Usage

```bash
# Start a remote Claude session
claude-remote connect

# Run a one-off command
claude-remote run "Your prompt here"
```

## Configuration

Set the following environment variables before running:

| Variable | Description |
|----------|-------------|
| `ANTHROPIC_API_KEY` | Your Anthropic API key |
| `CLAUDE_REMOTE_HOST` | Remote host address (if applicable) |
| `CLAUDE_REMOTE_PORT` | Port for remote connection (default: `8080`) |

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.

## License

MIT
