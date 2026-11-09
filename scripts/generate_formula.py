#!/usr/bin/env python3
"""Generate the formula from a release wheel and its uv lock."""
import argparse
import ast
import email.parser
import hashlib
import json
import re
import tomllib
import urllib.request
import zipfile
from pathlib import Path
from urllib.parse import unquote, urlparse

parser = argparse.ArgumentParser()
parser.add_argument('--lock', type=Path, required=True)
parser.add_argument('--wheel', type=Path, required=True)
args = parser.parse_args()
lock = tomllib.loads(args.lock.read_text())
packages = {p['name']: p for p in lock['package']}
with zipfile.ZipFile(args.wheel) as archive:
    metadata_name = next(n for n in archive.namelist() if n.endswith('.dist-info/METADATA'))
    metadata = email.parser.BytesParser().parsebytes(archive.read(metadata_name))
version = metadata['Version']
if metadata['Name'].lower() != 'anymessage' or args.wheel.name != f'anymessage-{version}-py3-none-any.whl':
    raise ValueError('Expected the AnyMessage universal release wheel')
if packages['anymessage']['version'] != version:
    raise ValueError('The release wheel and lock versions differ')

values = {'sys_platform': 'darwin', 'platform_python_implementation': 'CPython', 'implementation_name': 'cpython', 'python_full_version': '3.13.18', 'python_version': '3.13', 'platform_machine': 'arm64', 'platform_system': 'Darwin', 'os_name': 'posix'}
def marker_applies(marker):
    if not marker:
        return True
    def evaluate(node):
        if isinstance(node, ast.Expression):
            return evaluate(node.body)
        if isinstance(node, ast.BoolOp):
            return (all if isinstance(node.op, ast.And) else any)(evaluate(x) for x in node.values)
        if isinstance(node, ast.Name):
            return values[node.id]
        if isinstance(node, ast.Constant):
            return node.value
        if isinstance(node, ast.Compare) and len(node.ops) == 1:
            left, right = evaluate(node.left), evaluate(node.comparators[0])
            if isinstance(node.left, ast.Name) and node.left.id in ('python_version', 'python_full_version'):
                left, right = tuple(map(int, left.split('.'))), tuple(map(int, right.split('.')))
            op = node.ops[0]
            if isinstance(op, ast.Eq): return left == right
            if isinstance(op, ast.NotEq): return left != right
            if isinstance(op, ast.Lt): return left < right
            if isinstance(op, ast.LtE): return left <= right
            if isinstance(op, ast.Gt): return left > right
            if isinstance(op, ast.GtE): return left >= right
            if isinstance(op, ast.In): return left in right
            if isinstance(op, ast.NotIn): return left not in right
        raise ValueError(f'Unsupported marker: {marker}')
    return evaluate(ast.parse(marker, mode='eval'))

roots = [re.match(r'([A-Za-z0-9_.-]+)', requirement).group(1).lower().replace('_', '-') for requirement in metadata.get_all('Requires-Dist', [])]
queue = [(name, ()) for name in roots]
visited = set()
selected = set()
while queue:
    name, extras = queue.pop()
    key = (name, tuple(extras))
    if key in visited:
        continue
    visited.add(key)
    selected.add(name)
    package = packages[name]
    deps = list(package.get('dependencies', []))
    for extra in extras:
        deps.extend(package.get('optional-dependencies', {}).get(extra, []))
    for dep in deps:
        if marker_applies(dep.get('marker')):
            queue.append((dep['name'], dep.get('extra', ())))

def choose_wheel(package, arch):
    candidates = []
    for item in package.get('wheels', []):
        filename = unquote(urlparse(item['url']).path.rsplit('/', 1)[-1])
        parts = filename[:-4].split('-')
        if len(parts) < 5 or not filename.endswith('.whl'):
            continue
        py, abi, platform = parts[-3:]
        if platform == 'any' and abi == 'none' and ('py3' in py.split('.') or 'py313' in py.split('.')):
            candidates.append(((2, 0, 0), item, filename))
        elif (py == 'cp313' and abi == 'cp313' or py.startswith('cp3') and abi == 'abi3' and int(py[2:]) <= 313):
            for tag in platform.split('.'):
                match = re.fullmatch(r'macosx_(\d+)_(\d+)_(arm64|x86_64|universal2)', tag)
                if match and match[3] in (arch, 'universal2') and (int(match[1]), int(match[2])) <= (14, 0):
                    candidates.append(((1, int(match[1]), int(match[2])), item, filename))
    if not candidates:
        raise ValueError(f'No compatible macOS 14 {arch} wheel for {package["name"]} {package["version"]}')
    return max(candidates, key=lambda c: (c[0], c[2]))[1:]

