# Homebrew tap for AnyMessage

Install [AnyMessage](https://github.com/knchst/AnyMessage) on Apple Silicon with macOS 14 or later and Homebrew. Intel Macs are not supported by this formula.

```sh
brew install knchst/tap/anymessage
anymessage demo
anymessage setup
anymessage doctor
```

The demo calls MCP tools against temporary fictional data without WeChat, account keys, or saved account configuration. It shows 3 matches in 9 scanned messages, then retrieves the proposal's surrounding approval and specification attachment. It does not call an AI model. Use `anymessage demo --mcp` to connect an AI client to that dataset.

The MCP server exposes read-only message search and attachment access through seven tools: `status`, `list_conversations`, `get_messages`, `get_message_context`, `search_messages`, `list_attachments`, and `read_attachment`.

Use `search_messages` to search 1–8 selected chats with optional UTC Unix-second date bounds. `start_time` is inclusive and `end_time` is exclusive.

Pass a search hit’s `conversation_id` and `id` to `get_message_context` as `conversation_id` and `message_id`. It returns the anchor and nearby local messages in chronological order, with `anchor_index` and flags for more messages on either side. `before` and `after` each accept 0–50 messages and default to 3. Returned attachment descriptors work with `read_attachment`. Queries are not an atomic snapshot.

Attachment reads use locally cached files only. They extract text from PDF, DOCX, XLSX, PPTX, and Unicode text files and return supported JPEG, PNG, GIF, and WebP images. They do not run OCR or download attachments from the network.

To print an MCP client configuration without changing a client file, run `anymessage mcp config --format json`. For client setup and privacy details, see the [AnyMessage documentation](https://github.com/knchst/AnyMessage).

## Maintain the formula

Generate the formula from the release wheel and the matching `uv.lock` using Python 3.11 or later.

```sh
python3 scripts/generate_formula.py --lock /path/to/uv.lock --wheel /path/to/anymessage-0.6.0-py3-none-any.whl
```

The generator checks each wheel URL and checksum against PyPI and the lock. Publish the release wheel at the URL in the formula before installing it. The GitHub Actions workflow uses a macOS 26 runner to link the checkout as a tap, install the formula, and run `brew test`.
