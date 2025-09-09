# Beehive Tracker Documentation

This directory contains the complete documentation site for the Beehive Photo Metadata Tracker, built with MkDocs and the Material theme.

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- pip or poetry

### Setup Documentation Site

1. **Install dependencies**:
   ```bash
   cd docs_site
   pip install -r requirements.txt
   ```

2. **Serve locally**:
   ```bash
   mkdocs serve
   ```
   
   The documentation will be available at `http://localhost:8000`

3. **Build static site**:
   ```bash
   mkdocs build
   ```

## 📁 Site Structure

```
docs_site/
├── mkdocs.yml              # Main configuration
├── requirements.txt        # Python dependencies
├── docs/                   # Documentation content
│   ├── index.md           # Homepage
│   ├── overview.md        # Project overview
│   ├── architecture.md    # System architecture
│   ├── getting-started/   # Installation & quick start
│   ├── user-guide/        # Feature documentation
│   ├── api-reference/     # Auto-generated API docs
│   ├── deployment/        # Deployment guides
│   └── development/       # Developer resources
├── stylesheets/           # Custom CSS
├── javascripts/           # Custom JavaScript
└── assets/                # Images and static files
```

## ✨ Features

- **Material Design**: Clean, modern interface with light/dark themes
- **Auto-generated API docs**: Python docstrings via mkdocstrings
- **Interactive elements**: Mermaid diagrams, code copying, search
- **Mobile responsive**: Optimized for all device sizes  
- **Beehive-themed styling**: Custom colors and visual elements
- **Rich content**: Cards, callouts, tables, and navigation aids

## 🎨 Customization

### Styling
- Main CSS: `stylesheets/extra.css`
- Custom JavaScript: `javascripts/extra.js`
- Theme colors: Amber/orange palette inspired by bees and honey

### Content
- All content is in Markdown with Material extensions
- Mermaid diagrams for architecture and workflows
- Code syntax highlighting with copy buttons
- Responsive image galleries and cards

## 📝 Contributing

To add or update documentation:

1. Edit Markdown files in `docs/`
2. Test changes: `mkdocs serve`
3. Build for production: `mkdocs build`

### API Documentation
API reference is auto-generated from Python docstrings using Google format:

```python
def example_function(param: str) -> Dict:
    """Brief description.
    
    Longer description here.
    
    Args:
        param: Description of parameter.
        
    Returns:
        Dictionary with result.
        
    Example:
        >>> result = example_function("test")
    """
```

## 🚀 Deployment

The documentation can be deployed to:

- **GitHub Pages**: `mkdocs gh-deploy`
- **Netlify**: Connect to repository, build command: `mkdocs build`
- **Any static host**: Upload contents of `site/` directory

## 🔧 Configuration

Key configuration in `mkdocs.yml`:

- **Theme**: Material with custom colors
- **Plugins**: Search, blog, mkdocstrings, minify
- **Extensions**: All pymdown extensions, Mermaid support
- **Navigation**: Multi-level structure with clear organization

## 📊 Analytics

Add analytics by configuring in `mkdocs.yml`:

```yaml
extra:
  analytics:
    provider: google
    property: G-XXXXXXXXXX
```

---

This documentation site provides a professional, comprehensive resource for users and developers of the Beehive Photo Metadata Tracker. The combination of auto-generated API docs, hand-crafted guides, and interactive features creates an excellent user experience that reflects the quality of the application itself.