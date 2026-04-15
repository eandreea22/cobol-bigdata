# UI Developer Guide

Quick reference for working with the enhanced Banking System UI.

---

## Quick Start

### File Location
```
ui/app.py — Main Streamlit application with custom CSS and component styling
```

### Running the App
```bash
cd ui/
streamlit run app.py
```

Visit `http://localhost:8501`

---

## Customizing the Design

### 1. Change the Accent Color

**In `inject_custom_css()` function, find:**
```css
--accent: #06b6d4;  /* Current: Cyan */
```

**Replace with your color:**
```css
--accent: #8b5cf6;  /* New: Purple */
```

Then update the hover state:
```css
.stButton > button:hover {
  background-color: #7c3aed;  /* Darker version of new accent */
}
```

### 2. Change Fonts

**In `inject_custom_css()` function, find:**
```css
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;500;600;700;800&family=Inter:wght@400;500;600;700&display=swap');
```

**For different fonts, modify the URL:**
```css
/* Example: Using Outfit + Poppins */
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@600;700;800&family=Poppins:wght@400;500;600;700&display=swap');

/* Then update declarations */
h1, h2, h3, h4, h5, h6 {
  font-family: 'Outfit', sans-serif;
}

body, .stApp {
  font-family: 'Poppins', sans-serif;
}
```

### 3. Modify Spacing

**In CSS, find:**
```css
padding: 1.5rem;  /* Card padding */
margin-bottom: 1.5rem;  /* Section margin */
gap: 2rem;  /* Tab gap */
```

**Adjust to desired spacing (base unit is 0.25rem = 4px):**
```css
padding: 2rem;  /* More spacious */
margin-bottom: 2rem;  /* Larger gaps */
gap: 3rem;  /* Extra space between tabs */
```

### 4. Add/Remove Shadow Levels

**In CSS, find shadow definitions:**
```css
--shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
--shadow-md: 0 4px 6px rgba(0, 0, 0, 0.07);
--shadow-lg: 0 10px 15px rgba(0, 0, 0, 0.1);
```

**Modify opacity or blur values:**
```css
/* Less shadow (lighter UI) */
--shadow-md: 0 2px 4px rgba(0, 0, 0, 0.03);
--shadow-lg: 0 4px 8px rgba(0, 0, 0, 0.05);

/* More shadow (deeper UI) */
--shadow-md: 0 6px 12px rgba(0, 0, 0, 0.1);
--shadow-lg: 0 15px 30px rgba(0, 0, 0, 0.15);
```

---

## Working with Components

### Using Metric Cards

```python
st.markdown(f"""
<div class="metric-card">
    <div class="metric-label">Your Label</div>
    <div class="metric-value">{value}</div>
</div>
""", unsafe_allow_html=True)
```

**Customize metric value size:**
```python
# Small value
<div class="metric-value" style="font-size: 1.5rem;">Small</div>

# Default value (2rem)
<div class="metric-value">Default</div>

# Large value (use for key metrics)
<div class="metric-value" style="font-size: 2.5rem;">Large</div>
```

### Using Status Badges

```python
# Low Risk (Green)
st.markdown(
    '<span class="status-badge badge-success">🟢 LOW RISK</span>',
    unsafe_allow_html=True
)

# Medium Risk (Amber)
st.markdown(
    '<span class="status-badge badge-warning">🟡 MEDIUM RISK</span>',
    unsafe_allow_html=True
)

# High Risk (Red)
st.markdown(
    '<span class="status-badge badge-danger">🔴 HIGH RISK</span>',
    unsafe_allow_html=True
)
```

**Or use the helper functions:**
```python
badge_html = get_risk_badge(risk_score)
st.markdown(badge_html, unsafe_allow_html=True)
```

### Using Info Boxes

```python
st.markdown("""
<div class="info-box">
    <strong>Summary:</strong> Your informational text here.
</div>
""", unsafe_allow_html=True)
```

**With custom border color:**
```python
st.markdown("""
<div class="info-box" style="border-left-color: #ef4444;">
    <strong>Error:</strong> Something went wrong.
</div>
""", unsafe_allow_html=True)
```

### Creating Sections

```python
# Section heading
st.markdown("#### Account Overview")

# Content with divider
col1, col2, col3 = st.columns(3, gap="medium")

# ... content in columns ...

# Divider between sections
st.divider()
```

---

## Color Reference

### Quick Color Lookup

```python
# Primary colors
--primary: #0f172a       # Deep navy (headings)
--accent: #06b6d4        # Cyan (interactive)

# Semantic colors
--success: #10b981       # Green (low risk, approved)
--warning: #f59e0b       # Amber (medium risk)
--danger: #ef4444        # Red (high risk, declined)

# Text colors
--text-primary: #0f172a  # Dark navy (body text)
--text-secondary: #64748b # Slate (secondary text)

# Backgrounds
--bg-light: #f8fafc      # Page background
--bg-card: #ffffff       # Card background
--border: #e2e8f0        # Borders
```

### Using Colors in Custom Styles

```python
st.markdown("""
<div style="color: var(--accent); font-weight: 600;">
    Styled text using design system colors
</div>
""", unsafe_allow_html=True)
```

---

## Typography Reference

### Font Families

