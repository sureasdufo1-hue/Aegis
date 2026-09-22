import re

with open('dashboard/templates/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Find all fetch('...') or fetch("...") calls
fetch_calls = set(re.findall(r'fetch\(["\']([^"\']+)["\']', content))
print("Static fetch calls found in JS:")
for url in sorted(fetch_calls):
    print(" -", url)

# Find template literal fetch calls
template_fetches = set(re.findall(r'fetch\(`([^`]+)`', content))
print("\nTemplate literal fetch calls:")
for url in sorted(template_fetches):
    print(" -", url)

# Find all SUBMENU_MAP entries and check if switchView handles them
submenus = re.findall(r"['\"]([a-zA-Z0-9_]+)['\"]:\s*\[([^\]]+)\]", content)
print("\nSubmenu categories:")
for cat, items in submenus:
    item_ids = re.findall(r"id:\s*['\"]([^'\"]+)['\"]", items)
    print(f" Category: {cat} -> {item_ids}")
