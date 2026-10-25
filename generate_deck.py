from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)

# Visual Theme: Slate / Cyber Cyan
BG = RGBColor(11, 15, 25)          # Deep obsidian #0B0F19
CARD = RGBColor(22, 30, 49)        # Card surface #161E31
CARD_BORDER = RGBColor(38, 50, 79) # Border #26324F
TEXT_TITLE = RGBColor(255, 255, 255)
TEXT_BODY = RGBColor(203, 213, 225)
TEXT_MUTED = RGBColor(148, 163, 184)
CYAN = RGBColor(56, 189, 248)       # #38BDF8
GREEN = RGBColor(52, 211, 153)      # #34D399
RED = RGBColor(248, 113, 113)       # #F87171

def set_bg(slide):
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb = BG

def add_header(slide, tag, title):
    box = slide.shapes.add_textbox(Inches(0.8), Inches(0.4), Inches(11.7), Inches(1.1))
    tf = box.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
    
    p_tag = tf.paragraphs[0]
    p_tag.text = tag.upper()
    p_tag.font.size = Pt(11)
    p_tag.font.bold = True
    p_tag.font.color.rgb = CYAN
    
    p_title = tf.add_paragraph()
    p_title.text = title
    p_title.font.size = Pt(22)
    p_title.font.bold = True
    p_title.font.color.rgb = TEXT_TITLE

def add_card(slide, left, top, width, height, border_color=CARD_BORDER):
    card = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, width, height)
    card.fill.solid()
    card.fill.fore_color.rgb = CARD
    card.line.color.rgb = border_color
    card.line.width = Pt(1.5)
    return card

blank = prs.slide_layouts[6]

# ==========================================
# SLIDE 1: COVER
# ==========================================
s1 = prs.slides.add_slide(blank)
set_bg(s1)

tbox = s1.shapes.add_textbox(Inches(1.0), Inches(1.8), Inches(11.3), Inches(3.6))
tf = tbox.text_frame
tf.word_wrap = True
p = tf.paragraphs[0]
p.text = "ReplyFlow"
p.font.size = Pt(48)
p.font.bold = True
p.font.color.rgb = TEXT_TITLE

p2 = tf.add_paragraph()
p2.text = "Autonomous Customer Operations Workforce"
p2.font.size = Pt(22)
p2.font.bold = True
p2.font.color.rgb = CYAN

p3 = tf.add_paragraph()
p3.text = "\nReplacing slow virtual assistants with real-time omnichannel lead triage, grounded inventory resolution, and automated escalation."
p3.font.size = Pt(14)
p3.font.color.rgb = TEXT_BODY

pills = ["ZETARIS (Data Fabric)", "METERLESS (Token Control)", "NVIDIA (NeMo Safety)", "CURSOR (AI Built)"]
for i, pill in enumerate(pills):
    pill_shape = s1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(1.0 + i * 2.85), Inches(5.8), Inches(2.65), Inches(0.55))
    pill_shape.fill.solid()
    pill_shape.fill.fore_color.rgb = CARD
    pill_shape.line.color.rgb = CYAN
    ptf = pill_shape.text_frame
    ptf.text = pill
    ptf.paragraphs[0].font.size = Pt(10)
    ptf.paragraphs[0].font.bold = True
    ptf.paragraphs[0].font.color.rgb = TEXT_TITLE
    ptf.paragraphs[0].alignment = PP_ALIGN.CENTER

# ==========================================
# SLIDE 2: THE BRUTAL REALITY
# ==========================================
s2 = prs.slides.add_slide(blank)
set_bg(s2)
add_header(s2, "The Reality", "Why Businesses Burn Cash & Abandon Ready Buyers")

stats = [
    ("60%", "INBOUND LEADS LOST", "Inquiries through WhatsApp and DMs go unanswered until prospective buyers move on to alternatives.", RED),
    ("18 hrs", "AVERAGE VA RESPONSE LAG", "Human customer teams and offshore assistants cannot sustain instant 24/7 coverage across channels.", CYAN),
    ("10,000+", "VIRAL COMMENTS UNREAD", "90% is hype or emojis, but high-ticket inquiries and brand-damaging grievances get lost in the noise.", GREEN)
]