```css
/* Display (headings, buttons, metrics) */
font-family: 'Syne', sans-serif;

/* Body (text, labels, descriptions) */
font-family: 'Inter', sans-serif;
```

### Font Sizes & Usage

```python
# Page title (2.5rem / 40px)
st.markdown(f"<h1>{title}</h1>", unsafe_allow_html=True)

# Section heading (1.875rem / 30px)
st.markdown(f"#### {section}")

# Subsection (1.25rem / 20px)
st.markdown(f"##### {subsection}")

# Body text (default Streamlit)
st.write("Normal paragraph text")

# Small text
st.markdown(f"<small>{small_text}</small>", unsafe_allow_html=True)
```

---

## Layout Patterns

### Three-Column Metric Layout

```python
col1, col2, col3 = st.columns(3, gap="medium")

with col1:
    st.markdown("""<div class="metric-card">
        <div class="metric-label">Metric 1</div>
        <div class="metric-value">Value 1</div>
    </div>""", unsafe_allow_html=True)

with col2:
    st.markdown("""<div class="metric-card">
        <div class="metric-label">Metric 2</div>
        <div class="metric-value">Value 2</div>
    </div>""", unsafe_allow_html=True)

with col3:
    st.markdown("""<div class="metric-card">
        <div class="metric-label">Metric 3</div>
        <div class="metric-value">Value 3</div>
    </div>""", unsafe_allow_html=True)
```

### Two-Column Form Layout

```python
col1, col2 = st.columns(2, gap="medium")

with col1:
    input1 = st.text_input("Field 1")
    input2 = st.text_input("Field 2")

with col2:
    select1 = st.selectbox("Option 1", ["A", "B", "C"])
    select2 = st.selectbox("Option 2", ["X", "Y", "Z"])
```

### Responsive Design

Streamlit automatically handles responsive layout:
- **Wide screens:** Columns display as configured
- **Tablet:** Columns may narrow
- **Mobile:** Columns stack vertically

No additional code needed — it's automatic!

---

## Common Customizations

### Change Button Text Color

```css
.stButton > button {
  color: #ffffff;  /* Currently white, change as needed */
}
```

### Make Cards Taller

```python
st.markdown("""
<div class="metric-card" style="padding: 2.5rem 1.5rem; min-height: 200px;">
    <div class="metric-label">Label</div>
    <div class="metric-value">Value</div>
</div>
""", unsafe_allow_html=True)
```

### Disable Card Hover Effect

```python
st.markdown("""
<div class="metric-card" style="transition: none;">
    <div class="metric-label">Label</div>
    <div class="metric-value">Value</div>
</div>
""", unsafe_allow_html=True)
```

### Add Custom Border Color

```python
st.markdown("""
<div class="metric-card" style="border-color: #10b981; border-width: 2px;">
    <div class="metric-label">Success Card</div>
    <div class="metric-value">✓</div>
</div>
""", unsafe_allow_html=True)
```

---

## Performance Tips

### Don't Overuse `unsafe_allow_html=True`

✅ Good: Use for designed components
```python
st.markdown(f'<div class="metric-card">...</div>', unsafe_allow_html=True)
```

❌ Bad: Don't use for simple text
```python
st.markdown('<p>Simple text</p>', unsafe_allow_html=True)  # Use st.write() instead
```

### Cache Custom CSS

The CSS injection already happens once at app start:
```python
def inject_custom_css():
    custom_css = """..."""
    st.markdown(custom_css, unsafe_allow_html=True)

# Called in main() — only injected once
```

---

## Testing Your Changes

### Local Testing
```bash
streamlit run ui/app.py
```

### Testing on Different Screens

Use browser developer tools:
1. Open DevTools (`F12`)
2. Click responsive design mode (`Ctrl+Shift+M`)
3. Test at different viewport widths

### Checking Colors

Use browser color picker in DevTools to verify colors match design system.

---

## Troubleshooting

### CSS Not Applying

**Problem:** Custom styles not showing
- **Solution:** Ensure `unsafe_allow_html=True` is set in `st.markdown()`
- **Check:** Browser console for errors (`F12` → Console tab)

### Font Not Loading

**Problem:** Text using wrong font
- **Solution:** Check Google Fonts import in CSS
- **Fix:** Verify font names match in `@import` and `font-family`

### Colors Look Wrong

**Problem:** Color doesn't match spec
- **Solution:** Check browser color picker (DevTools)
- **Fix:** Ensure hex values are correct in CSS

### Layout Not Responsive

**Problem:** Columns not stacking on mobile
- **Solution:** Streamlit handles this automatically
- **Note:** Test in actual responsive mode (not browser zoom)

---

## Resources

- **Design System:** See `DESIGN-SYSTEM.md`
- **Full Documentation:** See `UI-DESIGN-ENHANCEMENT.md`
- **Color Reference:** Use CSS variables in `:root`
- **Font Files:** Loaded from Google Fonts CDN

---

## Questions?

Refer to the main design documentation:
- `UI-DESIGN-ENHANCEMENT.md` — Full design philosophy and implementation
- `DESIGN-SYSTEM.md` — Complete specification and component library
- `app.py` — Source code with inline comments

---

**Last Updated:** 2026-04-15  
**Design System Version:** 1.0
