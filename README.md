# Homebrew tap for AnyMessage

Install [AnyMessage](https://github.com/knchst/AnyMessage) on Apple Silicon with macOS 14 or later and Homebrew. Intel Macs are not supported by this formula.

```sh
brew install knchst/tap/anymessage
anymessage demo
anymessage setup
anymessage doctor
```

The demo calls MCP tools against temporary fictional data without WeChat, account keys, or saved account configuration. It does not call an AI model. Use `anymessage demo --mcp` to connect an AI client to that dataset.

The MCP server exposes read-only message search and attachment access through six tools: `status`, `list_conversations`, `get_messages`, `search_messages`, `list_attachments`, and `read_attachment`.

Attachment reads use locally cached files only. They extract text from PDF, DOCX, XLSX, PPTX, and Unicode text files and return supported JPEG, PNG, GIF, and WebP images. They do not run OCR or download attachments from the network.

To print an MCP client configuration without changing a client file, run `anymessage mcp config --format json`. For client setup and privacy details, see the [AnyMessage documentation](https://github.com/knchst/AnyMessage).

## Maintain the formula

Generate the formula from the release wheel and the matching `uv.lock` using Python 3.11 or later.

```sh
python3 scripts/generate_formula.py --lock /path/to/uv.lock --wheel /path/to/anymessage-0.4.0-py3-none-any.whl
```

The generator checks each wheel URL and checksum against PyPI and the lock. Publish the release wheel at the URL in the formula before installing it. The GitHub Actions workflow uses a macOS 26 runner to link the checkout as a tap, install the formula, and run `brew test`.