for i, (num, label, desc, color) in enumerate(stats):
    c = add_card(s2, Inches(0.8 + i * 4.0), Inches(1.8), Inches(3.7), Inches(4.8))
    tf = c.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = Inches(0.3)
    p = tf.paragraphs[0]
    p.text = num
    p.font.size = Pt(44)
    p.font.bold = True
    p.font.color.rgb = color
    
    p2 = tf.add_paragraph()
    p2.text = label
    p2.font.size = Pt(12)
    p2.font.bold = True
    p2.font.color.rgb = TEXT_TITLE
    
    p3 = tf.add_paragraph()
    p3.text = "\n" + desc
    p3.font.size = Pt(13)
    p3.font.color.rgb = TEXT_BODY

# ==========================================
# SLIDE 3: THE SPARK (FOUNDER STORY)
# ==========================================
s3 = prs.slides.add_slide(blank)
set_bg(s3)
add_header(s3, "The Founder Story", "A Broken Real-World Telecom Experience Sparked ReplyFlow")

c_left = add_card(s3, Inches(0.8), Inches(1.8), Inches(5.6), Inches(4.8), RED)
tf_l = c_left.text_frame
tf_l.word_wrap = True
tf_l.margin_left = tf_l.margin_right = tf_l.margin_top = Inches(0.3)
tf_l.paragraphs[0].text = "❌ The Status Quo (Real Telecom Incident)"
tf_l.paragraphs[0].font.size = Pt(15)
tf_l.paragraphs[0].font.bold = True
tf_l.paragraphs[0].font.color.rgb = RED

story_left = [
    "A SIM card failure led me to a major African telecom's official WhatsApp support.",
    "The AI returned generic, irrelevant walls of text with zero context.",
    "Asking for a human repeated the exact same bot response.",
    "The ticket remained unresolved for 2+ days with zero escalation.",
    "Result: Lost customer trust and permanent brand damage."
]
for item in story_left:
    p = tf_l.add_paragraph()
    p.text = "\n• " + item
    p.font.size = Pt(12)
    p.font.color.rgb = TEXT_BODY

c_right = add_card(s3, Inches(6.8), Inches(1.8), Inches(5.6), Inches(4.8), GREEN)
tf_r = c_right.text_frame
tf_r.word_wrap = True
tf_r.margin_left = tf_r.margin_right = tf_r.margin_top = Inches(0.3)
tf_r.paragraphs[0].text = "✅ The ReplyFlow Standard"
tf_r.paragraphs[0].font.size = Pt(15)
tf_r.paragraphs[0].font.bold = True
tf_r.paragraphs[0].font.color.rgb = GREEN

story_right = [
    "Sub-Second Intent Triage: Understands real problem immediately.",
    "Zero-Copy Grounding: Queries actual inventory & account data.",
    "Safe Automated Negotiation: Quotes firm pricing & provisions bookings.",
    "Executive Support Brief: Auto-pauses bot and summarizes issue for staff.",
    "Result: Resolution in under 250ms with clean escalation paths."
]
for item in story_right:
    p = tf_r.add_paragraph()
    p.text = "\n• " + item
    p.font.size = Pt(12)
    p.font.color.rgb = TEXT_BODY

# ==========================================
# SLIDE 4: 5-NODE ARCHITECTURE PIPELINE
# ==========================================
s4 = prs.slides.add_slide(blank)
set_bg(s4)
add_header(s4, "Multi-Agent System", "LangGraph 5-Node Deterministic Execution Flow (~212ms)")

steps = [
    ("Step 1: Inbound Triage", "25ms | 110t", "Filters 0-token spam.\nIdentifies 5 intent categories."),
    ("Step 2: Zetaris Fabric", "91ms | 280t", "Queries physical POS & Excel depots live.\nZero data copying."),
    ("Step 3: Commercial Scope", "40ms | 290t", "Quotes firm prices.\nProvisions Google Meet links."),
    ("Step 4: NVIDIA NeMo Gate", "12ms | 35t", "Guards price floors.\nBlocks prompt injection."),
    ("Step 5: Action & Dispatch", "10ms | 15t", "Routes directly to WhatsApp, IG DMs, or Live Inbox.")
]

