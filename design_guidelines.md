# CEX/DEX Arbitrage Trading Platform - Design System Guidelines

## CRITICAL: GRADIENT RESTRICTION RULE

**NEVER use dark/saturated gradient combos (e.g., purple/pink, blue-purple, red-pink) on any UI element.**

**ENFORCEMENT RULES:**
- NEVER let gradients cover more than 20% of the viewport
- NEVER apply gradients to text-heavy content or reading areas
- NEVER use gradients on small UI elements (<100px width)
- NEVER stack multiple gradient layers in the same viewport
- IF gradient area exceeds 20% of viewport OR impacts readability, THEN use solid colors only

**ALLOWED GRADIENT USAGE:**
- Subtle background accents in hero sections (if applicable)
- Decorative overlays only (not for this institutional platform)
- **FOR THIS PROJECT: NO GRADIENTS. Use solid colors only for institutional-grade appearance.**

---

## Design Philosophy

**Visual Identity:** Institutional-grade, Fortune 500 quality trading platform with dark mode by default and lime-green accents used SPARINGLY for critical actions, status indicators, and key KPIs.

**Target User:** Professional traders, operators, and institutional users monitoring live arbitrage systems with sub-second latency requirements.

**Tone:** Confident, minimal, data-dense, trustworthy, and professional. No playful elements, no neon effects, no low-contrast text.

**Core Principle:** Reserve lime for decisions, status, and focus. Keep most visuals in cool neutrals (grays, blues). Encode meaning with icon/shape/label, not color alone (color-blind safe).

---

## Color System

### Background Colors (Dark Mode Default)

```json
{
  "app_background": "#0B0F14",
  "surface_1": "#0F141A",
  "surface_2": "#121923",
  "surface_3": "#17202A",
  "description": "Use app_background for main container. surface_1 for cards/panels. surface_2 for nested cards. surface_3 for hover states or elevated elements."
}
```

### Text Colors

```json
{
  "text_primary": "#E5EDF5",
  "text_secondary": "#B6C2CF",
  "text_tertiary": "#7C8AA0",
  "text_muted": "#5A6B7D",
  "description": "text_primary for headings and critical data. text_secondary for labels and descriptions. text_tertiary for metadata and timestamps. text_muted for disabled states."
}
```

### Border Colors

```json
{
  "border_subtle": "#1E2937",
  "border_strong": "#223043",
  "border_focus": "#A3E635",
  "description": "border_subtle for card edges and dividers. border_strong for emphasized boundaries. border_focus for active/focused elements (lime accent)."
}
```

### Accent Colors (Lime Green - Use SPARINGLY)

```json
{
  "lime_400": "#A3E635",
  "lime_500": "#84CC16",
  "lime_700": "#4D7C0F",
  "usage": "lime_400 for primary actions, active states, key KPIs. lime_500 for hover states. lime_700 for pressed/active states.",
  "critical_rule": "Reserve lime for: CTA buttons, status indicators (healthy), active navigation items, focus rings, key metrics that require immediate attention. DO NOT use lime for backgrounds or large areas."
}
```

### Status Colors

```json
{
  "success": "#22C55E",
  "warning": "#F59E0B",
  "danger": "#EF4444",
  "info": "#60A5FA",
  "description": "success for healthy connections, completed trades. warning for degraded performance, pending actions. danger for errors, disconnections. info for informational messages."
}
```

### Trading-Specific Colors

```json
{
  "buy_green": "#22C55E",
  "sell_red": "#F43F5E",
  "neutral_gray": "#7C8AA0",
  "description": "buy_green for buy orders and positive price movements. sell_red for sell orders and negative price movements. neutral_gray for neutral states."
}
```

### CSS Custom Properties (Add to index.css)

