# UI/UX Design Prompt for Google Stitch

## Project Overview

**Project Name:** GROWW Weekly Review Pulse Agent Dashboard

**Framework:** Next.js (React-based framework)

**Purpose:** A dashboard for monitoring and managing the GROWW Weekly Review Pulse Agent, which analyzes app store reviews and generates weekly pulse notes for the GROWW Mutual Fund app.

---

## Design Goals

Create a modern, clean, and professional dashboard that allows product teams, support teams, and leadership to:
- Monitor pipeline runs and their status
- View weekly pulse content
- Track review trends and themes
- Configure agent parameters
- Receive alerts on failures

---

## Target Audience

1. **Product/Growth Teams** - Need to understand what to fix next
2. **Support Teams** - Need to know what users are saying
3. **Leadership** - Need quick weekly health pulse
4. **DevOps/Engineering** - Need to monitor pipeline health

---

## Design Style & Aesthetics

- **Color Palette:** Professional financial services aesthetic
  - Primary: Deep blue/navy (#1a365d)
  - Secondary: Growth green (#38a169)
  - Accent: Warning orange (#dd6b20)
  - Background: Light gray/white (#f7fafc)
  - Text: Dark gray (#2d3748)

- **Typography:** Clean, modern sans-serif (Inter or similar)
  - Headings: Bold, clear hierarchy
  - Body: Readable, good contrast
  - Monospace for code/logs

- **Visual Style:**
  - Card-based layout
  - Subtle shadows and borders
  - Rounded corners (8px-12px)
  - Clean whitespace
  - Professional, trustworthy feel

---

## Key Screens & Components

### 1. Dashboard Home

**Purpose:** High-level overview of recent pipeline runs and system health

**Components:**
- **Header:** Logo, navigation, user profile
- **Summary Cards:**
  - Last run status (success/failure/partial)
  - Reviews processed this week
  - Themes identified
  - Pulse word count
- **Recent Runs Table:**
  - Run ID, timestamp, status, duration, tokens used
  - Click to view details
- **Quick Actions:**
  - "Run Pipeline Now" button
  - "View Latest Pulse" button
  - "Configure Agent" button

**Layout:**
- Top: Header
- Upper section: 4 summary cards in a row
- Middle section: Recent runs table
- Bottom section: Quick actions

---

### 2. Pipeline Run Details

**Purpose:** Detailed view of a single pipeline run

**Components:**
- **Run Header:**
  - Run ID, timestamp, status badge
  - Configuration summary (weeks, dry-run mode, etc.)
- **Stage Progress:**
  - Visual timeline showing stages (Ingestion → Analysis → Generation → Delivery)
  - Each stage shows: status, duration, tokens used
  - Failed stages highlighted in red
- **Metrics Section:**
  - Review count, theme count, pulse word count
  - Token usage vs budget
  - Duration breakdown
- **Output Section:**
  - Generated pulse content (markdown rendered)
  - Themes with quotes
  - Delivery results (Doc URL, Draft ID)
- **Error Section:**
  - List of errors (if any)
  - Error details and stack traces

**Layout:**
- Top: Run header
- Middle: Stage progress timeline
- Bottom: Tabs for Metrics, Output, Errors

---

### 3. Pulse Content Viewer

**Purpose:** View and review generated weekly pulse content

**Components:**
- **Pulse Header:**
  - Date range
  - Theme count
  - Word count
- **Pulse Content:**
  - Rendered markdown with proper formatting
  - Headers, bullet points, quotes styled appropriately
- **Action Buttons:**
  - "Copy to Clipboard"
  - "Download as PDF"
  - "Share via Email"
  - "Edit Pulse" (for manual adjustments)

**Layout:**
- Left: Pulse content (main area)
- Right: Action buttons and metadata sidebar

---

### 4. Configuration Panel

**Purpose:** Configure agent parameters

**Components:**
- **Form Sections:**
  - **Ingestion Settings:**
    - Weeks to look back (slider: 1-52)
    - Review source selection (Play Store, App Store, both)
  - **Analysis Settings:**
    - Max themes (slider: 1-10)
    - Sample count (number input)
    - Batch size (number input)
  - **Generation Settings:**
    - Max words (number input)
    - LLM model selection (dropdown)
  - **Delivery Settings:**
    - Google Doc ID (text input)
    - Gmail recipient (email input)
    - Alert channel (radio: email/slack)
  - **Budget Settings:**
    - Token budget (number input)
- **Save/Reset Buttons**
- **Validation Messages**

**Layout:**
- Left: Configuration form with sections
- Right: Preview of current configuration

---

### 5. Alerts & Notifications

**Purpose:** View and manage system alerts

**Components:**
- **Alert List:**
  - Timestamp, severity (critical/warning/info), message
  - Run ID link
  - Status (acknowledged/unacknowledged)
- **Filter Controls:**
  - Severity filter
  - Date range filter
  - Status filter
- **Alert Detail Modal:**
  - Full error message
  - Stack trace
  - Related run details
  - Acknowledge button

**Layout:**
- Top: Filter controls
- Middle: Alert list
- Bottom: Pagination

---

### 6. Analytics & Trends

**Purpose:** Visualize review trends and theme evolution over time

**Components:**
- **Date Range Picker**
- **Charts:**
  - Review volume over time (line chart)
  - Rating distribution (pie/bar chart)
  - Theme frequency over time (stacked bar chart)
  - Token usage trends (line chart)
- **Theme Cloud:**
  - Visual representation of common themes
  - Size indicates frequency
- **Export Button**

**Layout:**
- Top: Date range picker
- Middle: Charts grid (2x2)
- Bottom: Theme cloud

---

## UI Components Library

### Buttons

- **Primary Button:** Solid blue, white text, rounded corners
- **Secondary Button:** Outline blue, blue text
- **Danger Button:** Solid red, white text (for destructive actions)
- **Success Button:** Solid green, white text
- **Icon Button:** Icon only, subtle background on hover

### Cards

- White background
- Subtle border (#e2e8f0)
- Rounded corners (8px)
- Box shadow (small)
- Padding: 16px-24px

### Tables

- Clean rows with hover effect
- Sortable headers
- Pagination at bottom
- Status badges (green for success, red for failure, yellow for partial)

### Forms

- Labeled inputs with clear focus states
- Validation error messages below fields
- Group related fields in sections
- Save/Cancel action buttons at bottom

### Modals

- Overlay with backdrop blur
- Centered content
- Close button in top-right
- Action buttons at bottom

### Navigation

- Sidebar navigation (collapsible)
- Active state highlighting
- Icons for each section
- Breadcrumb for nested pages

---

## Responsive Design

- **Desktop (1440px+):** Full sidebar, multi-column layouts
- **Tablet (768px-1439px):** Collapsible sidebar, stacked cards
- **Mobile (<768px):** Bottom navigation, single column, simplified views

---

## Accessibility

- WCAG AA compliance
- Keyboard navigation support
- Screen reader friendly
- High contrast mode support
- Focus indicators on interactive elements

---

## Next.js-Specific Considerations

- **Server-Side Rendering:** Use Next.js SSR for initial page loads
- **Client-Side Navigation:** Use Next.js Link component for smooth transitions
- **API Routes:** Use Next.js API routes for backend communication
- **Static Generation:** Pre-render static pages where possible
- **Image Optimization:** Use Next.js Image component for optimized images
- **Font Optimization:** Use Next.js font optimization

---

## Data Visualization

Use a charting library compatible with Next.js (e.g., Recharts, Chart.js, or Victory.js):
- Line charts for trends
- Bar charts for comparisons
- Pie charts for distributions
- Color-coded data points for status

---

## Loading States

- Skeleton screens for content loading
- Spinners for button actions
- Progress bars for long-running operations
- Error boundaries for graceful failure handling

---

## Empty States

- Friendly illustrations or icons
- Clear messaging explaining why there's no data
- Call-to-action buttons to add data or trigger actions

---

## Dark Mode Support

- Toggle switch in header
- Inverted color palette
- Maintains contrast ratios
- Persists user preference

---

## Internationalization (i18n)

- Support for multiple languages
- Date/time localization
- Number formatting
- RTL language support

---

## Performance Considerations

- Lazy loading for heavy components
- Code splitting for routes
- Optimistic UI updates
- Debounced search inputs
- Virtual scrolling for long lists

---

## Security UI

- Secure badge for authenticated areas
- Mask sensitive data (API keys, tokens)
- Confirmation dialogs for destructive actions
- Audit log viewer for admin users

---

## Branding

- GROWW logo in header
- Consistent use of brand colors
- Professional financial services aesthetic
- Trustworthy and modern feel

---

## Deliverables

Please generate UI mockups/images for the following screens:
1. Dashboard Home
2. Pipeline Run Details
3. Pulse Content Viewer
4. Configuration Panel
5. Alerts & Notifications
6. Analytics & Trends

Each mockup should show:
- Desktop view (1440px width)
- Mobile view (375px width)
- Dark mode variant (optional)

---

## Additional Notes

- The dashboard should feel like a professional SaaS product
- Emphasize clarity and ease of use over complex visual effects
- Ensure data is presented in a scannable, digestible format
- Include micro-interactions for better user experience
- Consider adding onboarding tour for first-time users