for i, (title, meta, desc) in enumerate(steps):
    c = add_card(s4, Inches(0.7 + i * 2.4), Inches(2.0), Inches(2.25), Inches(4.5))
    tf = c.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = Inches(0.2)
    p = tf.paragraphs[0]
    p.text = title
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = CYAN
    
    p2 = tf.add_paragraph()
    p2.text = meta
    p2.font.size = Pt(11)
    p2.font.bold = True
    p2.font.color.rgb = GREEN
    
    p3 = tf.add_paragraph()
    p3.text = "\n" + desc
    p3.font.size = Pt(12)
    p3.font.color.rgb = TEXT_BODY

# ==========================================
# SLIDE 5: 0-TOKEN NOISE FILTER & CHANNELS
# ==========================================
s5 = prs.slides.add_slide(blank)
set_bg(s5)
add_header(s5, "Social Ingress", "Omnichannel Ingestion & 0-Cost Spam Filter")

c5_left = add_card(s5, Inches(0.8), Inches(1.8), Inches(4.5), Inches(4.8))
tf5 = c5_left.text_frame
tf5.word_wrap = True
tf5.margin_left = tf5.margin_right = tf5.margin_top = Inches(0.3)
tf5.paragraphs[0].text = "5 Engagement Tiers"
tf5.paragraphs[0].font.size = Pt(16)
tf5.paragraphs[0].font.bold = True
tf5.paragraphs[0].font.color.rgb = CYAN

tiers = [
    ("1. Noise & Emojis", "Dropped at 0 tokens (No LLM burn)"),
    ("2. Commercial Leads", "1-Click bridge to private WhatsApp"),
    ("3. Brand Sarcasm", "Polite, fact-grounded responses"),
    ("4. Support Disputes", "Escalated immediately to Live Inbox"),
    ("5. B2B Partnerships", "Calendar & scoping discovery bridge")
]
for name, desc in tiers:
    p = tf5.add_paragraph()
    p.text = f"\n• {name}:\n  {desc}"
    p.font.size = Pt(11)
    p.font.color.rgb = TEXT_BODY

c5_right = add_card(s5, Inches(5.6), Inches(1.8), Inches(6.9), Inches(4.8))
tf_img = c5_right.text_frame
tf_img.word_wrap = True
tf_img.margin_top = Inches(1.8)
p = tf_img.paragraphs[0]
p.text = "[ DROP SCREENSHOT HERE ]\n\n'Connected Communication Channels' & '5-Category Governance Panel'"
p.font.size = Pt(14)
p.font.color.rgb = TEXT_MUTED
p.alignment = PP_ALIGN.CENTER

# ==========================================
# SLIDE 6: ZETARIS ZERO-COPY FABRIC
# ==========================================
s6 = prs.slides.add_slide(blank)
set_bg(s6)
add_header(s6, "Sponsor Integration: Zetaris", "Zero-Copy Unified Semantic Layer Across Disconnected Silos")

c6_left = add_card(s6, Inches(0.8), Inches(1.8), Inches(4.5), Inches(4.8))
tf6 = c6_left.text_frame
tf6.word_wrap = True
tf6.margin_left = tf6.margin_right = tf6.margin_top = Inches(0.3)
tf6.paragraphs[0].text = "The Grounding Solution"
tf6.paragraphs[0].font.size = Pt(16)
tf6.paragraphs[0].font.bold = True
tf6.paragraphs[0].font.color.rgb = CYAN

z_points = [
    "Silo A: Akwa Showroom POS Register.",
    "Silo B: Yaounde Cloud Spreadsheet Depot.",
    "Standard Failure: Website catalog says 'Out of Stock' while 14 Space Black iPhones sit in depot.",
    "Zetaris Fix: Federated ANSI SQL queries POS + Spreadsheets live in 91ms.",
    "Zero data migration. Zero stale cache."
]
for item in z_points:
    p = tf6.add_paragraph()
    p.text = "\n• " + item
    p.font.size = Pt(11)
    p.font.color.rgb = TEXT_BODY

c6_right = add_card(s6, Inches(5.6), Inches(1.8), Inches(6.9), Inches(4.8))
tf6_r = c6_right.text_frame
tf6_r.word_wrap = True
tf6_r.margin_top = Inches(1.8)
p = tf6_r.paragraphs[0]
p.text = "[ DROP SCREENSHOT HERE ]\n\n'Branch Locations & Live Inventory Sources'\n(Branch #1 POS + Branch #2 Spreadsheet)"
p.font.size = Pt(14)
p.font.color.rgb = TEXT_MUTED
p.alignment = PP_ALIGN.CENTER