```css
:root {
  /* Backgrounds */
  --bg-app: #0B0F14;
  --bg-surface-1: #0F141A;
  --bg-surface-2: #121923;
  --bg-surface-3: #17202A;
  
  /* Text */
  --text-primary: #E5EDF5;
  --text-secondary: #B6C2CF;
  --text-tertiary: #7C8AA0;
  --text-muted: #5A6B7D;
  
  /* Borders */
  --border-subtle: #1E2937;
  --border-strong: #223043;
  --border-focus: #A3E635;
  
  /* Accent Lime */
  --lime-400: #A3E635;
  --lime-500: #84CC16;
  --lime-700: #4D7C0F;
  
  /* Status */
  --status-success: #22C55E;
  --status-warning: #F59E0B;
  --status-danger: #EF4444;
  --status-info: #60A5FA;
  
  /* Trading */
  --trade-buy: #22C55E;
  --trade-sell: #F43F5E;
  
  /* Shadows */
  --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.3);
  --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.4);
  --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.5);
  
  /* Focus Ring */
  --focus-ring: 0 0 0 2px rgba(163, 230, 53, 0.6);
  
  /* Radius */
  --radius-sm: 4px;
  --radius-md: 8px;
  --radius-lg: 16px;
  
  /* Spacing Rhythm */
  --space-xs: 4px;
  --space-sm: 8px;
  --space-md: 16px;
  --space-lg: 24px;
  --space-xl: 32px;
  --space-2xl: 48px;
}
```

---

## Typography System

### Font Families

**Primary Font (UI Text):** Inter
- Use for: Headings, labels, body text, navigation, buttons
- Import: `@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');`

**Secondary Font (Numeric Data):** JetBrains Mono
- Use for: Trading data, prices, percentages, timestamps, tabular numbers, code snippets
- Import: `@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600&display=swap');`
- **Critical:** Enable tabular numbers for alignment in tables using `font-variant-numeric: tabular-nums;`

### Font Size Hierarchy

```json
{
  "h1_main_heading": "text-2xl sm:text-3xl lg:text-4xl (24px/28px/36px)",
  "h2_section_heading": "text-xl sm:text-2xl (20px/24px)",
  "h3_card_heading": "text-lg (18px)",
  "body_default": "text-base (16px)",
  "body_small": "text-sm (14px)",
  "caption_metadata": "text-xs (12px)",
  "trading_data": "text-sm to text-base with JetBrains Mono (14px-16px)",
  "kpi_large": "text-3xl to text-4xl with JetBrains Mono (30px-36px)"
}
```

### Font Weight Usage

```json
{
  "regular_400": "Body text, descriptions, secondary information",
  "medium_500": "Labels, table headers, emphasized text",
  "semibold_600": "Card headings, section titles, button text",
  "bold_700": "Main headings, critical KPIs, primary navigation"
}
```

### Typography CSS Classes (Add to index.css)

```css
/* Typography Base */
body {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  font-feature-settings: 'cv02', 'cv03', 'cv04', 'cv11';
}

.font-mono {
  font-family: 'JetBrains Mono', 'Courier New', monospace;
  font-variant-numeric: tabular-nums;
}

/* Heading Styles */
.heading-1 {
  font-size: 36px;
  font-weight: 700;
  line-height: 1.2;
  color: var(--text-primary);
  letter-spacing: -0.02em;
}

.heading-2 {
  font-size: 24px;
  font-weight: 600;
  line-height: 1.3;
  color: var(--text-primary);
  letter-spacing: -0.01em;
}

.heading-3 {
  font-size: 18px;
  font-weight: 600;
  line-height: 1.4;
  color: var(--text-primary);
}

/* Body Text */
.body-default {
  font-size: 16px;
  font-weight: 400;
  line-height: 1.5;
  color: var(--text-secondary);
}

.body-small {
  font-size: 14px;
  font-weight: 400;
  line-height: 1.5;
  color: var(--text-secondary);
}

.caption {
  font-size: 12px;
  font-weight: 400;
  line-height: 1.4;
  color: var(--text-tertiary);
}

/* Trading Data */
.trading-value {
  font-family: 'JetBrains Mono', monospace;
  font-variant-numeric: tabular-nums;
  font-size: 16px;
  font-weight: 500;
  color: var(--text-primary);
}

.kpi-large {
  font-family: 'JetBrains Mono', monospace;
  font-variant-numeric: tabular-nums;
  font-size: 36px;
  font-weight: 600;
  color: var(--text-primary);
  letter-spacing: -0.02em;
}
```

---

## Component Library

### Shadcn/UI Components to Use

**Primary Components (from /app/frontend/src/components/ui/):**

