# Homebrew tap for AnyMessage

Install [AnyMessage](https://github.com/knchst/AnyMessage) on Apple Silicon with macOS 14 or later and Homebrew. Intel Macs are not supported by this formula.

```sh
brew install knchst/tap/anymessage
anymessage setup
anymessage doctor
```

The MCP server exposes read-only message search and attachment access through six tools: `status`, `list_conversations`, `get_messages`, `search_messages`, `list_attachments`, and `read_attachment`.

To print an MCP client configuration without changing a client file, run `anymessage mcp config --format json`. For client setup and privacy details, see the [AnyMessage documentation](https://github.com/knchst/AnyMessage).

## Maintain the formula

Generate the formula from the release wheel and the matching `uv.lock` using Python 3.11 or later.

```sh
python3 scripts/generate_formula.py --lock /path/to/uv.lock --wheel /path/to/anymessage-0.3.0-py3-none-any.whl
```

The generator checks each wheel URL and checksum against PyPI and the lock. Publish the release wheel at the URL in the formula before installing it. The GitHub Actions workflow uses a macOS 26 runner to link the checkout as a tap, install the formula, and run `brew test`.