# ==========================================
# SLIDE 7: AI EXECUTIVE HANDOFF BRIEF
# ==========================================
s7 = prs.slides.add_slide(blank)
set_bg(s7)
add_header(s7, "Clean Human Escalation", "AI Executive Handoff Brief: Zero-Scrolling Staff Takeover")

c7_left = add_card(s7, Inches(0.8), Inches(1.8), Inches(4.5), Inches(4.8))
tf7 = c7_left.text_frame
tf7.word_wrap = True
tf7.margin_left = tf7.margin_right = tf7.margin_top = Inches(0.3)
tf7.paragraphs[0].text = "The 4-Point Summary"
tf7.paragraphs[0].font.size = Pt(16)
tf7.paragraphs[0].font.bold = True
tf7.paragraphs[0].font.color.rgb = GREEN

b_points = [
    "1. Customer Goal: What the client actually wants.",
    "2. What AI Discussed: The context and proposed resolution.",
    "3. Escalation Blocker: Why the bot stopped (e.g., SLA review requested).",
    "4. Recommended Staff Next Step: Concrete guidance for the human agent.",
    "Bot replies pause automatically. Staff take over with 1 click."
]
for item in b_points:
    p = tf7.add_paragraph()
    p.text = "\n• " + item
    p.font.size = Pt(11)
    p.font.color.rgb = TEXT_BODY

c7_right = add_card(s7, Inches(5.6), Inches(1.8), Inches(6.9), Inches(4.8))
tf7_r = c7_right.text_frame
tf7_r.word_wrap = True
tf7_r.margin_top = Inches(1.8)
p = tf7_r.paragraphs[0]
p.text = "[ DROP SCREENSHOT HERE ]\n\n'AI Executive Handoff Brief (Active Support Ticket)' in Live Inbox"
p.font.size = Pt(14)
p.font.color.rgb = TEXT_MUTED
p.alignment = PP_ALIGN.CENTER

# ==========================================
# SLIDE 8: OBSERVABILITY WATERFALL
# ==========================================
s8 = prs.slides.add_slide(blank)
set_bg(s8)
add_header(s8, "Observability", "Live Execution Waterfall: 'The Agent That Explains Why'")

c8_left = add_card(s8, Inches(0.8), Inches(1.8), Inches(4.5), Inches(4.8))
tf8 = c8_left.text_frame
tf8.word_wrap = True
tf8.margin_left = tf8.margin_right = tf8.margin_top = Inches(0.3)
tf8.paragraphs[0].text = "Real-Time Telemetry"
tf8.paragraphs[0].font.size = Pt(16)
tf8.paragraphs[0].font.bold = True
tf8.paragraphs[0].font.color.rgb = CYAN

w_points = [
    "Total Execution Latency: 212ms - 4,946ms cold.",
    "Tokens Burned: 780 tokens per verified commercial resolution.",
    "Transparent Step Breakdown: Triage -> Zetaris -> Scoping -> NVIDIA NeMo Guard.",
    "Audit & Learning Farm: Human edits automatically retrain the Business Brain."
]
for item in w_points:
    p = tf8.add_paragraph()
    p.text = "\n• " + item
    p.font.size = Pt(11)
    p.font.color.rgb = TEXT_BODY

c8_right = add_card(s8, Inches(5.6), Inches(1.8), Inches(6.9), Inches(4.8))
tf8_r = c8_right.text_frame
tf8_r.word_wrap = True
tf8_r.margin_top = Inches(1.8)
p = tf8_r.paragraphs[0]
p.text = "[ DROP SCREENSHOT HERE ]\n\n'Execution Waterfall & Audit' panel showing Step 1 through Step 5"
p.font.size = Pt(14)
p.font.color.rgb = TEXT_MUTED
p.alignment = PP_ALIGN.CENTER

# ==========================================
# SLIDE 9: METERLESS & NVIDIA
# ==========================================
s9 = prs.slides.add_slide(blank)
set_bg(s9)
add_header(s9, "Sponsors: Meterless & NVIDIA", "Margin Protection & Enterprise Safety Gates")

