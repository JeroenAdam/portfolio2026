"""Build static data.json for the single-page React portfolio.

Extracts all content from the captured Gatsby page-data JSON files (which
contain the original Contentful data) and rewrites asset references so the
site works as a plain static folder. Run:  python build_data.py
"""
import json, os, re, shutil
from urllib.parse import unquote

REPO = r"C:\Users\Adam\projects\portfolio"
CAPTURED = os.path.join(os.path.dirname(os.path.abspath(__file__)), "captured")
OUT = os.path.dirname(os.path.abspath(__file__))

def load(fname):
    with open(os.path.join(CAPTURED, fname), encoding="utf-8") as f:
        return json.load(f)

# ---------------------------------------------------------------- helpers ---
def original_image(gatsby_image):
    """Extract the original Contentful URL from a gatsbyImage object."""
    try:
        src = gatsby_image["images"]["fallback"]["src"]
    except (KeyError, TypeError):
        return None
    m = re.search(r"[?&]u=([^&]+)", src)
    if not m:
        return None
    return unquote(m.group(1))

# asset refs like /rabat1.jpg -> images/rabat1.jpg (files get copied below)
copied_assets, missing_assets = set(), set()

def rewrite_content(text):
    """Rewrite markdown/HTML content: asset paths, internal links, decorations."""
    if not text:
        return text
    # Contentful text-decoration markers -> markdown bold
    text = text.replace("{b}", "**").replace("{/}", "**")
    # absolute internal links -> hash routes (keep trailing #fragment)
    text = re.sub(r"https://(www\.)?adambahri\.com/", "#/", text)

    def localize(path):
        """Map a root-relative /static path to images/<path>; track copies."""
        if path.startswith("http") or path.startswith("images/"):
            return path
        rel = path.lstrip("/")
        if os.path.isfile(os.path.join(REPO, "static", rel)):
            copied_assets.add(rel)
            return "images/" + rel
        missing_assets.add(rel)
        return path

    def fix_src(m):
        return 'src="' + localize(m.group(1)) + '"'

    def fix_url(m):
        return "url(" + m.group(1) + localize(m.group(2)) + m.group(1) + ")"

    text = re.sub(r'src="(/[^"]+)"', fix_src, text)
    text = re.sub(r"url\((['\"]?)(/[^)'\"\s]+)\1\)", fix_url, text)
    # markdown image/link to an image asset: ](/x.jpg)
    def fix_md_asset(m):
        rel = m.group(1).lstrip("/")
        if os.path.isfile(os.path.join(REPO, "static", rel)):
            copied_assets.add(rel)
            return "](images/" + rel + ")"
        missing_assets.add(rel)
        return m.group(0)

    text = re.sub(r'\]\((/[^)\s]+\.(?:jpg|jpeg|png|gif|webp|avif))\)', fix_md_asset, text)
    return text

def as_list(value):
    """Contentful string-array fields may arrive as list or single string."""
    if value is None:
        return []
    if isinstance(value, list):
        return [v for v in value]
    return [value]

# ------------------------------------------------------------------- jobs ---
jobs_raw = load("sq_1706634930.json")["data"]["allContentfulJobs"]["nodes"]
jobs = [{
    "company": j["company"],
    "position": j["position"],
    "date": j["date"],
    "desc": [rewrite_content(d) for d in as_list(j["desc"])],
} for j in jobs_raw]

# --------------------------------------------------------------- projects ---
projects_raw = load("pd_projects.json")["result"]["data"]["projects"]["nodes"]
projects = []
for p in projects_raw:
    stack = p.get("stack") or []
    if isinstance(stack, str):
        stack = [stack]
    projects.append({
        "title": p["title"],
        "featured": bool(p.get("featured")),
        "status": p.get("status") or "",
        "descriptionHtml": rewrite_content((p.get("description") or {}).get("childMarkdownRemark", {}).get("html", "")),
        "github": p.get("github") or "",
        "url": p.get("url") or "",
        "stack": stack,
        "image": original_image(p["image"]["gatsbyImage"]) if p.get("image") else None,
    })

# ------------------------------------------------------------------ blogs ---
blogs_raw = load("pd_blog.json")["result"]["data"]["allContentfulBlog"]["nodes"]
blogs = [{
    "id": b["id"],
    "slug": b["slug"],
    "title": b["title"],
    "desc": b.get("desc") or "",
    "created": b.get("created") or "",
    "category": [c for c in as_list(b.get("category"))],
    "image": original_image(b["image"]["gatsbyImage"]) if b.get("image") else None,
    "content": rewrite_content(b["content"]["content"]),
} for b in blogs_raw]

