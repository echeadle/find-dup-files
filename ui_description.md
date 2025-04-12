# Duplicate File Viewer - HTML Interface Description

## 📋 Overall Layout
The interface consists of a two-column layout:
- **Left sidebar** with navigation links
- **Right main content area** for scanning and displaying results

---

## 🟦 Sidebar (Left)

Styled with a light gray background. Contains vertical navigation:

```html
<div class="sidebar">
  <h2>Navigation</h2>
  <ul>
    <li><a href="/">🏠 Home</a></li>
    <li><a href="/config/excludes">📁❌ Edit Excluded Directories</a></li>
    <li><a href="/config/filetypes">📄 Edit File Types</a></li>
  </ul>
</div>
```

---

## 🟩 Main Content Area (Right)

### Header
```html
<h1>Duplicate File Viewer</h1>
```

### Directory Input + Scan Button
```html
<label for="scanDir">Directory to Scan:</label>
<input type="text" id="scanDir" placeholder="/home/user/Documents" />
<button id="scanBtn">Scan</button>
```

### Status Message Area (Optional)
```html
<div id="statusMessage">Status: Ready to scan...</div>
```

---

## 📄 Scan Results Section

Titled with "Scan Results". Displays hash + list of duplicate files:

```html
<div class="results">
  <h2>Scan Results</h2>

  <div class="dup-group">
    <h4>Duplicate Group: <code>ab12cd34</code></h4>
    <ul>
      <li>/path/to/file1.jpg</li>
      <li>/another/path/file1.jpg</li>
      <li>/more/files/file1.jpg</li>
    </ul>
  </div>

  <div class="dup-group">
    <h4>Duplicate Group: <code>de45ef67</code></h4>
    <ul>
      <li>/path/to/another/file.doc</li>
      <li>/backup/file.doc</li>
    </ul>
  </div>
</div>
```

---

## 🧾 Basic Styling Suggestions (CSS)

```css
body {
  display: flex;
  margin: 0;
  font-family: sans-serif;
}

.sidebar {
  width: 220px;
  background: #f0f0f0;
  padding: 1rem;
  height: 100vh;
}

.sidebar ul {
  list-style: none;
  padding-left: 0;
}

.sidebar li {
  margin-bottom: 1em;
}

.sidebar a {
  text-decoration: none;
  color: #0066cc;
  font-weight: bold;
}

.main-content {
  flex-grow: 1;
  padding: 2rem;
  background: #ffffff;
}

input[type="text"] {
  width: 60%;
  padding: 0.5rem;
  margin-right: 1rem;
}

button {
  padding: 0.5rem 1rem;
}

#statusMessage {
  margin-top: 1em;
  font-style: italic;
  color: #333;
}

.results {
  margin-top: 2em;
}

.results code {
  background: #eee;
  padding: 2px 4px;
  border-radius: 3px;
}
```