resources = {}
for name in sorted(selected):
    package = packages[name]
    with urllib.request.urlopen(f'https://pypi.org/pypi/{name}/{package["version"]}/json') as response:
        published = {entry['filename']: entry for entry in json.load(response)['urls']}
    resources[name] = {}
    for arch in ('arm64',):
        item, filename = choose_wheel(package, arch)
        entry = published[filename]
        if entry['url'] != item['url'] or 'sha256:' + entry['digests']['sha256'] != item['hash']:
            raise ValueError(f'PyPI and lock disagree for {filename}')
        resources[name][arch] = (item['url'], item['hash'].removeprefix('sha256:'))

def resource(name, data, indent):
    url, sha = data
    return f'{indent}resource "{name}" do\n{indent}  url "{url}", using: :nounzip\n{indent}  sha256 "{sha}"\n{indent}end\n'
shared = list(resources)
sha = hashlib.sha256(args.wheel.read_bytes()).hexdigest()
out = f'''class Anymessage < Formula
  include Language::Python::Virtualenv

  desc "Read-only local messaging MCP server"
  homepage "https://github.com/knchst/AnyMessage"
  url "https://github.com/knchst/AnyMessage/releases/download/v{version}/{args.wheel.name}", using: :nounzip
  sha256 "{sha}"
  license "MIT"

  depends_on macos: :sonoma
  depends_on arch: :arm64
  depends_on "python@3.13"
  depends_on "sqlcipher"

'''
for name in shared:
    out += resource(name, resources[name]['arm64'], '  ') + '\n'
out += '''  def install
    venv = virtualenv_create(libexec, (Formula["python@3.13"].opt_bin/"python3.13").to_s, system_site_packages: false)
    resources.each do |r|
      r.stage do
        venv.pip_install Pathname.pwd/r.downloader.basename
      end
    end
    venv.pip_install_and_link buildpath/"anymessage-#{version}-py3-none-any.whl"
  end

  test do
    ENV["HOME"] = testpath
    ENV["XDG_CONFIG_HOME"] = testpath/"config"
    ENV["XDG_DATA_HOME"] = testpath/"data"
    ENV["ANYMESSAGE_CONFIG_FILE"] = testpath/"config.json"
    ENV["ANYMESSAGE_DATA_DIR"] = testpath/"empty-data"
    ENV.delete("ANYMESSAGE_ACCOUNT")
    ENV.delete("ANYMESSAGE_KEYS_FILE")
    ENV.delete("ANYMESSAGE_SQLCIPHER")
    ENV.prepend_path "PATH", bin
    assert_match version.to_s, shell_output("#{bin}/anymessage --version")
    doctor = JSON.parse(shell_output("#{bin}/anymessage doctor --json", 1))
    assert_equal false, doctor.fetch("ready")
    assert_equal "data_missing", doctor.fetch("source").fetch("state")
    config = JSON.parse(shell_output("#{bin}/anymessage mcp config --format json"))
    assert_equal ["mcp"], config.fetch("mcpServers").fetch("AnyMessage").fetch("args")
    system libexec/"bin/python", "-c", <<~PYTHON, bin/"anymessage"
      import asyncio
      import sys
      from mcp import ClientSession, StdioServerParameters
      from mcp.client.stdio import stdio_client

      async def check():
          async with stdio_client(StdioServerParameters(command=sys.argv[1], args=["mcp"])) as (read, write):
              async with ClientSession(read, write) as session:
                  await session.initialize()
                  tools = await session.list_tools()
                  assert {tool.name for tool in tools.tools} == {"status", "list_conversations", "get_messages", "search_messages", "list_attachments", "read_attachment"}
                  assert all(tool.annotations and tool.annotations.readOnlyHint and tool.annotations.openWorldHint is False for tool in tools.tools)
                  result = await session.call_tool("status", {})
                  assert not result.isError

      asyncio.run(asyncio.wait_for(check(), timeout=30))
    PYTHON
  end
end
'''
Path('Formula/anymessage.rb').write_text(out)
print(f'Generated {len(shared)} resources for Apple Silicon.')
