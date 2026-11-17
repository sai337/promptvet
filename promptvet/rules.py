"""Default rule set. Pure data so teams can override it with a YAML/JSON file.

Severity drives the tier:
  high   -> BLOCKED  (never import into a company library)
  medium -> REVIEW   (a human approves it first)
  low    -> note only (small score penalty)
"""

RISK_RULES = [
    # --- Guardrail bypass / jailbreak -------------------------------------------------
    {"id": "JB001", "context_downgrade": True, "category": "jailbreak", "severity": "high",
     "pattern": r"\bignore (all |any )?(of )?(the |your )?(previous|prior|above|earlier) (instructions|rules|prompts|guidelines)",
     "message": "Tells the model to ignore its earlier instructions."},
    {"id": "JB002", "context_downgrade": True, "category": "jailbreak", "severity": "high",
     "pattern": r"\b(DAN|do anything now|STAN|DUDE|AIM)\b(?=[^.]{0,80}\b(mode|persona|jailbreak|unrestricted|no restrictions|any ?thing)\b)|\bdo anything now\b",
     "message": "Known jailbreak persona (DAN-style)."},
    {"id": "JB003", "context_downgrade": True, "category": "jailbreak", "severity": "high",
     "pattern": r"\b(without|free (of|from)|no) (any )?((ethical|moral|content|safety) (restrictions|filters|guidelines|limitations)|censorship|restrictions or (filters|limits|rules))\b",
     "message": "Asks for output with no safety restrictions."},
    {"id": "JB004", "context_downgrade": True, "category": "jailbreak", "severity": "high",
     "pattern": r"\b(bypass|circumvent|evade|disable)\b[^.]{0,40}\b(content (policy|filter)|safety|guardrails?|moderation|openai polic(y|ies))\b",
     "message": "Asks to bypass content policy or guardrails."},
    {"id": "JB005", "context_downgrade": True, "category": "jailbreak", "severity": "high",
     "pattern": r"\b(developer mode|unfiltered mode|evil (mode|confidant|assistant))\b|\bnot bound by\b[^.]{0,40}\b(rules|polic(y|ies)|guidelines)\b|\bnever refuse\b",
     "message": "Unrestricted-mode persona."},
    {"id": "JB006", "context_downgrade": True, "category": "jailbreak", "severity": "medium",
     "pattern": r"\b(uncensored|unrestricted|amoral)\b",
     "message": "Uses uncensored/unrestricted framing."},

    {"id": "JB007", "category": "jailbreak", "severity": "medium", "context_downgrade": True,
     "pattern": r"\bjailbreak(s|ing|ed)?\b(?! attempt)",
     "message": "Mentions jailbreaking (could be a jailbreak generator)."},

    # --- Prompt injection / exfiltration ----------------------------------------------
    {"id": "INJ001", "context_downgrade": True, "category": "injection", "severity": "high",
     "pattern": r"\b(reveal|print|show|repeat|output|leak)\b[^.]{0,30}\b(your |the )?(system prompt|hidden instructions|initial instructions|internal instructions)\b",
     "message": "Tries to extract a system prompt."},
    {"id": "INJ002", "category": "injection", "severity": "high",
     "pattern": r"!\[[^\]]*\]\(https?://[^)]*(\{|\$\{|%7B)[^)]*\)",
     "message": "Markdown image URL with a template slot (data exfiltration pattern)."},
    {"id": "INJ003", "category": "injection", "severity": "medium",
     "pattern": r"\b(send|post|upload|forward|transmit)\b[^.]{0,60}\bto\b[^.]{0,20}https?://",
     "message": "Instructs the model to send data to an external URL."},
    {"id": "INJ004", "category": "injection", "severity": "low",
     "pattern": r"https?://(?!(www\.)?(github\.com|wikipedia\.org|example\.com|prompts\.chat))[\w.-]+\.[a-z]{2,}",
     "message": "References an external URL."},

    # --- Secrets ------------------------------------------------------------------------
    {"id": "SEC001", "category": "secret", "severity": "high",
     "pattern": r"\b(AKIA|ASIA)[0-9A-Z]{16}\b", "message": "Looks like an AWS access key."},
    {"id": "SEC002", "category": "secret", "severity": "high",
     "pattern": r"\b(sk-(proj-|ant-)?[A-Za-z0-9_-]{24,}|ghp_[A-Za-z0-9]{30,}|xox[bpa]-[A-Za-z0-9-]{20,}|AIza[0-9A-Za-z_-]{35})\b",
     "message": "Looks like an API token."},
    {"id": "SEC003", "category": "secret", "severity": "high",
     "pattern": r"-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----", "message": "Embedded private key."},

    # --- Personal data ------------------------------------------------------------------
    {"id": "PII001", "category": "pii", "severity": "low",
     "pattern": r"\b[A-Za-z0-9._%+-]+@(?!example\.(com|org))[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
     "message": "Contains an email address."},
    {"id": "PII002", "category": "pii", "severity": "medium",
     "pattern": r"\b\d{3}-\d{2}-\d{4}\b", "message": "Looks like a US SSN."},

    # --- High-stakes advice personas -----------------------------------------------------
    {"id": "HS001", "category": "high_stakes", "severity": "medium",
     "pattern": r"\b(act|behave|serve|work|role-?play) as (a |an |my )?(\w+ )?(doctor|physician|surgeon|dentist|lawyer|attorney|legal advisor|financial advisor|investment advisor|stock ?broker|therapist|psychologist|psychiatrist|pharmacist|mental health counsel(l)?or)\b",
     "message": "Professional-advice persona (medical, legal, financial or mental health).",
     "unless": r"(not a substitute|consult (a|with a|your) (licensed |qualified )?(professional|doctor|lawyer|advisor)|for (informational|educational) purposes|disclaimer)"},

    # --- Deception / impersonation ------------------------------------------------------
    {"id": "DEC001", "category": "deception", "severity": "medium",
     "pattern": r"\b(never|do not|don't) (reveal|admit|mention|say) (that )?you are (an? )?(ai|bot|language model|chatbot)\b|\bpretend (to be|you are) (a )?(real )?human\b",
     "message": "Tells the model to hide that it is an AI."},

    # --- Offensive security -------------------------------------------------------------
    {"id": "SEC100", "context_downgrade": True, "category": "offensive_security", "severity": "medium",
     "pattern": r"\b(write|create|build|develop|generate)\b[^.]{0,40}\b(malware|ransomware|keylogger|botnet|phishing (email|page|site)|credential stealer|exploit code)\b",
     "message": "Asks to produce offensive-security tooling."},

    # --- Adult content ------------------------------------------------------------------
    {"id": "NSFW001", "context_downgrade": True, "category": "adult", "severity": "high",
     "pattern": r"\b(nsfw|explicit sexual|erotic(a)?|porn(ographic)?|sexually explicit)\b",
     "message": "Adult or sexually explicit content."},

    # --- Destructive tool use -----------------------------------------------------------
    {"id": "TOOL001", "context_downgrade": True, "category": "destructive_action", "severity": "medium",
     "pattern": r"\brm -rf (/|~)(\s|$|\*)|\bdrop (table|database)\b|\bformat (the )?(c:|disk|drive)\b|\bexecute any (command|code)\b",
     "message": "Destructive command or unrestricted execution."},
]