# ------------------------------------------------------------------ about ---
about_raw = load("pd_about.json")["result"]["data"]["about"]["nodes"][0]
about = {
    "title": about_raw["title"],
    "infoHtml": rewrite_content(about_raw["info"]["childMarkdownRemark"]["html"]),
    "stack": as_list(about_raw.get("stack")),
    "image": original_image(about_raw["image"]["gatsbyImage"]) if about_raw.get("image") else None,
    "toolset": [
        ["mysql.svg", "MySQL"], ["windows.svg", "Windows Server"], ["microsoft.svg", "Hyper-V"],
        ["docker.svg", "Docker"], ["powershell.svg", "Bash/Powershell"], ["linux.svg", "Linux"],
        ["apache.svg", "Apache"], ["icloud.svg", "Cloud infrastructure"], ["git.svg", "Git"],
        ["server.svg", "Tomcat"], ["apachemaven.svg", "Maven"], ["java.svg", "Java"],
        ["spring.svg", "Spring"], ["opencode.svg", "OpenCode"], ["visualstudiocode.svg", "VS Code"],
        ["googlechrome.svg", "Chrome DevTools"], ["selenium.svg", "Selenium"], ["postman.svg", "Postman"],
        ["jenkins.svg", "Jenkins"], ["userauthentication.svg", "Keycloak"],
        ["elasticsearch.svg", "Elasticsearch"], ["node-red.svg", "Node-RED"], ["rocketchat.svg", "RocketChat"],
        ["jira.svg", "JIRA"], ["openapiinitiative.svg", "Swagger"],
    ],
    "sideProjects": [
        "**Web development:** Java / Spring / React \u2014 I'm developing [#web applications](#/projects) for knowledge workers, for educators, for entrepreneurs.",
        "**IT infrastructure:** local LLM / AWS / Hyper-V / Linux / Docker / Networking",
    ],
}

# ----------------------------------------------------------------- myboat ---
myboat_raw = load("pd_myboat.json")["result"]["data"]["myboat"]["nodes"][0]
myboat = {
    "title": myboat_raw["title"],
    "infoHtml": rewrite_content(myboat_raw["info"]["childMarkdownRemark"]["html"]),
    "image": original_image(myboat_raw["image"]["gatsbyImage"]) if myboat_raw.get("image") else None,
}

# ---------------------------------------------------------------- voyages ---
voyages = {
    "intro": ("During the summer of 2012 I departed from Belgium. I experienced some fantastic sailing "
              "in France, Spain and Portugal. Two months later, I arrived in Morocco. I'm now living with "
              "my wife and children, two steps away from the Moroccan capital, in Sal\u00e9."),
    "slides": [
        ["marinasalex.jpg", "I sailed from Belgium to Morocco and started a new life in Morocco."],
        ["sale-marina.jpg", "I'm now berthed two steps away from the Moroccan capital city, in Sal\u00e9."],
        ["kenitrax.jpg", "North of my current position I have been navigating upriver to the city of Kenitra."],
        ["dakhla-mouillagex.jpg", "South of my current position awaits an amazing surrounding.... Dakhla. When? Allahu a3lam."],
        ["moroccox.jpg", "A past holiday: North-Morocco and Spain."],
        ["gibraltarx.jpg", "I rented a berth right next to Jebel Tariq (Gibraltar)."],
        ["tangerportx.jpg", "One year later, I toured in North-Morocco (Tanger)."],
        ["smir2.jpg", "And navigated further to Marina Smir."],
        ["albughaz2017x.jpg", "Last summer, North-Morocco again (Smir)..."],
        ["tanger2017x.jpg", "This time with both children (Tanger)."],
        ["sailing03x.jpg", "This is an experience I cannot describe in a few words..."],
        ["ciesx.jpg", "At times you reach places where no car can come (Cies)."],
        ["biscayx.jpg", "But sometimes the sea gets rough (Biscay)."],
        ["algarvex.jpg", "At other times there is no better place to be (Algarve)."],
        ["maintenancex.jpg", "And sometimes the boat keeps you busy with... maintenance."],
        ["rabatx.jpg", "I'm now living aboard with my family..."],
        ["lifeaboard4x.jpg", "As we have been living for the past 7 years."],
        ["lifeaboard9x.jpg", "\u201cI don't know much about the sea yet, but I like being out there.\u201d"],
    ],
}