```json
{
  "navigation": ["navigation-menu.jsx", "breadcrumb.jsx", "tabs.jsx"],
  "data_display": ["table.jsx", "card.jsx", "badge.jsx", "avatar.jsx", "separator.jsx"],
  "forms": ["input.jsx", "select.jsx", "slider.jsx", "switch.jsx", "checkbox.jsx", "radio-group.jsx", "label.jsx"],
  "feedback": ["sonner.jsx", "toast.jsx", "alert.jsx", "progress.jsx", "skeleton.jsx"],
  "overlays": ["dialog.jsx", "sheet.jsx", "popover.jsx", "dropdown-menu.jsx", "tooltip.jsx", "hover-card.jsx"],
  "layout": ["scroll-area.jsx", "resizable.jsx", "collapsible.jsx", "accordion.jsx"]
}
```

### Button Component Specifications

**Style:** Professional/Corporate with minimal radius and subtle elevation

```javascript
// Button variants for institutional trading platform
const buttonVariants = {
  primary: {
    background: "var(--lime-400)",
    color: "#0B0F14",
    hover: "var(--lime-500)",
    active: "var(--lime-700)",
    radius: "6px",
    shadow: "var(--shadow-sm)",
    fontWeight: "600"
  },
  secondary: {
    background: "var(--bg-surface-2)",
    color: "var(--text-primary)",
    border: "1px solid var(--border-strong)",
    hover: "var(--bg-surface-3)",
    radius: "6px",
    fontWeight: "500"
  },
  ghost: {
    background: "transparent",
    color: "var(--text-secondary)",
    hover: "var(--bg-surface-2)",
    radius: "6px",
    fontWeight: "500"
  },
  danger: {
    background: "var(--status-danger)",
    color: "var(--text-primary)",
    hover: "#DC2626",
    radius: "6px",
    fontWeight: "600"
  }
};

// Button sizes
const buttonSizes = {
  sm: "px-3 py-1.5 text-sm",
  md: "px-4 py-2 text-base",
  lg: "px-6 py-3 text-lg"
};
```

**Button States:**
- Default: Base styling with subtle shadow
- Hover: Scale 1.02, brightness increase, transition 120ms
- Focus: Lime focus ring (--focus-ring)
- Active/Pressed: Scale 0.98, darker shade
- Disabled: Opacity 0.5, cursor not-allowed

### Card Component Specifications

```javascript
const cardStyles = {
  background: "var(--bg-surface-1)",
  border: "1px solid var(--border-subtle)",
  borderRadius: "16px",
  padding: "16px",
  boxShadow: "var(--shadow-sm)",
  hover: {
    borderColor: "var(--border-strong)",
    boxShadow: "var(--shadow-md)",
    transition: "all 150ms ease"
  }
};
```

### Table Component Specifications

**Institutional-grade tables with sticky headers and hover states**

```javascript
const tableStyles = {
  container: {
    background: "var(--bg-surface-1)",
    border: "1px solid var(--border-subtle)",
    borderRadius: "12px",
    overflow: "hidden"
  },
  header: {
    background: "var(--bg-surface-2)",
    position: "sticky",
    top: 0,
    zIndex: 10,
    borderBottom: "1px solid var(--border-strong)",
    fontWeight: "600",
    fontSize: "14px",
    color: "var(--text-secondary)",
    textTransform: "uppercase",
    letterSpacing: "0.05em"
  },
  row: {
    height_dense: "36px",
    height_comfortable: "44px",
    borderBottom: "1px solid var(--border-subtle)",
    hover: {
      background: "var(--bg-surface-2)",
      transition: "background 120ms ease"
    }
  },
  cell: {
    padding: "12px 16px",
    fontSize: "14px",
    color: "var(--text-primary)",
    fontFamily: "JetBrains Mono for numeric cells"
  }
};
```

### Badge Component Specifications

```javascript
const badgeVariants = {
  success: {
    background: "rgba(34, 197, 94, 0.15)",
    color: "var(--status-success)",
    border: "1px solid rgba(34, 197, 94, 0.3)"
  },
  warning: {
    background: "rgba(245, 158, 11, 0.15)",
    color: "var(--status-warning)",
    border: "1px solid rgba(245, 158, 11, 0.3)"
  },
  danger: {
    background: "rgba(239, 68, 68, 0.15)",
    color: "var(--status-danger)",
    border: "1px solid rgba(239, 68, 68, 0.3)"
  },
  lime: {
    background: "rgba(163, 230, 53, 0.15)",
    color: "var(--lime-400)",
    border: "1px solid rgba(163, 230, 53, 0.3)"
  },
  neutral: {
    background: "var(--bg-surface-2)",
    color: "var(--text-secondary)",
    border: "1px solid var(--border-subtle)"
  }
};
```