# Quality signals: (id, weight, pattern, label)
QUALITY_SIGNALS = [
    ("role", 15, r"\b(act as|you are (a|an|my)|i want you to act|imagine you are|behave as|your role is)\b", "Defines a role"),
    ("task", 15, r"\b(write|create|generate|analy[sz]e|review|explain|summari[sz]e|translate|design|plan|draft|help me|suggest|evaluate|build|provide|list|convert|identify|answer)\b", "States a clear task"),
    ("format", 15, r"\b(format|table|json|markdown|bullet|numbered|list|code block|template|sections?|headings?|step[- ]by[- ]step|word count|\d+ words|interface|layout|html|css|component|endpoint|schema)\b", "Specifies the output format"),
    ("constraints", 15, r"\b(do not|don't|only|must|should not|avoid|no more than|at most|at least|limit|never|always|ensure|make sure|requirements?|include)\b", "Sets constraints"),
    ("inputs", 10, r"(\$\{[^}]+\}|\{\{[^}]+\}\}|\[[A-Z][A-Za-z _-]{2,30}\]|<[a-z_ ]{3,30}>|my first (request|command|sentence|question|suggestion) is)", "Has input slots"),
    ("examples", 10, r"\b(for example|e\.g\.|example:|such as|for instance|sample)\b", "Gives examples"),
]