# ------------------------------------------------------------- static bits --
data = {
    "_comment": "Static content for the single-page portfolio. Edit freely; the app fetches this file.",
    "site": {
        "title": "Jeroen Adam | IT Generalist, Web Developer",
        "description": "Personal portfolio of Jeroen Adam: IT generalist, web developer, author of Talim.app.",
    },
    "profile": {
        "name": "Jeroen Adam",
        "greetingArabic": "\u0627\u0644\u0633\u0644\u0627\u0645 \u0639\u0644\u064a\u0643\u0645",
        "headline": "IT Generalist | Web Developer",
        "authorOf": "author of Talim.app",
        "talimUrl": "https://talim.app",
        "note": "(and working remotely aboard my sailboat)",
        "heroImage": "images/hero-img.avif",
        "heroImageFallback": "images/hero-img.png",
        "email": "info@adambahri.com",
        "formAction": "https://formspree.io/meqpjjrr",
        "social": [
            {"id": "linkedin", "label": "Linkedin account", "icon": "fa-brands fa-linkedin", "url": "https://www.linkedin.com/in/jeroen-devenijn/"},
            {"id": "github", "label": "Github profile", "icon": "fa-brands fa-github", "url": "https://github.com/JeroenAdam"},
            {"id": "dev", "label": "Dev.to website", "icon": "fa-brands fa-dev", "url": "https://dev.to/jeroenadam"},
        ],
    },
    "navigation": [
        {"id": 1, "text": "home", "url": "#/", "icon": "fa-solid fa-house"},
        {"id": 2, "text": "about", "url": "#/about", "icon": "fa-solid fa-user"},
        {"id": 3, "text": "projects", "url": "#/projects", "icon": "fa-solid fa-briefcase"},
        {"id": 4, "text": "my voyages", "url": "#/myvoyages", "icon": "fa-solid fa-compass"},
        {"id": 5, "text": "blog", "url": "#/blog", "icon": "fa-solid fa-newspaper"},
        {"id": 6, "text": "my boat", "url": "#/myboat", "icon": "fa-solid fa-anchor"},
        {"id": 7, "text": "contact", "url": "#/contact", "icon": "fa-solid fa-envelope"},
    ],
    "services": [
        {"id": 1, "icon": "fa-solid fa-screwdriver-wrench", "title": "IT / APPLICATION SUPPORT",
         "text": "(8y.) Handling a business-critical app (+500 users), former service desk tech lead (5y.)."},
        {"id": 2, "icon": "fa-solid fa-server", "title": "DEVOPS / CLOUD",
         "text": "Infra/server mgmt., scripting, low-code, API integration, CI/CD, ChatOps, MLOps."},
        {"id": 3, "icon": "fa-solid fa-database", "title": "DATABASES",
         "text": "Handling SQL databases on a daily basis, building queries, backup/restore tasks."},
        {"id": 4, "icon": "fa-solid fa-code", "title": "PROGRAMMING / TESTING",
         "text": "Java / Spring / JavaScript / React / Node.js. Test automation, manual testing."},
        {"id": 5, "icon": "fa-solid fa-mug-hot", "title": "WEB DEVELOPMENT",
         "text": "Developing web applications, for knowledge workers, for educators, for entrepreneurs."},
        {"id": 6, "icon": "fa-solid fa-language", "title": "LANGUAGES / COMMUNICATION",
         "text": "Trilingual (nl/fr/en), good communicator, research minded, knowledge mgmt."},
    ],
    "jobs": jobs,
    "projects": projects,
    "blogs": blogs,
    "about": about,
    "myboat": myboat,
    "voyages": voyages,
}

# ------------------------------------------------------- write + copy files -
os.makedirs(OUT, exist_ok=True)
with open(os.path.join(OUT, "data.json"), "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

# validate round-trip
with open(os.path.join(OUT, "data.json"), encoding="utf-8") as f:
    check = json.load(f)
assert len(check["blogs"]) == len(blogs_raw)
assert sum(len(b["content"]) for b in check["blogs"]) == sum(len(b["content"]) for b in check["blogs"])
print(f"data.json written: {os.path.getsize(os.path.join(OUT, 'data.json')):,} bytes | "
      f"projects={len(projects)} blogs={len(blogs)} jobs={len(jobs)}")

# copy images used by the app
img_out = os.path.join(OUT, "images")
os.makedirs(os.path.join(img_out, "slides"), exist_ok=True)
shutil.copy(os.path.join(REPO, "src", "assets", "hero-img.avif"), img_out)
shutil.copy(os.path.join(REPO, "src", "assets", "hero-img.png"), img_out)
for fname, _cap in voyages["slides"]:
    shutil.copy(os.path.join(REPO, "src", "assets", "slides", fname), os.path.join(img_out, "slides"))
# contentful images referenced directly keep their URLs; copy local /static files referenced in content
for rel in sorted(copied_assets):
    dst = os.path.join(img_out, rel)
    os.makedirs(os.path.dirname(dst), exist_ok=True) if os.path.dirname(rel) else None
    shutil.copy(os.path.join(REPO, "static", rel), dst)
# svg tool icons + video demo
svg_out = os.path.join(OUT, "svg")
shutil.copytree(os.path.join(REPO, "static", "svg"), svg_out, dirs_exist_ok=True)
if os.path.isfile(os.path.join(REPO, "static", "custom-pmtool.mp4")):
    shutil.copy(os.path.join(REPO, "static", "custom-pmtool.mp4"), os.path.join(OUT, "custom-pmtool.mp4"))

print(f"copied {len(copied_assets)} static image(s) from blog/content references")
if missing_assets:
    print("MISSING (left untouched in content):", sorted(missing_assets))
