# Homebrew tap for AnyMessage

Install [AnyMessage](https://github.com/knchst/AnyMessage) on Apple Silicon with macOS 14 or later and Homebrew. Intel Macs are not supported by this formula.

```sh
brew install knchst/tap/anymessage
anymessage demo
```

The demo calls MCP tools against temporary fictional data without WeChat, account keys, or saved account configuration. It shows 3 matches in 9 scanned messages, then retrieves the proposal's surrounding approval and specification attachment. It does not call an AI model. Use `anymessage demo --mcp` to connect an AI client to that dataset.

For your own WeChat account, run `anymessage setup`, then `anymessage doctor`.
For a Telegram Desktop JSON export, start a separate server without WeChat setup:

```sh
anymessage mcp --telegram-export /absolute/path/to/result.json
```

Telegram export mode loads one immutable text snapshot, up to 16 MiB. Restart the server to load changed bytes. Telegram media and rich-message bodies are unsupported. Follow the [export and manual client configuration guide](https://github.com/knchst/AnyMessage/blob/v0.7.0/docs/telegram-export.md).

The MCP server exposes read-only message search and attachment access through seven tools: `status`, `list_conversations`, `get_messages`, `get_message_context`, `search_messages`, `list_attachments`, and `read_attachment`.

Use `search_messages` to search 1–8 selected chats with optional UTC Unix-second date bounds. `start_time` is inclusive and `end_time` is exclusive.

Pass a search hit's `conversation_id` and `id` to `get_message_context` as `conversation_id` and `message_id`. It returns the anchor and nearby dated records in chronological order, with `anchor_index` and flags for more records on either side. `before` and `after` each accept 0 to 50 records and default to 3. WeChat queries are not an atomic snapshot. Telegram reports `snapshot_consistency="immutable_export"` and counts undated unsupported records outside chronology.

WeChat attachment descriptors work with `read_attachment`, using locally cached files only. The reader extracts text from PDF, DOCX, XLSX, PPTX, and Unicode text files and returns supported JPEG, PNG, GIF, and WebP images. It does not run OCR or download attachments. Telegram attachment tools return explicit unsupported results without opening media paths.

To print the default WeChat MCP configuration without changing a client file, run `anymessage mcp config --format json`. Telegram requires the separate manual entry in the export guide; `mcp add/config` does not select an export. For client setup and privacy details, see the [AnyMessage documentation](https://github.com/knchst/AnyMessage).

## Maintain the formula

Generate the formula from the release wheel and the matching `uv.lock` using Python 3.11 or later.

```sh
python3 scripts/generate_formula.py --lock /path/to/uv.lock --wheel /path/to/anymessage-0.7.0-py3-none-any.whl
```

The generator checks each wheel URL and checksum against PyPI and the lock. Publish the release wheel at the URL in the formula before installing it. The GitHub Actions workflow uses a macOS 26 runner to link the checkout as a tap, install the formula, and run `brew test`.