CATEGORIES = {
    "coding": r"\b(code|developer|programm|javascript|python|sql|api|debug|software|function|regex|git|typescript|react)\w*",
    "devops_sre": r"\b(devops|kubernetes|docker|terraform|cloud|aws|incident|sre|linux|infrastructure|monitoring|ci/cd|deployment)\w*",
    "data_ai": r"\b(data|machine learning|ml|statistic|dataset|analytics|llm|prompt engineer|model)\w*",
    "writing": r"\b(write|writer|story|essay|poem|novel|blog|article|copy|editor|proofread)\w*",
    "marketing": r"\b(marketing|seo|brand|advertis|social media|campaign|sales|copywrit|newsletter)\w*",
    "business": r"\b(business|startup|strategy|product manager|project|consult|recruit|interview|resume|career|hr)\w*",
    "education": r"\b(teach|tutor|student|learn|lesson|course|quiz|explain|teacher|exam)\w*",
    "design": r"\b(design|ui|ux|logo|figma|color palette|typography)\w*",
    "image_gen": r"\b(photo|portrait|selfie|lighting|camera|cinematic|midjourney|stable diffusion|dall-?e|image prompt|photograph|render|8k|cinematic)\w*",
    "health": r"\b(doctor|health|medical|fitness|diet|nutrition|therap|mental)\w*",
    "legal_finance": r"\b(lawyer|legal|contract|finance|invest|accountant|tax|stock)\w*",
    "entertainment": r"\b(game|play|character|movie|music|joke|fun|riddle|role ?play)\w*",
}

# Context that lowers a finding one level (high -> medium, medium -> low). It never clears it,
# so a prompt that quotes an attack in order to defend against it goes to human review, not a block.
DEFENSIVE_CONTEXT = (r"\b(detect\w*|flag\w*|block\w*|refus\w*|reject\w*|watch for|look for|patterns?|attempts?|e\.g\.|"
                     r"for example|such as|examples?|injection|attacks?|malicious|protect\w*|guard\w*|negative[_ ]prompts?|"
                     r"avoid|exclude|if (the )?(user|input|message|email|content|document)\w*)\b")
NEGATION_NEAR = r"\b(no|not|never|without|avoid|don't|do not|must not|nor|outweigh)\b"
SECRET_PLACEHOLDER = r"(example|0000|xxxx|your[_-]|dummy|fake|redacted|placeholder|not-real|abcdef|123456|wxyz)"
# Prompts whose job is to detect, review or moderate (judged from the title and opening).
DEFENSIVE_GENRE = r"\b(guardian|moderat\w*|classif\w*|detect\w*|evaluat\w*|audit\w*|lint\w*|review\w*|scanner|guardrails?|red[- ]team\w*|safety check\w*)\b"

# Visual (image/video generation) prompts are scored on a different rubric.
VISUAL_DETECT = r"\b(photo\w*|portrait|selfie|ultra-realistic|photorealistic|isometric|voxel|vertical orientation|still|wears|outfit|skin|hair|pose|background|lighting|camera|lens|\d+mm|aspect ratio|--ar|render\w*|cinematic|8k|4k|bokeh|composition|close-up|shot|illustration|midjourney|negative[_ ]prompt)\b"
VISUAL_SIGNALS = [
    ("subject", 20, r"\b(subject|person|woman|man|girl|boy|character|scene|product|portrait of|featuring)\b", "Names the subject"),
    ("style", 15, r"\b(style|aesthetic|cinematic|film|editorial|realistic|watercolor|anime|vintage|minimalist)\b", "Sets a style"),
    ("lighting", 15, r"\b(light\w*|shadow\w*|golden hour|backlit|glow\w*|contrast)\b", "Describes lighting"),
    ("camera", 15, r"\b(camera|lens|\d+mm|angle|shot|close-up|framing|aspect ratio|--ar|depth of field|composition)\b", "Gives camera/composition"),
    ("negative", 10, r"\b(negative[_ ]prompt|avoid|no text|no watermark|without (text|logos?))\b", "Has negative constraints"),
    ("detail", 5, r"\b(color|palette|texture|background|pose|expression|outfit|mood)\b", "Adds visual detail"),
]
