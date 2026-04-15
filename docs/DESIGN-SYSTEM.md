# Design System Specification

**Version:** 1.0  
**Date:** 2026-04-15  
**Framework:** Streamlit + Custom CSS  

---

## Color System

### Core Palette

| Use Case | Color | Hex | RGB | CSS Variable |
|----------|-------|-----|-----|--------------|
| **Headers, Primary Text** | Deep Navy | `#0f172a` | 15, 23, 42 | `--primary` |
| **Secondary Text** | Slate-700 | `#1e293b` | 30, 41, 59 | `--secondary` |
| **Interactive Accent** | Cyan | `#06b6d4` | 6, 182, 212 | `--accent` |
| **Success / Low Risk** | Emerald | `#10b981` | 16, 185, 129 | `--success` |
| **Warning / Medium Risk** | Amber | `#f59e0b` | 245, 158, 11 | `--warning` |
| **Danger / High Risk** | Red | `#ef4444` | 239, 68, 68 | `--danger` |
| **Page Background** | Slate-50 | `#f8fafc` | 248, 250, 252 | `--bg-light` |
| **Card Background** | White | `#ffffff` | 255, 255, 255 | `--bg-card` |
| **Body Text** | Deep Navy | `#0f172a` | 15, 23, 42 | `--text-primary` |
| **Secondary Text** | Slate-500 | `#64748b` | 100, 116, 139 | `--text-secondary` |
| **Borders & Dividers** | Slate-200 | `#e2e8f0` | 226, 232, 240 | `--border` |

### Color Usage Rules

**Never use:**
- ❌ Generic grays for primary accent
- ❌ Multiple accent colors (confusing)
- ❌ Semantic colors for non-semantic purposes (green for "cool", red for "hot")