---

## Layout System

### Grid and Spacing

**Spacing Rhythm:** 16/24/32px base rhythm for consistent whitespace

```json
{
  "container_padding": "24px on mobile, 32px on desktop",
  "card_padding": "16px",
  "section_gap": "32px",
  "component_gap": "16px",
  "element_gap": "8px"
}
```

### Navigation Structure

**Top Bar (Sticky):**
- Height: 64px
- Background: var(--bg-surface-1)
- Border bottom: 1px solid var(--border-subtle)
- Contents: Logo (left), Global search (⌘K), CEX/DEX status pills, Notifications, Profile (right)
- Z-index: 50

**Left Sidebar (Collapsible):**
- Width: 240px (expanded), 64px (collapsed)
- Background: var(--bg-surface-1)
- Border right: 1px solid var(--border-subtle)
- Active item indicator: 3px lime border on left edge + lime text color
- Icon + label layout with grouped sections

**Main Content Area:**
- Max width: 1440px
- Padding: 32px
- Background: var(--bg-app)

### Responsive Breakpoints

```json
{
  "mobile": "< 640px",
  "tablet": "640px - 1024px",
  "desktop": "> 1024px",
  "wide": "> 1440px"
}
```

---

## Key UI Patterns

### 1. Live Status Indicators

**CEX/DEX Connection Status Pills:**

```javascript
const statusPills = {
  healthy: {
    background: "rgba(163, 230, 53, 0.15)",
    color: "var(--lime-400)",
    icon: "circle with pulse animation",
    text: "Connected"
  },
  degraded: {
    background: "rgba(245, 158, 11, 0.15)",
    color: "var(--status-warning)",
    icon: "circle with slow pulse",
    text: "Degraded"
  },
  down: {
    background: "rgba(239, 68, 68, 0.15)",
    color: "var(--status-danger)",
    icon: "circle (no pulse)",
    text: "Disconnected"
  }
};
```

**Pulse Animation CSS:**

```css
@keyframes pulse-healthy {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.6; }
}

.status-pulse {
  animation: pulse-healthy 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}
```

### 2. Real-Time Data Streams with Value Change Indicators

**Color-Fade Pulse on Value Changes (NEVER blink):**

```javascript
// Framer Motion implementation
const valueChangeVariants = {
  initial: { scale: 1, backgroundColor: "transparent" },
  positive: {
    scale: [1, 1.05, 1],
    backgroundColor: ["transparent", "rgba(34, 197, 94, 0.2)", "transparent"],
    transition: { duration: 0.6, ease: "easeOut" }
  },
  negative: {
    scale: [1, 1.05, 1],
    backgroundColor: ["transparent", "rgba(244, 63, 94, 0.2)", "transparent"],
    transition: { duration: 0.6, ease: "easeOut" }
  }
};
```

### 3. KPI Cards with Sparklines

**Card Structure:**
- Header: KPI name + info tooltip
- Main value: Large JetBrains Mono font (36px)
- Change indicator: Percentage with up/down arrow
- Sparkline: Mini line chart (height: 40px)
- Period toggle: 1d / 7d / 30d buttons

**Sparkline Implementation:**
- Use Recharts library: `<LineChart>` with minimal styling
- No axes, no grid, just the line
- Line color: lime-400 for positive trend, danger for negative
- Stroke width: 2px
- Smooth curve: `type="monotone"`

### 4. Opportunity Heatmap

**Time-of-Day Pattern Visualization:**
- Grid layout: 24 columns (hours) x 7 rows (days)
- Cell color intensity: Based on opportunity frequency
- Color scale: From bg-surface-2 (low) to lime-400 (high)
- Hover: Tooltip with exact count and time
- Interactive: Click to filter opportunities by time window

### 5. Dual-Leg Execution Timeline

**Visual Representation of Arbitrage Trades:**
- Horizontal timeline with two parallel tracks (CEX and DEX)
- Start marker: Opportunity detected (lime dot)
- CEX leg: Top track with buy/sell indicator
- DEX leg: Bottom track with buy/sell indicator
- Connection line: Dotted line connecting both legs
- End marker: Trade completed (success green or danger red)
- Latency labels: Time taken for each leg

### 6. Risk Control Sliders

