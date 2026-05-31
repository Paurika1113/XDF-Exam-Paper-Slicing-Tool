with open('E:/AIzy/github/edgeone_deploy/index.html', 'r', encoding='utf-8') as f:
    c = f.read()

# Fix 1: Add responseType blob
c = c.replace("x.open('POST', apiUrl('/api/slice'));", "x.open('POST', apiUrl('/api/slice'));\n      x.responseType = 'blob';")

# Fix 2: Fix revokeObjectURL timing
old = "document.body.removeChild(a);\n  URL.revokeObjectURL(url);\n  addLog('success', '\\u5df2\\u5f00\\u59cb\\u4e0b\\u8f7d \\u5207\\u7247\\u7ed3\\u679c.zip');"
new = "document.body.removeChild(a);\n  setTimeout(function() { URL.revokeObjectURL(url); }, 5000);\n  addLog('success', '\\u5df2\\u5f00\\u59cb\\u4e0b\\u8f7d');"
c = c.replace(old, new)

with open('E:/AIzy/github/edgeone_deploy/index.html', 'w', encoding='utf-8') as f:
    f.write(c)

print('done')