c9_left = add_card(s9, Inches(0.8), Inches(1.8), Inches(5.6), Inches(4.8))
tf9_l = c9_left.text_frame
tf9_l.word_wrap = True
tf9_l.margin_left = tf9_l.margin_right = tf9_l.margin_top = Inches(0.3)

p_huge = tf9_l.paragraphs[0]
p_huge.text = "86%"
p_huge.font.size = Pt(44)
p_huge.font.bold = True
p_huge.font.color.rgb = GREEN

p_sub = tf9_l.add_paragraph()
p_sub.text = "TOKEN BURN REDUCTION (METERLESS)"
p_sub.font.size = Pt(13)
p_sub.font.bold = True
p_sub.font.color.rgb = TEXT_TITLE

m_points = [
    "Markovian memory cuts 185k tokens to 26k over 10 turns.",
    "Enforces strict subscription quotas ($29 to $499/mo).",
    "Prevents viral comment spikes from exhausting API budgets."
]
for item in m_points:
    p = tf9_l.add_paragraph()
    p.text = "\n• " + item
    p.font.size = Pt(12)
    p.font.color.rgb = TEXT_BODY

c9_right = add_card(s9, Inches(6.8), Inches(1.8), Inches(5.6), Inches(4.8))
tf9_r = c9_right.text_frame
tf9_r.word_wrap = True
tf9_r.margin_left = tf9_r.margin_right = tf9_r.margin_top = Inches(0.3)

p_huge2 = tf9_r.paragraphs[0]
p_huge2.text = "100%"
p_huge2.font.size = Pt(44)
p_huge2.font.bold = True
p_huge2.font.color.rgb = CYAN

p_sub2 = tf9_r.add_paragraph()
p_sub2.text = "SAFETY & POLICY AUDIT (NVIDIA NeMo)"
p_sub2.font.size = Pt(13)
p_sub2.font.bold = True
p_sub2.font.color.rgb = TEXT_TITLE

n_points = [
    "Evaluates every candidate message in <15ms.",
    "0.00% prompt injection and jailbreak risk.",
    "Strict price-floor protection prevents unauthorized discounts."
]
for item in n_points:
    p = tf9_r.add_paragraph()
    p.text = "\n• " + item
    p.font.size = Pt(12)
    p.font.color.rgb = TEXT_BODY

# ==========================================
# SLIDE 10: SCORECARD & ROADMAP
# ==========================================
s10 = prs.slides.add_slide(blank)
set_bg(s10)
add_header(s10, "Hackathon Scorecard", "Open Agent Hackathon 2026 Evaluation Criteria")

checks = [
    ("Impact (30 pts)", "Solves 60% lead abandonment & high VA overhead for real African SMEs."),
    ("Technical (20 pts)", "5-node LangGraph state machine, async FastAPI, and zero-leakage PostgreSQL RLS."),
    ("Innovation (15 pts)", "Public-to-private triage converting YouTube/IG comments to 1-click WhatsApp."),
    ("Demo (15 pts)", "Live, non-hardcoded multi-branch stock resolution and automated meeting scheduling."),
    ("Product & UX (10 pts)", "Dual-portal Next.js 16 app with real-time reasoning telemetry and live inbox."),
    ("Sponsor Tech (10 pts)", "Deep working integration of Zetaris USL, Meterless governance, and NVIDIA NeMo.")
]

for idx, (crit, desc) in enumerate(checks):
    left = Inches(0.8 + (idx % 2) * 6.0)
    top = Inches(2.0 + (idx // 2) * 1.6)
    card = add_card(s10, left, top, Inches(5.7), Inches(1.4))
    tf = card.text_frame
    tf.word_wrap = True
    tf.margin_top = Inches(0.15)
    tf.margin_left = tf.margin_right = Inches(0.25)
    
    p = tf.paragraphs[0]
    p.text = "✅ " + crit
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = GREEN
    
    p2 = tf.add_paragraph()
    p2.text = desc
    p2.font.size = Pt(12)
    p2.font.color.rgb = TEXT_BODY

prs.save("ReplyFlow_Pitch_Deck_Visual.pptx")
print("Visual pitch deck created successfully: ReplyFlow_Pitch_Deck_Visual.pptx")