**Interactive Risk Management:**
- Use shadcn Slider component
- Track: bg-surface-2 with border-subtle
- Thumb: lime-400 with focus ring
- Fill: lime-400 with 0.3 opacity
- Labels: Current value (left), Max value (right)
- Preview: Real-time impact calculation below slider

---

## Micro-Interactions and Motion

### Animation Timing

```json
{
  "instant": "60ms - Immediate feedback (button press)",
  "fast": "120ms - Hover states, focus changes",
  "normal": "160ms - Card elevation, modal open",
  "slow": "300ms - Page transitions, complex animations",
  "pulse": "2000ms - Status indicators, live data pulse"
}
```

### Easing Functions

```css
:root {
  --ease-in: cubic-bezier(0.4, 0, 1, 1);
  --ease-out: cubic-bezier(0, 0, 0.2, 1);
  --ease-in-out: cubic-bezier(0.4, 0, 0.2, 1);
  --ease-bounce: cubic-bezier(0.68, -0.55, 0.265, 1.55);
}
```

### Hover State Patterns

**Cards:**
```css
.card-hover {
  transition: transform 150ms var(--ease-out), box-shadow 150ms var(--ease-out);
}

.card-hover:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}
```

**Buttons:**
```css
.button-hover {
  transition: transform 120ms var(--ease-out), background-color 120ms var(--ease-out);
}

.button-hover:hover {
  transform: scale(1.02);
}

.button-hover:active {
  transform: scale(0.98);
}
```

**Table Rows:**
```css
.table-row-hover {
  transition: background-color 120ms var(--ease-out);
}

.table-row-hover:hover {
  background-color: var(--bg-surface-2);
}
```

### Focus States

**All interactive elements MUST have visible focus states:**

```css
.focus-visible {
  outline: none;
  box-shadow: var(--focus-ring);
  transition: box-shadow 120ms var(--ease-out);
}
```

### Reduced Motion Support

```css
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

---

## Accessibility Requirements

### Contrast Ratios

**All text must meet WCAG AA standards (4.5:1 minimum):**

- text-primary (#E5EDF5) on app-background (#0B0F14): **15.2:1** ✓
- text-secondary (#B6C2CF) on app-background (#0B0F14): **10.8:1** ✓
- lime-400 (#A3E635) on app-background (#0B0F14): **11.5:1** ✓
- status-success (#22C55E) on app-background (#0B0F14): **7.2:1** ✓

### Keyboard Navigation

- All interactive elements must be keyboard accessible
- Tab order must follow logical reading flow
- Focus indicators must be clearly visible (lime focus ring)
- Escape key closes modals and dropdowns
- Enter/Space activates buttons and toggles

### Screen Reader Support

- Use semantic HTML elements (nav, main, section, article)
- Add ARIA labels for icon-only buttons
- Include alt text for all images
- Use aria-live regions for real-time data updates
- Provide skip navigation links

### Color-Blind Safe Design

**Never rely on color alone to convey information:**
- Use icons + labels + color for status indicators
- Add patterns or shapes to differentiate data
- Provide text alternatives for color-coded information
- Test with color-blind simulation tools

---

## Data Visualization

### Sparklines (Mini Charts)

**Library:** Recharts

**Implementation:**
```javascript
import { LineChart, Line, ResponsiveContainer } from 'recharts';