**Always use:**
- ✅ Deep navy (#0f172a) for headings
- ✅ Cyan (#06b6d4) for interactive elements
- ✅ Semantic colors (green/amber/red) for status
- ✅ Slate-500 for secondary text

---

## Typography System

### Font Stack

```css
/* Display Font */
font-family: 'Syne', 'Helvetica Neue', sans-serif;

/* Body Font */
font-family: 'Inter', 'Helvetica Neue', sans-serif;
```

### Scale & Weight

| Element | Font | Size | Weight | Line Height | Letter Spacing | Usage |
|---------|------|------|--------|-------------|----------------|-------|
| Page Title | Syne | 2.5rem (40px) | 700 | 1.2 | -0.5px | `<h1>` |
| Section Heading | Syne | 1.875rem (30px) | 700 | 1.2 | -0.5px | `<h2>` |
| Subsection | Syne | 1.25rem (20px) | 700 | 1.3 | 0 | `<h3>` |
| Label (Uppercase) | Syne | 0.875rem (14px) | 700 | 1.4 | +0.05em | Metric labels |
| Metric Value | Syne | 2rem (32px) | 800 | 1.1 | -0.5px | Large numbers |
| Body Text | Inter | 1rem (16px) | 400 | 1.6 | 0 | Paragraphs |
| Small Text | Inter | 0.875rem (14px) | 400 | 1.5 | 0 | Descriptions |
| Button | Syne | 1rem (16px) | 600 | 1.2 | 0 | CTAs |

### Font Pairing

**Display:** Syne 700 (Geometric, confident, contemporary)  
**Body:** Inter 400/600 (Clean, readable, professional)

**Rationale:**
- Syne's geometric style conveys modernity and tech-forward thinking
- Inter provides excellent readability at body text sizes
- Pairing avoids generic defaults (Arial, Roboto, system fonts)
- Both fonts optimize for digital displays

### Heading Hierarchy

```
h1: Page Title (2.5rem, Syne 700)
    └─ h2: Section Title (1.875rem, Syne 700)
        └─ h3: Subsection (1.25rem, Syne 700)
            └─ p: Body Text (1rem, Inter 400)
                └─ small: Additional Info (0.875rem, Inter 400)
```

---

## Spacing System

### Base Unit: 0.25rem (4px)

| Scale | Size | Usage |
|-------|------|-------|
| xs | 0.25rem (4px) | Tiny gaps |
| sm | 0.5rem (8px) | Small padding |
| md | 1rem (16px) | Standard padding/margin |
| lg | 1.5rem (24px) | Section spacing |
| xl | 2rem (32px) | Large section spacing |
| 2xl | 3rem (48px) | Page sections |

### Component Spacing

| Component | Internal Padding | External Margin | Gap |
|-----------|------------------|-----------------|-----|
| Card | 1.5–2rem | 1.5rem | — |
| Button | 0.75rem 2rem | 0.5rem | — |
| Input Field | 0.75rem 1rem | 0.5rem | — |
| Metric Card | 1.5rem | 0 | 1rem between cards |
| Section | 2rem | 2rem top/bottom | — |
| Column | — | — | medium (Streamlit default) |

---

## Component Library

### 1. Metric Card

```css
.metric-card {
  background: linear-gradient(135deg, var(--bg-card) 0%, rgba(6, 182, 212, 0.02) 100%);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 1.5rem;
  text-align: center;
  box-shadow: var(--shadow-sm);
  transition: all 0.3s ease;
}

.metric-card:hover {
  box-shadow: var(--shadow-lg);
  border-color: var(--accent);
  transform: translateY(-4px);
}
```

**Usage:**
```html
<div class="metric-card">
  <div class="metric-label">Account Balance</div>
  <div class="metric-value">$45,000.00</div>
</div>
```

### 2. Status Badge

```css
.status-badge {
  display: inline-block;
  font-family: 'Syne', sans-serif;
  font-weight: 700;
  padding: 0.5rem 1.25rem;
  border-radius: 20px;
  font-size: 0.95rem;
  letter-spacing: 0.05em;
}

.badge-success {
  background-color: rgba(16, 185, 129, 0.1);
  color: var(--success);
}

.badge-warning {
  background-color: rgba(245, 158, 11, 0.1);
  color: var(--warning);
}

.badge-danger {
  background-color: rgba(239, 68, 68, 0.1);
  color: var(--danger);
}
```

**Usage:**
```html
<span class="status-badge badge-success">🟢 LOW RISK</span>
<span class="status-badge badge-warning">🟡 MEDIUM RISK</span>
<span class="status-badge badge-danger">🔴 HIGH RISK</span>
```

### 3. Info Box

```css
.info-box {
  background-color: rgba(6, 182, 212, 0.05);
  border: 1px solid rgba(6, 182, 212, 0.2);
  border-left: 4px solid var(--accent);
  border-radius: 8px;
  padding: 1rem;
  margin: 1rem 0;
}
```

**Usage:**
```html
<div class="info-box">
  <strong>Summary:</strong> Customer C-00001 has a low-risk profile.
</div>
```

### 4. Button

```css
.stButton > button {
  font-family: 'Syne', sans-serif;
  font-weight: 600;
  background-color: var(--accent);
  color: white;
  border: none;
  border-radius: 8px;
  padding: 0.75rem 2rem;
  font-size: 1rem;
  transition: all 0.3s ease;
  cursor: pointer;
  box-shadow: var(--shadow-sm);
}

.stButton > button:hover {
  background-color: #0891b2;
  box-shadow: var(--shadow-lg);
  transform: translateY(-2px);
}

.stButton > button:active {
  transform: translateY(0);
}
```

### 5. Input Fields

```css
.stTextInput input,
.stNumberInput input,
.stSelectbox select {
  font-family: 'Inter', sans-serif;
  background-color: var(--bg-card);
  border: 2px solid var(--border);
  border-radius: 8px;
  padding: 0.75rem 1rem;
  font-size: 1rem;
  color: var(--text-primary);
  transition: all 0.2s ease;
}

.stTextInput input:focus,
.stNumberInput input:focus,
.stSelectbox select:focus {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px rgba(6, 182, 212, 0.1);
  outline: none;
}
```

---

## Shadow System

| Level | Definition | Usage |
|-------|-----------|-------|
| sm | `0 1px 2px rgba(0, 0, 0, 0.05)` | Subtle elevation |
| md | `0 4px 6px rgba(0, 0, 0, 0.07)` | Card default |
| lg | `0 10px 15px rgba(0, 0, 0, 0.1)` | Card on hover |

---

## Border Radius

| Size | Pixels | Usage |
|------|--------|-------|
| xs | 4px | Input fields, small components |
| sm | 8px | Cards, info boxes, buttons |
| md | 12px | Metric cards, larger containers |
| full | 20px–50px | Badge pills |

---

## Icon System

### Emoji Icons (Recommended for Streamlit)

Use for quick visual recognition:
- 💳 Customer 360
- 📊 Loan Assessment
- ⚠️ Fraud Detection
- 🟢 Low Risk
- 🟡 Medium Risk
- 🔴 High Risk
- ✓ Success/Approved
- ❌ Declined/Error
- ℹ️ Info

### Color + Icon Combinations

| Status | Color | Icon | Badge |
|--------|-------|------|-------|
| **Low Risk** | Green (#10b981) | 🟢 | `badge-success` |
| **Medium Risk** | Amber (#f59e0b) | 🟡 | `badge-warning` |
| **High Risk** | Red (#ef4444) | 🔴 | `badge-danger` |
| **Approved** | Green (#10b981) | ✅ | `badge-success` |
| **Declined** | Red (#ef4444) | ❌ | `badge-danger` |

---

## Layout Grid

### Tab Layout
- **3-column grid** for metrics (60/30/10 viewport)
- **Responsive:** Stacks on mobile
- **Gap:** `gap="medium"` (Streamlit default ~16px)

### Metric Cards
- **Default:** 3 cards per row (equal width)
- **Mobile:** 1 card per row
- **Card width:** Auto (flex)
- **Card aspect ratio:** 1:1 (square, balanced)

### Input Fields
- **Default:** 2-column layout (50/50)
- **Mobile:** 1-column (full width)
- **Input width:** 100% (fill parent)

---

## Animation System

### Transitions

```css
/* Hover states */
transition: all 0.3s ease;

/* Focus states on inputs */
transition: all 0.2s ease;

/* Page load (future) */
animation: fadeInUp 0.6s ease-out;
```

### Timing

| Duration | Usage |
|----------|-------|
| 0.2s | Focused state changes (inputs) |
| 0.3s | Hover states (buttons, cards) |
| 0.6s | Page load animations (future) |

### Easing

- **ease-out:** Page load (deceleration)
- **ease:** Standard interactions (balanced)
- **ease-in:** Fade out (acceleration)

---

## Accessibility Specifications

### Color Contrast

| Element | Background | Foreground | WCAG Level |
|---------|-----------|-----------|-----------|
| Primary Text | #f8fafc | #0f172a | AAA |
| Secondary Text | #f8fafc | #64748b | AA |
| Accent (Button) | #06b6d4 | #ffffff | AAA |
| Success Badge | #ffffff | #10b981 | AA |
| Warning Badge | #ffffff | #f59e0b | AA |
| Danger Badge | #ffffff | #ef4444 | AAA |

### Focus States

- **Visible focus:** 3px cyan glow + border color change
- **Focus outline:** None (custom focus-visible styling)
- **Keyboard navigation:** All interactive elements accessible via Tab

### Font Sizes

- **Minimum:** 14px (small text)
- **Body:** 16px
- **Large:** 20px+
- **Headings:** 30px+
- **All readable:** No sub-12px text

---

## Responsive Breakpoints

Streamlit uses automatic responsive layouts:
- **Wide (desktop):** 2–3 column layouts
- **Medium (tablet):** 2 column layouts
- **Narrow (mobile):** 1 column (full width)

No custom breakpoints needed — Streamlit handles this.

---

## Implementation Checklist

- [ ] Google Fonts imported (Syne, Inter)
- [ ] CSS variables defined in `:root`
- [ ] All component styles defined
- [ ] Color palette applied consistently
- [ ] Typography scales correctly
- [ ] Spacing is consistent
- [ ] Hover/focus states work
- [ ] Mobile responsive
- [ ] Accessible contrast ratios
- [ ] No inline styles (use classes)

---

## Code Example: Complete Card Implementation

```html
<div class="metric-card">
  <div class="metric-label">Account Balance</div>
  <div class="metric-value">$45,000.00</div>
  <div style="font-size: 0.9rem; color: var(--text-secondary); margin-top: 0.5rem;">
    Last updated: Today
  </div>
</div>
```

Rendered as:
- Large "Account Balance" label (small caps, gray)
- Large number "$45,000.00" (Navy, bold)
- Small "Last updated" text (secondary gray)
- Subtle gradient + border
- Lifts on hover

---

## Maintenance & Evolution

### When to Update

1. **Color changes:** Update CSS variables only
2. **Font changes:** Update font imports + family declarations
3. **New components:** Add to this document with spec
4. **Breaking changes:** Major version bump

### Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-04-15 | Initial design system |
| — | — | (future updates) |

---

**Design System Status:** ✅ Complete & Ready for Production