const SparklineChart = ({ data }) => (
  <ResponsiveContainer width="100%" height={40}>
    <LineChart data={data}>
      <Line 
        type="monotone" 
        dataKey="value" 
        stroke="var(--lime-400)" 
        strokeWidth={2}
        dot={false}
      />
    </LineChart>
  </ResponsiveContainer>
);
```

### Full Charts (Detailed Analysis)

**Library:** Recharts

**Chart Types:**
- Line charts: Price trends, PnL over time
- Bar charts: Volume comparison, opportunity frequency
- Area charts: Cumulative PnL, inventory levels
- Composed charts: Multi-metric overlays

**Chart Styling:**
- Background: var(--bg-surface-1)
- Grid lines: var(--border-subtle)
- Axis labels: text-tertiary, 12px
- Tooltips: bg-surface-2 with border-strong
- Legend: text-secondary, 14px

---

## Screen-Specific Guidelines

### 1. Overview (Operator Home)

**Layout:** 4-column grid on desktop, 2-column on tablet, 1-column on mobile

**Key Components:**
- Net PnL card (large, prominent, with sparkline)
- Capture Rate card (percentage with trend indicator)
- Latency card (average latency with status color)
- Active Windows card (count with live pulse)
- Recent opportunities table (5 rows, scrollable)
- CEX/DEX status pills (top right)

### 2. Opportunities (Live Stream)

**Layout:** Full-width table with filters sidebar

**Key Components:**
- Filter panel (left, collapsible): Exchange, pair, min spread, time range
- Opportunities table: Pair, CEX price, DEX price, spread %, estimated profit, action button
- Window overlay: Click row to open detailed opportunity view
- Real-time updates: New rows fade in from top with lime highlight

### 3. Execution Monitor

**Layout:** Timeline view with dual tracks

**Key Components:**
- Trade selector dropdown (top)
- Dual-leg timeline (CEX top, DEX bottom)
- Latency labels (between legs)
- Status indicators (opportunity detected, legs executed, completed)
- Trade details panel (right): Amounts, fees, net profit

### 4. Trades Ledger

**Layout:** Full-width table with export button

**Key Components:**
- Date range picker (top left)
- Export CSV button (top right)
- Trades table: Timestamp, pair, type, CEX leg, DEX leg, profit, status
- Pagination (bottom)
- Summary row (total profit, total trades)

### 5. Inventory & Rebalance

**Layout:** Grid of venue cards + rebalance panel

**Key Components:**
- Venue cards: Exchange name, asset balances, total value, drift indicator
- Rebalance panel: Source/target selectors, amount input, preview, execute button
- Drift monitoring: Visual indicator (lime = balanced, warning = needs rebalance)

### 6. Risk & Limits

**Layout:** Control panel with sliders and audit trail

**Key Components:**
- Risk sliders: Max position size, max spread, max latency
- Preview panel: Impact calculation, affected opportunities
- Kill switch: Large danger button with confirmation modal
- Audit trail table: Timestamp, user, action, previous value, new value

### 7. Reports

**Layout:** Tab navigation + chart area

**Key Components:**
- Tab navigation: Weekly summary, Time-of-day profile, Venue performance
- Chart area: Recharts visualizations
- Export button: Download as PDF or CSV
- Date range selector

### 8. Settings

**Layout:** Sidebar navigation + content area

**Key Components:**
- Sidebar: API Keys, Endpoints, Feature Flags, Notifications
- Content area: Forms with input fields, switches, and save buttons
- Validation: Real-time feedback with error messages
- Success toast: Confirmation after save

---

## Additional Libraries and Installation

### Required Libraries

```bash
# Install Recharts for data visualization
npm install recharts

# Install Framer Motion for animations
npm install framer-motion

# Install Lucide React for icons
npm install lucide-react

# Install date-fns for date formatting
npm install date-fns

# Install clsx for conditional classes
npm install clsx
```

### Icon Library Usage

**Use Lucide React for all icons:**

```javascript
import { 
  TrendingUp, 
  TrendingDown, 
  Activity, 
  AlertCircle, 
  CheckCircle, 
  XCircle,
  Search,
  Filter,
  Download,
  Settings,
  Bell,
  User
} from 'lucide-react';
```

**Icon Sizing:**
- Small: 16px (w-4 h-4)
- Medium: 20px (w-5 h-5)
- Large: 24px (w-6 h-6)

---

## Testing Attributes

**All interactive and key informational elements MUST include data-testid attributes:**

```javascript
// Examples
<button data-testid="execute-trade-button">Execute</button>
<input data-testid="max-position-size-input" />
<div data-testid="net-pnl-value">{pnl}</div>
<table data-testid="opportunities-table">...</table>
<span data-testid="cex-status-indicator">Connected</span>
```

**Naming Convention:** kebab-case that defines the element's role, not appearance
- Format: `{component}-{action/type}-{element}`
- Examples: `login-form-submit-button`, `opportunity-filter-panel`, `trade-execution-timeline`

---

## Common Mistakes to Avoid

### DON'T:
- Use dark gradients (purple/pink, blue/purple) anywhere
- Apply lime color to large backgrounds or text-heavy areas
- Use gradients on small UI elements or reading areas
- Mix multiple gradient directions in the same section
- Center-align the entire app container (disrupts reading flow)
- Use universal transitions like `transition: all`
- Use emoji characters for icons (🤖💰📊 etc.)
- Ignore hover and focus states
- Skip responsive font sizing
- Forget tabular numbers for trading data

### DO:
- Use solid colors for all backgrounds and content areas
- Reserve lime for CTAs, status indicators, and key metrics
- Maintain consistent spacing using the 16/24/32px rhythm
- Test on mobile devices with touch interactions
- Include accessibility features (focus states, contrast, ARIA labels)
- Use JetBrains Mono with tabular numbers for all numeric data
- Add data-testid attributes to all interactive elements
- Implement micro-animations for hover states (120-160ms)
- Support reduced motion preferences
- Encode meaning with icon + label + color (not color alone)

---

## Implementation Checklist

### Phase 1: Foundation
- [ ] Add CSS custom properties to index.css
- [ ] Import Inter and JetBrains Mono fonts
- [ ] Set up dark mode as default
- [ ] Configure Tailwind with custom colors
- [ ] Install required libraries (Recharts, Framer Motion, Lucide React)

### Phase 2: Core Components
- [ ] Customize shadcn Button component with lime accent
- [ ] Customize shadcn Card component with dark styling
- [ ] Customize shadcn Table component with sticky headers
- [ ] Create status pill component with pulse animation
- [ ] Create KPI card component with sparkline

### Phase 3: Layout
- [ ] Build top navigation bar with status indicators
- [ ] Build left sidebar with active state indicators
- [ ] Set up main content area with responsive grid
- [ ] Implement responsive breakpoints

### Phase 4: Screens
- [ ] Build Overview screen with KPI cards
- [ ] Build Opportunities screen with live table
- [ ] Build Execution Monitor with dual-leg timeline
- [ ] Build Trades Ledger with export functionality
- [ ] Build Inventory & Rebalance screen
- [ ] Build Risk & Limits control panel
- [ ] Build Reports screen with charts
- [ ] Build Settings screen with forms

### Phase 5: Polish
- [ ] Add micro-interactions to all interactive elements
- [ ] Implement real-time data pulse animations
- [ ] Add focus states to all interactive elements
- [ ] Test keyboard navigation
- [ ] Test with screen readers
- [ ] Test color-blind simulation
- [ ] Add data-testid attributes
- [ ] Test responsive behavior on mobile/tablet

---

## Design Tokens Summary (Quick Reference)

```javascript
const designTokens = {
  colors: {
    background: {
      app: "#0B0F14",
      surface1: "#0F141A",
      surface2: "#121923",
      surface3: "#17202A"
    },
    text: {
      primary: "#E5EDF5",
      secondary: "#B6C2CF",
      tertiary: "#7C8AA0",
      muted: "#5A6B7D"
    },
    accent: {
      lime400: "#A3E635",
      lime500: "#84CC16",
      lime700: "#4D7C0F"
    },
    status: {
      success: "#22C55E",
      warning: "#F59E0B",
      danger: "#EF4444",
      info: "#60A5FA"
    },
    trading: {
      buy: "#22C55E",
      sell: "#F43F5E"
    }
  },
  typography: {
    fontFamily: {
      ui: "Inter",
      mono: "JetBrains Mono"
    },
    fontSize: {
      xs: "12px",
      sm: "14px",
      base: "16px",
      lg: "18px",
      xl: "20px",
      "2xl": "24px",
      "3xl": "30px",
      "4xl": "36px"
    },
    fontWeight: {
      regular: 400,
      medium: 500,
      semibold: 600,
      bold: 700
    }
  },
  spacing: {
    xs: "4px",
    sm: "8px",
    md: "16px",
    lg: "24px",
    xl: "32px",
    "2xl": "48px"
  },
  radius: {
    sm: "4px",
    md: "8px",
    lg: "16px"
  },
  timing: {
    instant: "60ms",
    fast: "120ms",
    normal: "160ms",
    slow: "300ms",
    pulse: "2000ms"
  }
};
```

---

## Final Notes

This design system is optimized for institutional-grade arbitrage trading platforms with sub-second latency requirements. The dark mode with lime accents provides excellent readability for extended trading sessions while maintaining a professional, trustworthy appearance.

**Key Principles to Remember:**
1. Reserve lime for critical actions and status indicators only
2. Use JetBrains Mono with tabular numbers for all trading data
3. Maintain 4.5:1 contrast ratio minimum for accessibility
4. Encode meaning with icon + label + color (never color alone)
5. Add micro-interactions to all interactive elements (120-160ms)
6. Support keyboard navigation and screen readers
7. Test with color-blind simulation tools
8. Add data-testid attributes for robust testing

**This design system ensures a Fortune 500-quality trading platform that is functional, accessible, and visually sophisticated.**

---

## General UI/UX Design Guidelines (CRITICAL - READ CAREFULLY)

### Transition Rules
- **NEVER** apply universal transitions like `transition: all` - this breaks transforms
- **ALWAYS** add transitions for specific properties: `transition: background-color 150ms, transform 150ms, box-shadow 150ms`
- **EXCLUDE** transforms from universal transitions to prevent conflicts

### Text Alignment Rules
- **NEVER** center-align the app container (`.App { text-align: center; }`)
- Center alignment disrupts natural reading flow
- Use left-aligned text for body content and descriptions
- Center alignment only for specific components (headings, CTAs)

### Icon Usage Rules
- **NEVER** use emoji characters for icons (🤖🧠💭💡🔮🎯📚 etc.)
- **ALWAYS** use Lucide React icons or FontAwesome CDN
- Lucide React is already installed: `import { IconName } from 'lucide-react'`

### Gradient Restriction Rules (CRITICAL)
- **NEVER** use dark/saturated gradient combos (purple/pink, blue/purple, green/blue, red/pink)
- **NEVER** use dark gradients for logo, testimonial, footer, or any component
- **NEVER** let gradients cover more than 20% of viewport
- **NEVER** apply gradients to text-heavy content or reading areas
- **NEVER** use gradients on small UI elements (<100px width)
- **NEVER** stack multiple gradient layers in same viewport

**ENFORCEMENT RULE:**
- IF gradient area exceeds 20% of viewport OR affects readability, **THEN** use solid colors

**ALLOWED GRADIENT USAGE:**
- Section backgrounds (not content backgrounds)
- Hero section header content (dark to light to dark)
- Decorative overlays and accent elements only
- Hero sections with 2-3 mild colors
- Gradients can be horizontal, vertical, or diagonal

**FOR THIS PROJECT: NO GRADIENTS. Use solid colors only for institutional appearance.**

### Color Guidelines for AI/Voice Applications
- **DO NOT** use purple color for AI chat or voice applications
- **USE** colors like light green, ocean blue, peach orange, or other distinctive colors

### Interaction Guidelines
- Every interaction needs micro-animations: hover states, transitions, parallax effects, entrance animations
- Static designs feel lifeless - add motion to create engagement
- Use 2-3x more spacing than feels comfortable - cramped designs look cheap
- Add subtle grain textures, noise overlays, custom cursors, selection states, loading animations

### Component Reuse
- Prioritize using pre-existing components from `/app/frontend/src/components/ui/`
- Create new components that match existing style and conventions
- Examine existing components to understand project patterns before creating new ones

### Component Library Priority
- **IMPORTANT:** Do not use HTML-based components (dropdown, calendar, toast)
- **MUST** always use shadcn components from `/app/frontend/src/components/ui/` as primary components
- These are modern, stylish, and accessible components

### Export Conventions
- Components **MUST** use named exports: `export const ComponentName = ...`
- Pages **MUST** use default exports: `export default function PageName() {...}`

### Toast Notifications
- Use `sonner` for all toast notifications
- Sonner component located at `/app/frontend/src/components/ui/sonner.jsx`

### Visual Quality
- Use 2-4 color gradients (when allowed), subtle textures/noise overlays, or CSS-based noise to avoid flat visuals
- The result should feel human-made, visually appealing, converting, and easy for AI agents to implement
- Maintain good contrast, balanced font sizes, proper gradients (when allowed), sufficient whitespace, thoughtful motion and hierarchy
- Avoid overuse of elements - deliver a polished, effective design system

### Calendar Components
- If calendar is required, **ALWAYS** use shadcn calendar component
- Located at `/app/frontend/src/components/ui/calendar.jsx`

### Testing Attributes (CRITICAL)
- All interactive and key informational elements **MUST** include `data-testid` attribute
- This facilitates robust automated testing
- Applies to: buttons, links, form inputs, menus, any element users interact with or that displays critical information
- Use kebab-case convention that defines element's role, not appearance
- Example: `data-testid="login-form-submit-button"`
- Creates stable, decoupled interface for tests, preventing breaks from stylistic refactors

---

**END OF DESIGN GUIDELINES**
