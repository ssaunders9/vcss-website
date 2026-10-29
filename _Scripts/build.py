#!/usr/bin/env python3
"""Build the VCSS static site skeleton into ../site/ from the PAGES definitions below.

Run:  /config/workspace/.venv/bin/python _Scripts/build.py   (from VCSS_Website/)
Edit content here (or in content.py later); never hand-edit site/*.html.
Placeholders: [TBD ...] and [VERIFY ...] are auto-highlighted.
"""
import re, shutil, csv, hashlib
VERSION = ""  # set in main() from the CSS hash so unchanged CSS keeps the same cache key
from pathlib import Path
from html import escape

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
ASSETS = ROOT / "Assets"

# ---------- helpers ----------
def mark(s):
    return re.sub(r"\[(TBD|VERIFY)([^\]]*)\]", lambda m: f'<mark class="{m.group(1).lower()}">[{m.group(1)}{m.group(2)}]</mark>', s)

def p(t): return f"<p>{t}</p>"
def ul(items): return "<ul>" + "".join(f"<li>{i}</li>" for i in items) + "</ul>"
def ol(items): return "<ol class='steps'>" + "".join(f"<li>{i}</li>" for i in items) + "</ol>"
def check(items): return "<ul class='checklist'>" + "".join(f"<li>{i}</li>" for i in items) + "</ul>"
def details(q, a): return f"<details><summary>{q}</summary><div>{a}</div></details>"
def faq(pairs): return "".join(details(q, p(a)) for q, a in pairs)
def btn(label, href="#", secondary=False): return f'<a class="btn{" btn-2" if secondary else ""}" href="{href}">{label}</a>'
def table(head, rows):
    h = "".join(f"<th>{c}</th>" for c in head)
    b = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows)
    return f'<div class="tablewrap"><table><thead><tr>{h}</tr></thead><tbody>{b}</tbody></table></div>'
def cards(items, img=None):
    """items: (title, text, href, button label)"""
    out = ['<div class="cards">']
    for t, x, href, lab in items:
        im = f'<img src="@@/img/{img}" alt="" loading="lazy">' if img else ""
        out.append(f'<article class="card">{im}<h3>{t}</h3><p>{x}</p>{btn(lab, href, True)}</article>')
    out.append("</div>")
    return "".join(out)
def program(title, who=None, get=None, apply=None, deadline=None, contact=None, button=None, img=None, alt=""):
    im = f'<img src="@@/img/{img}" alt="{escape(alt)}" loading="lazy">' if img else ""
    return (f'<article class="card program">{im}<h3>{title}</h3><dl><dt>Who it is for</dt><dd>{who}</dd><dt>What you get</dt><dd>{get}</dd>'
            f'<dt>How to apply</dt><dd>{apply}</dd><dt>Deadline</dt><dd>{deadline}</dd><dt>Contact</dt><dd>{contact}</dd></dl>{button or ""}</article>')
def person_grid(people):
    return '<div class="cards people">' + "".join(
        f'<article class="card person"><img src="@@/img/{img}" alt="{escape(name)}, {escape(role)}" loading="lazy"><h3>{name}</h3><p>{role}</p><p>{extra}</p></article>'
        for name, role, extra, img in people) + "</div>"
L = lambda u, t: f'<a href="{u}">{t}</a>'
PERSON = "person-placeholder.svg"

# ---------- global ----------
SITE_TITLE = "Voiland College Student Resources"
BYLINE = "Provided by the VCEA Student Success Team"
NAV = [("Academic Help", "academic-help"), ("First-Year & Transfer", "first-year-transfer"),
       ("Careers & Internships", "careers"), ("Paying for School", "paying-for-school"),
       ("Get Involved", "get-involved"), ("Wellness", "wellness"), ("About & Contact", "about")]
UTIL = [("Employers", "employers"), ("Faculty & Staff", "faculty-staff"), ("Club Advisors", "club-advisors"), ("Give", "give")]
FOOTER_QUICK = [("Find a Tutor", "academic-help/tutoring"), ("Book a Career Coach", "careers/coaching"),
                ("Join a Club", "get-involved/clubs"), ("Scholarships", "paying-for-school/scholarships"), ("Wellness Center", "wellness")]

def contact(name, role, email=None, phone=None, office=None):
    bits = [f"<strong>{name}</strong>"]
    if role: bits.append(role)
    if email: bits.append(f'<a href="mailto:{email}">{email}</a>')
    if phone: bits.append(f'<a href="tel:{re.sub(r"[^0-9+]", "", phone)}">{phone}</a>' if "TBD" not in phone else phone)
    if office: bits.append(office)
    return '<aside class="contact"><h2>Contact</h2><p>' + "<br>".join(bits) + "</p></aside>"

MAJORS = [
 ("Architecture", "https://sdc.wsu.edu/student-resources/", "https://sdc.wsu.edu/architecture/program-info/bs-in-architectural-studies/"),
 ("Bioengineering", "https://voiland.wsu.edu/undergraduate-advising/", "https://voiland.wsu.edu/schedules-of-study-2/"),
 ("Chemical Engineering", "https://voiland.wsu.edu/undergraduate-advising/", "https://voiland.wsu.edu/schedules-of-study/"),
 ("Civil Engineering", "https://ce.wsu.edu/advising/", "https://ce.wsu.edu/undergraduate/civil-engineering/"),
 ("Computer Engineering", "https://advise.eecs.wsu.edu/", "https://advise.eecs.wsu.edu/index.php/schedules-of-study/sheets/"),
 ("Computer Science", "https://advise.eecs.wsu.edu/", "https://advise.eecs.wsu.edu/index.php/schedules-of-study/sheets/"),
 ("Construction Management", "https://sdc.wsu.edu/student-resources/", "https://sdc.wsu.edu/construction-management/program-info/certification-requirements/"),
 ("Cybersecurity", "https://school.eecs.wsu.edu/undergraduate-advising/", "https://catalog.wsu.edu/General/Academics/DegreeProgram/10631"),
 ("Electrical Engineering", "https://advise.eecs.wsu.edu/", "https://advise.eecs.wsu.edu/index.php/schedules-of-study/sheets/"),
 ("Interior Design", "https://sdc.wsu.edu/student-resources/", "https://sdc.wsu.edu/interior-design/program-info/ba-in-interior-design/"),
 ("Landscape Architecture", "https://sdc.wsu.edu/student-resources/", "https://sdc.wsu.edu/landscape-architecture/program-info/bla/"),
 ("Materials Science and Engineering", "https://mme.wsu.edu/undergraduate/current-students/#ADV", "https://mme.wsu.edu/undergraduate/current-students/"),
 ("Mechanical Engineering", "https://mme.wsu.edu/undergraduate/current-students/#ADV", "https://mme.wsu.edu/undergraduate/current-students/"),
 ("Software Engineering", "https://advise.eecs.wsu.edu/", "https://school.eecs.wsu.edu/academics/undergraduate-program/software-engineering/requirements/"),
]
TUTORS = [("Aiden Vezzetti", "Computer Science", "aiden-vezzetti"), ("Annalee Nersten", "Computer Science", "annalee-nersten"), ("Atticus Prim", "Electrical Engineering", "atticus-prim"),
 ("Audrey Scott", "Civil Engineering", "audrey-scott"), ("Caleb Goin", "Mechanical Engineering", "caleb-goin"), ("Chloe Wallace", "Civil Engineering", "chloe-wallace"),
 ("Curtis Cummings", "Mechanical Engineering", "curtis-cummings"), ("Kobe Bui", "Mechanical Engineering", "kobe-bui"), ("Matt Jordan", "Architecture (M.Arch)", "matt-jordan"),
 ("Maura Castillo", "Chemical Engineering", "maura-castillo"), ("Samuel Faville", "Mechanical Engineering", "samuel-faville"), ("Savannah Frey", "Mechanical Engineering", "savannah-frey"),
 ("Timothy Le", "Computer Engineering", "timothy-le")]
COACH_BOOK = "https://outlook.office365.com/book/VoilandCollegeCareerServices@email.wsu.edu/"

# ---------- pages ----------
# slug, title, section(slug of parent nav item), dict(summary, button, where, body, contact, related, hero)
PAGES = {}
def page(slug, title, parent=None, summary="", button=None, where=None, body="", contact_card=None, related=None, hero=None, empty_note=None):
    PAGES[slug] = dict(title=title, parent=parent, summary=summary, button=button, where=where, body=body,
                       contact=contact_card, related=related or [], hero=hero)
def sec(h, content): return f"<section><h2>{h}</h2>{content}</section>"

# 0. Home is rendered separately (see render_home)

# 1. Academic Help
page("academic-help", "Academic Help", summary="Advising, tutoring, and mentoring to keep you on track.",
     body=cards([("Academic Advising", "Plan your degree with your assigned advisor.", "@@/academic-help/advising/", "Find my advisor"),
                 ("Tutoring", "Free drop-in peer tutoring in SEH 130.", "@@/academic-help/tutoring/", "See tutoring"),
                 ("Mentoring", "Connect with a peer or working engineer.", "@@/academic-help/mentoring/", "Explore mentoring")], "card-academic.svg")
     + sec("Other WSU academic support", ul([
         L("https://ascc.wsu.edu/channels/tutoring/", "Academic Success and Career Center") + ": peer-facilitated drop-in tutoring",
         L("https://www.math.wsu.edu/math-learning-center/", "Math Learning Center") + ": tutor-assisted study halls",
         L("https://writingprogram.wsu.edu/undergraduate-writing-center/", "Writing Center") + ": peer help with writing assignments",
         L("https://chem.wsu.edu/chemistry-learning-center/", "Chemistry Learning Center") + ": homework help and test prep",
         L("https://ascc.wsu.edu/resources/etutoring/", "eTutoring") + ": online help for undergraduates"])))

page("academic-help/advising", "Academic Advising", "academic-help",
     "Every VCEA student has an assigned advisor (assigned at New Coug Orientation) who helps you plan your degree and stay on track.",
     ("Find my advisor", "https://my.wsu.edu/"), None,
     sec("Who is my advisor?", p("Advisors are assigned at <a href=\"https://orientation.wsu.edu/\">New Coug Orientation</a>. In myWSU: open the Academic Advising tile, then Academic Progress, then My Academics. [VERIFY: current myWSU steps]"))
     + sec("Before your appointment", check(["Review your Academic Requirements report", "Bring your questions", "Check for holds"]))
     + sec("Reading your Academic Requirements report", ol(["Sign in to myWSU with your WSU Network ID", "Open the Academic Advising tile", "Choose Academic Progress in the left menu", "Open the My Academics tab to see your report"]))
     + sec("Requirements by major", table(["Major", "Advising", "Schedule of study"], [[m, f'<a href="{a}">Advising</a>', f'<a href="{r}">Requirements</a>'] for m, a, r in MAJORS])
           + p("<small>Many majors share one link on the current site (SDC, EECS, MME). Confirm each. Four SDC links are http://. Plan said 16 majors; the live site lists 14.</small>"))
     + sec("UCORE", p("UCORE requirements apply to every student regardless of major. " + L("https://ucore.wsu.edu/students/categories-and-courses/", "See categories and courses") + "."))
     + sec("Plan your classes", ul([L("https://schedules.wsu.edu/", "Schedule of Classes"), L("https://writingprogram.wsu.edu/uwpsubmission/", "Writing Portfolio information")]))
     + sec("Registration holds", p("Check myWSU for holds before you meet your advisor. They show in the gray box on the right side of your Student Center, and myWSU may call them “Service Indicators.” [VERIFY: current myWSU wording]")),
     contact("Kasey Schertenleib", "[TBD: role]", "kasey@wsu.edu", "[TBD]", "[TBD]"),
     [("Tutoring", "academic-help/tutoring"), ("New Student Checklist", "first-year-transfer/new-student-checklist")])

page("academic-help/tutoring", "Tutoring", "academic-help",
     "Free drop-in, one-on-one peer tutoring for VCEA courses. No appointment needed.",
     ("See today's tutors", "https://tutoring.wsu.edu/"), "Bowers Tutoring Center, Schweitzer Engineering Hall (SEH) 130, Monday to Friday, times vary by course (see tutor schedule), Closed when WSU is not holding classes.",
     sec("How it works", p("Walk in, no appointment. Tutors are trained Voiland College students who have already passed the course they tutor. Stop by early in the semester to see the space and the tutor schedules posted on the wall."))
     + sec("What to bring", ul(["Textbook and notes", "The assignment you are working on", "A scientific calculator", "Specific questions, so the tutor knows where you are stuck"]))
     + sec("Holiday schedule", p("Tutoring runs only on days WSU holds classes, so it is closed on holidays such as Presidents' Day."))
     + sec("Courses we cover", p("[TBD: list or link]"))
     + sec("Meet your tutors", person_grid([(n, m, "Courses: [TBD]", f"tutor-{k}.jpg") for n, m, k in TUTORS])
           + p("<small>Photos pulled from the current site; alt text now names each tutor. Bios intentionally not copied: write 2-line bios without “this year” wording. Matt Jordan is a graduate student, so say “peer tutors,” not “undergraduates.”</small>"))
     + sec("Become a tutor", p("[TBD: hiring info]"))
     + sec("More help across WSU", p("Also see " + L("https://ascc.wsu.edu/resources/etutoring/", "eTutoring") + ", the " + L("https://www.math.wsu.edu/math-learning-center/", "Math Learning Center") + ", the " + L("https://writingprogram.wsu.edu/undergraduate-writing-center/", "Writing Center") + " and the " + L("https://chem.wsu.edu/chemistry-learning-center/", "Chemistry Learning Center") + ".")),
     contact("Bowers Tutoring Center", "[VERIFY: live page lists only vcea.info@wsu.edu, not Lisa Hill]", "vcea.info@wsu.edu"),
     [("Academic Advising", "academic-help/advising"), ("Mentoring", "academic-help/mentoring")])

page("academic-help/mentoring", "Mentoring", "academic-help",
     "Get connected with a peer or a working engineer who has been where you are.", None, None,
     '<div class="cards">'
     + program("Voiland Peer Network", "First-year and transfer students", "An experienced undergraduate peer for guidance, resources, and practice with communication and leadership", "Use the Get started button", "[TBD]", "[TBD: contact]",
               btn("Get started", "https://vcea.wsu.edu/student-success/mentorship-programs/voiland-peer-network/"), "mentor-peer.jpg", "Illustration of a person helping another with map directions")
     + program("SWE Mentoring Program", "First-year engineering students", "A practicing woman engineer who stays in touch through college: email check-ins, meetups during breaks, job shadowing, facility tours, campus luncheons", "Email the program", "[TBD]",
               '<a href="mailto:wsu.swe.mentor@wsu.edu">wsu.swe.mentor@wsu.edu</a>', None, "mentor-swe.jpg", "Members of the Society of Women Engineers seated in front of a stone wall")
     + program("Boeing Mentorship Program", "Engineering students", "A Boeing mentor in your field, a virtual kickoff and networking, Boeing speaker events, and possibly a midyear group event", "Online application (hide button when closed)",
               "[TBD: 2026-27 dates; live page still shows Aug 29, 2025]",
               '<a href="mailto:vcea.internships@wsu.edu">vcea.internships@wsu.edu</a>, 509-335-8726 [VERIFY: live page links tel to 509-335-3740]', None, "mentor-boeing.jpg", "People walking past a wall with the Dreamliner and WSU Cougar logos")
     + "</div>")

# 2. First-Year & Transfer
page("first-year-transfer", "First-Year & Transfer", summary="Welcome to Voiland College. Start here.",
     body=p("[TBD: welcome message]") + cards([
         ("First-Year Program", "ENGR 101/102 and first-year support.", "@@/first-year-transfer/first-year-program/", "Learn more"),
         ("Transfer Students", "Credits, advising, and getting connected.", "@@/first-year-transfer/transfer-students/", "Learn more"),
         ("New Student Checklist", "Six things to do first.", "@@/first-year-transfer/new-student-checklist/", "Open checklist")], "card-firstyear.svg"))
page("first-year-transfer/first-year-program", "First-Year Program (ENGR 101/102)", "first-year-transfer",
     "What the ENGR 101/102 sequence is and why it matters. [TBD: course description, outcomes]", None, None,
     sec("What you'll do", p("[TBD]")) + sec("How it fits your major", p("[TBD]"))
     + sec("First-year support", ul(['<a href="@@/academic-help/tutoring/">Tutoring</a>', '<a href="@@/academic-help/mentoring/">Voiland Peer Network</a>', '<a href="@@/academic-help/advising/">Advising</a>'])),
     contact("[TBD: First-Year Programs lead]", None, "[TBD]", "[TBD]"))
page("first-year-transfer/transfer-students", "Transfer Students", "first-year-transfer", "Everything you need to land smoothly at Voiland College.", None, None,
     sec("Transferring credits and equivalencies", p("[TBD]")) + sec("Meet your advisor", p('<a href="@@/academic-help/advising/">Academic Advising</a>'))
     + sec("Peer Network for transfers", p('<a href="@@/academic-help/mentoring/">Voiland Peer Network</a>'))
     + sec("Getting involved quickly", ul(['<a href="@@/get-involved/clubs/">Clubs</a>', '<a href="@@/get-involved/maker-spaces/">FIZ</a>'])),
     contact("[TBD]", None, "[TBD]", "[TBD]"))
page("first-year-transfer/new-student-checklist", "New Student Checklist", "first-year-transfer", "Six steps for your first weeks.", None, None,
     ol(['<a href="@@/academic-help/advising/">Find your advisor</a>', '<a href="@@/academic-help/advising/">Check your Academic Requirements report</a>',
         '<a href="@@/academic-help/tutoring/">Bookmark tutoring hours</a>', '<a href="@@/get-involved/clubs/">Join a club</a> (club fair date [TBD])',
         '<a href="#">Create your Handshake profile</a>', '<a href="@@/wellness/">Visit the Wellness Center</a> and <a href="@@/get-involved/maker-spaces/">FIZ</a>']))

# 3. Careers
page("careers", "Careers & Internships", summary="Career coaching, internships, career fairs, and job search tools for Voiland College students.",
     button=("Book a career coach", COACH_BOOK),
     where="SEH Welcome Center, Room 102, 150 SE Spokane St. [VERIFY: Mentoring page still says Dana 140], Peer Career Guide drop-ins: Mon 2–3, Tue 12–1, Wed 3–4, Thu 12–1, Fri 2–3",
     body=p("<strong>Who we serve:</strong> In-person support for Pullman and Bremerton students; remote support for students at other WSU campuses.")
     + sec("What we do", ul(["Career coaching and mock interviews", "Technical career fairs and employer information sessions", "Networking events and industry tours", "Job postings and on-campus interviews", "The ProPEL internship credit program"]))
     + cards([("Career Coaching", "One-on-one coaching and mock interviews.", "@@/careers/coaching/", "Meet coaches"),
              ("Internships & ProPEL", "Earn credit for a paid internship.", "@@/careers/internships-propel/", "Learn more"),
              ("Career Fairs", "Dates, prep, and FAQs.", "@@/careers/career-fairs/", "See fairs"),
              ("Career Toolkit", "Résumés, interviews, job search.", "@@/careers/toolkit/", "Open toolkit"),
              ("Careers Blog", "Tips and news.", "@@/careers/blog/", "Read")], "card-careers.svg"),
     contact_card=contact("Lisa Hathaway", "Director, Career Services", "vcea.internships@wsu.edu", "509-335-8726"))
page("careers/coaching", "Career Coaching", "careers", "What a coaching session covers, and how to book one.", ("Book a coach", COACH_BOOK), "Drop-ins at SEH 102 (Peer Career Guides): Mon 2–3, Tue 12–1, Wed 3–4, Thu 12–1, Fri 2–3",
     sec("What a session covers", ul(["Clarifying your career goals", "Résumé, cover letter and LinkedIn review", "Finding internships and jobs", "Interview practice", "Planning your next step"]) + p("Book a time with the Director or a Peer Career Guide, or drop in at SEH 102 during guide hours."))
     + sec("Meet the coaches (single list, maintained here only)", person_grid([("Lisa Hathaway", "Director", btn("Book", "https://outlook.office.com/book/VoilandCollegeCareerServices@email.wsu.edu/s/z8HObUnNHUCdM4K38rPyAQ2", True), PERSON)] + [(n, f"Peer Career Guide, {m}", btn("Book", COACH_BOOK, True), PERSON) for n, m in [("Chance Shungu", "CS"), ("Samantha Klein", "CS"), ("Cheri Heng", "ME"), ("Gavin O’Connor", "EE")]]))
     + sec("Mock interviews", p("Practice with a coach before the real thing. Book a session above and mention the role you are interviewing for.")))
page("careers/internships-propel", "Internships & ProPEL", "careers", "ProPEL lets you earn credit (ENGR 488/489) for a paid internship or co-op.",
     ("Apply for ProPEL", "https://wsu.co1.qualtrics.com/jfe/form/SV_bQsYvv92hiP9Bxs"), None,
     sec("How it works", ol(["Get an offer. Pay is required, and you need a worksite mentor.", "Apply online as soon as you have the offer, and ask your employer to complete the " + L("https://wsu.co1.qualtrics.com/jfe/form/SV_0ibm16Vtjuxd8lU", "employer form") + ". Both forms are needed.", "Enroll in ENGR 488 (or your major's cross-listed 488) while you work, then ENGR 489 the semester after."]))
     + sec("Good to know", ul(["Placements run 12 weeks to 12 months, and many employers prefer six months or longer.", "You can stay a full-time WSU student while on a full-time internship.", "Talk to your advisor first about time to degree.", "How credit counts toward your major varies by department."]))
     + sec("Eligibility", check(["At least 420 hours (full time up to 12 months, or part time across terms)", "Paid (wage, stipend, or fellowship)", "A named mentor/supervisor at the worksite", "At least 50% related to your major", "On-site (virtual case by case)", "Enroll in ENGR 488 (2 cr) during the work term and ENGR 489 (1 cr) afterward"]))
     + sec("Credit and costs", p("Tuition applies like any course. Full-time work earns 2 credits of 488, part-time 1. Both 488 and 489 are needed for the tech/free elective. [VERIFY: live page contradicts itself on “one or two credit” and 30-hour thresholds]"))
     + sec("Financial aid note", p("Co-op income earned while enrolled in ProPEL has not counted against your aid calculation. [VERIFY: confirm wording against the current Student Aid Index rules with Financial Aid]"))
     + sec("FAQ", faq([("Do I need to take other classes?", "No. Other WSU courses are not required while you are in ProPEL."), ("Can I work part time?", "Yes. Part-time work can add up to 420 hours over several terms."), ("Can the internship be remote?", "Case by case. On-site is the default."), ("Do I pay tuition?", "Yes, ENGR 488 and 489 are regular courses.")]))
     + sec("Other experience options", ul([L("https://info.parkerdewey.com/vcea.wsu/students", "Parker Dewey micro-internships") + ": paid projects of 20 to 40 hours over 2 to 4 weeks, often remote, year-round", L("https://www.theforage.com/", "The Forage") + ": free job simulations that take about 5 to 6 hours and give you something to put on a résumé"])),
     related=[("Employers (host an intern)", "employers")])
page("careers/career-fairs", "Career Fairs", "careers", "Meet employers and practice getting hired.", None, None,
     sec("Upcoming fairs", p("No fairs listed yet. [TBD: spring 2027 dates. Fall 2026 fairs (Sept 9 Internship Pop-Up, CUB; Oct 6 Technical Fair, Beasley) are past, so auto-hide.]") + p("<small>Auto-hide past events; one registration link per fair.</small>"))
     + sec("WSU Career Expos and Virtual Expo", p("WSU Career Expos run each fall and spring through the " + L("https://ascc.wsu.edu/", "Academic Success and Career Center") + ". The Virtual Expo uses Handshake for group info sessions and one-on-one chats with recruiters. It is an introduction, not an interview. Next date: [TBD]."))
     + sec("Prepare in 5 steps", ol(["Update your résumé and get it reviewed in SEH 102", "Complete your Handshake profile", "Research the employers attending", "Practice a 30-second introduction", "Plan what to wear"]))
     + sec("FAQ", faq([("How often are fairs held?", "Career Expos run every fall and spring. [VERIFY: Voiland pages say both bi-annual and tri-annual]"), ("Who can attend?", "Every student, freshman through senior. Many employers hire interns, co-ops and full-time staff."), ("Why go?", "Employers see you, you hear about temporary and permanent roles, and you learn what to study next.")])))
page("careers/toolkit", "Career Toolkit", "careers", "Tools to get you from résumé to offer.", None, None,
     cards([("Résumés & Cover Letters", "Bullet formula, action verbs, tips.", "@@/careers/toolkit/resumes-cover-letters/", "Open"),
            ("Interviews & Offers", "Prepare, perform, negotiate.", "@@/careers/toolkit/interviews-offers/", "Open"),
            ("Job & Internship Search", "Tools grouped by purpose.", "@@/careers/toolkit/job-search/", "Open")]))
TK_BTN = '<p class="bottom-cta">' + btn("Book a coach", "#") + "</p>"
page("careers/toolkit/resumes-cover-letters", "Résumés & Cover Letters", "careers/toolkit", "Get started, then get a review.", None, None,
     check(["Pick a template", "Use the bullet formula", "Proofread (fix typos!)"])
     + details("Getting started", p("[TBD]")) + details("Bullet formula", p("[TBD]")) + details("Action verbs", p("[TBD: add the actual list]"))
     + details("Cover letter tips", p("[TBD]")) + details("Next step", p("Drop in for a review, then upload to Handshake.")) + TK_BTN)
page("careers/toolkit/interviews-offers", "Interviews & Offers", "careers/toolkit", "Target length about 800 words (cut from about 2,900).", None, None,
     check(["Know the interview type", "Prepare STAR stories", "Send a thank-you note"])
     + "".join(details(h, p("[TBD]")) for h in ["Types of interviews (replace Skype with video)", "Before, during, after", "STAR method", "What to wear",
                                                "Thank-you notes", "Negotiating salary (add salary sites; remove “$X to $X”)", "Accepting or declining an offer"])
     + '<p>' + btn("Schedule a mock interview", "#", True) + "</p>" + TK_BTN)
page("careers/toolkit/job-search", "Job & Internship Search", "careers/toolkit", "Tools in three buckets.", None, None,
     sec("Search", ul(["Handshake", L("https://voiland.careershift.com/", "CareerShift"), L("https://info.parkerdewey.com/vcea.wsu/students", "Parker Dewey"), L("https://www.theforage.com/", "The Forage"), "VCEA Jobs Board"]))
     + sec("Explore careers", ul(["Vault", "O*NET", "What Can I Do With This Major?", "CareerOneStop"]))
     + sec("Track and network", ul(["Job Search Tracker", "Email finders"])) + TK_BTN)
page("careers/blog", "Careers Blog", "careers", "Tips and news from Career Services.", None, None, p("[TBD: category feed from the existing blog]"))

# 4. Paying
page("paying-for-school", "Paying for School", summary="Scholarships and emergency aid.",
     body=cards([("Scholarships", "One application for most Voiland College scholarships.", "@@/paying-for-school/scholarships/", "Learn more"),
                 ("Emergency Aid", "Help when something unexpected happens.", "@@/paying-for-school/emergency-aid/", "Learn more")], "card-money.svg")
     + p('<a href="#">WSU Financial Aid</a>'))
page("paying-for-school/scholarships", "Scholarships", "paying-for-school",
     "One application (the WSU General Scholarship Application) puts you in the running for most Voiland College scholarships.",
     ("Apply at WSU Scholarships", "#"), "Priority deadline: January 31, [TBD: year]",
     sec("Featured scholarships", ul(["Distinguished Dean's Scholarship", "Dean's Scholarship", "WUEE Scholarship"]))
     + sec("School and department scholarships", p("[TBD: links]")) + sec("External opportunities", p("[TBD]")),
     contact("[TBD]", None, "[TBD]"))
page("paying-for-school/emergency-aid", "Emergency Aid", "paying-for-school", "[TBD: pending the VCEA emergency scholarship policy]", None, None,
     "".join(sec(h, p("[TBD]")) for h in ["Who is eligible", "What it covers", "How to request", "Response time", "Confidential contact"])
     + p('<a href="#">WSU-wide emergency resources</a>'))

# 5. Get Involved
page("get-involved", "Get Involved", summary="Clubs, making, entrepreneurship, and events.",
     body=cards([("Student Clubs", "40+ clubs.", "@@/get-involved/clubs/", "Browse"), ("Maker Spaces & FIZ", "Build something.", "@@/get-involved/maker-spaces/", "Explore"),
                 ("Entrepreneurship", "Frank Institute.", "@@/get-involved/entrepreneurship/", "Learn more"), ("Events", "What's coming up.", "@@/get-involved/events/", "See events"),
                 ("Student Spotlights", "Meet your peers.", "@@/get-involved/spotlights/", "Read")], "card-involved.svg"))
page("get-involved/clubs", "Student Clubs", "get-involved", "40+ Voiland College student clubs, from design teams to professional societies.", ("Browse clubs", "#directory"), None,
     '<section id="directory"><h2>Club directory</h2>' + p("[TBD: filterable list: name, type, major, contact]")
     + table(["Club", "Type", "Major", "Contact"], [["[TBD]", "[TBD]", "[TBD]", "[TBD]"]]) + "</section>"
     + sec("How to join", p("[TBD]")) + sec("Start a new club", p("[TBD]"))
     + p('Officers and advisors: <a href="@@/club-advisors/">Club Advisors &amp; Officers</a>'),
     contact("Club Hub", None, "vcea.studentclubs@wsu.edu", "509-335-6643", "SEH 202"))
MAKER = lambda n, loc: f'<article class="card"><h3>{n}</h3><dl><dt>What it is</dt><dd>[TBD]</dd><dt>Who can use it</dt><dd>[TBD]</dd><dt>Access / training</dt><dd>[TBD]</dd><dt>Hours</dt><dd>[TBD]</dd><dt>Location</dt><dd>{loc}</dd></dl>{btn("[TBD]", "#", True)}</article>'
page("get-involved/maker-spaces", "Maker Spaces & FIZ", "get-involved", "Spaces and tools to build your ideas.", None, None,
     '<div class="cards">' + MAKER("Frank Innovation Zone (FIZ)", "Dana Hall, ground floor") + MAKER("Fabrication Labs", "Next to Carpenter Hall") + MAKER("Voiland College Shops", "Dana Hall, ground floor") + "</div>",
     contact("Miles Pepper", None, "mpepper@wsu.edu", "509-335-8550", "Dana 46"))
page("get-involved/entrepreneurship", "Entrepreneurship", "get-involved", "Harold Frank Engineering Entrepreneurship Institute: competitions, funding, mentoring. [TBD]",
     ("Visit the Frank Institute", "#"), None, "", None)
page("get-involved/events", "Events", "get-involved", "Student events and signature events.", None, None,
     p("[TBD: auto-feed of student events; hide when empty]")
     + cards([("Ice Cream Socials", "[TBD: dates]", "#", "Details"), ("Senior Capstone Expo", "April 15, [TBD: year/location]", "#", "Details"),
              ("Engineering Innovation Expo", "[TBD: date]", "#", "Details"), ("Career Fairs", "Dates and prep.", "@@/careers/career-fairs/", "See fairs")]))
page("get-involved/spotlights", "Student Spotlights", "get-involved", "Stories from Voiland College students.", ("Nominate a student", "#"), None, p("[TBD: category feed]"))

# 6. Wellness
page("wellness", "Wellness", summary="A free space in Voiland College to relax, recharge, or talk with a trained peer supporter.",
     where="Daggy Hall [VERIFY: 101 vs. 130/133], Monday to Friday, 9 a.m. to 4 p.m., Closed weekends and holidays",
     body='<div class="crisis" role="note"><strong>In crisis?</strong> Call or text <a href="tel:988">988</a>, Emergencies <a href="tel:911">911</a>, After-hours counseling <a href="tel:5093352159">(509) 335-2159</a></div>'
     + sec("Wellness Rooms", ul(["Relaxation Room", "Art Room", "Game Room"])) + sec("How to use the center", p("[TBD: QR check-in steps]"))
     + sec("Peer support conversations", p("A conversation with a trained peer. It is not therapy. [TBD: keep current copy; fix “We are ran by students”]"))
     + sec("Become a peer supporter or practicum student", p("[TBD]")),
     contact_card='<aside class="contact"><h2>Contacts</h2><p><strong>Alena Hume</strong>, Director<br><a href="mailto:alena.hume@wsu.edu">alena.hume@wsu.edu</a><br>(509) 335-5376</p>'
                  '<p><strong>Ria Dominic</strong>, Graduate Assistant<br><a href="mailto:ria.dominic@wsu.edu">ria.dominic@wsu.edu</a></p></aside>')

# 7. About
page("about", "About & Contact", summary="Who we are and how to reach us.",
     body=cards([("Our Team", "Directory by area.", "@@/about/team/", "Meet the team"), ("Locations & Hours", "One table for every office.", "@@/about/locations/", "See locations")]))
AREAS = ["Recruiting", "First-Year Programs", "Advising", "Tutoring & Retention", "Career Services", "Clubs", "FIZ", "Wellness"]
page("about/team", "Our Team", "about", "[TBD: one-line mission]", None, None,
     sec("Leadership", person_grid([("Steve Saunders", "Associate Dean for Student Success", "[TBD: email, phone]", PERSON)]))
     + "".join(sec(a, person_grid([("[TBD: name]", "[TBD: role]", "[TBD: email, phone]", PERSON)])) for a in AREAS)
     + "<p><small>Static HTML so it renders without JavaScript.</small></p>")
page("about/locations", "Locations & Hours", "about", "The single source of truth for every office.", None, None,
     table(["Service", "Location", "Hours", "Email", "Phone"], [
         ["Main office", "[TBD]", "[TBD]", "vcea.info@wsu.edu", "509-335-5050"],
         ["Tutoring (Bowers Tutoring Center)", "SEH 130", "Mon–Fri, by course schedule", "vcea.info@wsu.edu", "509-335-5050"],
         ["Career Services", "SEH Welcome Center, Room 102", "Drop-ins listed on Careers page", "vcea.internships@wsu.edu", "509-335-8726"],
         ["Club Hub", "SEH 202", "[TBD]", "vcea.studentclubs@wsu.edu", "509-335-6643"],
         ["FIZ / Maker Spaces", "Dana Hall", "[TBD]", "mpepper@wsu.edu", "509-335-8550"],
         ["Wellness Center", "Daggy Hall 101", "M to F, 9 to 4", "alena.hume@wsu.edu", "509-335-5376"]])
     + sec("Map", '<div class="map-slot">[TBD: map embed]</div>') + sec("Mailing addresses", p("PO Box 642250, Pullman, WA 99164-2250. Career Services mailing: PO Box 642718, Pullman, WA 99164-2718. Club package address: [TBD]")))

# Secondary audiences
page("employers", "Employers", summary="Recruit Voiland College students.",
     body=ul(["Register for career fairs", "Post jobs (Handshake)", "Host a ProPEL intern (employer Qualtrics form)", "Professional Applicant Profile Portal", "Sponsor a club or Expo"]),
     contact_card=contact("Career Services", None, "vcea.internships@wsu.edu", "509-335-8726"))
page("faculty-staff", "Faculty & Staff", summary="Ways to connect your students with support.",
     body=sec("Refer a student (EARS)", p("Early Academic Referral System. What happens after a referral: [TBD]")) + sec("Request a classroom presentation", p("Career, wellness, tutoring. [TBD: form]"))
     + sec("Refer students to tutoring", p("[TBD]")) + sec("Capstone and Expo involvement", p("[TBD]")), contact_card=contact("[TBD]", None, "[TBD]"))
page("club-advisors", "Club Advisors & Officers", summary="Resources for running a Voiland College club.",
     body=sec("Club governance and home-unit model", p("[TBD]")) + sec("Club Safety Manual and liability forms", p("[TBD: when finalized]"))
     + sec("Purchasing process", p("[TBD]")) + sec("Funding and RSO status", p("[TBD]")) + sec("Mailing packages and correspondence addresses", p("[TBD]")),
     contact_card=contact("Club Hub", None, "vcea.studentclubs@wsu.edu"))
page("give", "Give", summary="Your gift supports clubs, the Expo, emergency aid, and Wellness.", button=("Give now", "#"),
     body=sec("Donor impact story", p("[TBD]")))


# ---------- content from the live-site capture (overrides earlier placeholders) ----------
import json
CLUBS = json.loads((Path(__file__).resolve().parent / "clubs.json").read_text())
def mail(a): return f'<a href="mailto:{a}">{a}</a>'
def tel(n): return f'<a href="tel:{re.sub(r"[^0-9+]", "", n)}">{n}</a>'

def club_table():
    rows = [[escape(c["name"]), mail(c["email"]) if c["email"] else "[TBD]", escape(c["adv"]) or "[TBD]"] for c in CLUBS]
    return ('<label class="sr" for="clubfilter">Filter clubs</label><input id="clubfilter" class="filter" type="search" placeholder="Filter clubs by name">'
            + table(["Club", "Contact", "Faculty advisor"], rows).replace("<table>", '<table id="clubs">')
            + '<script>(function(){var i=document.getElementById("clubfilter");if(!i)return;i.addEventListener("input",function(){var q=i.value.toLowerCase();'
              'document.querySelectorAll("#clubs tbody tr").forEach(function(r){r.hidden=r.textContent.toLowerCase().indexOf(q)<0;});});})();</script>')

page("get-involved/clubs", "Student Clubs", "get-involved", "More than 40 Voiland College clubs, from design teams to professional societies. All are open to any enrolled WSU student, with no experience needed.", ("Browse clubs", "#directory"), None,
     sec("Three ways to join", ol(["Email the club using the directory below.", "Search " + L("https://wsu.presence.io/", "WSU Presence") + " for club profiles and events. [VERIFY: link]", "Ask the Club Hub in SEH 202 or at " + mail("vcea.studentclubs@wsu.edu") + "."]))
     + '<section id="directory"><h2>Club directory</h2>' + club_table() + "<p><small>Student officer names are left out so the list does not go stale. Add them only if the clubs keep them current.</small></p></section>"
     + sec("Start a new club", p("[TBD: steps]. New clubs register as a WSU Registered Student Organization; see " + L("@@/club-advisors/", "Club Advisors & Officers") + ".")),
     contact("Gary Offerdahl", "Student Success Coordinator, Clubs and Events", "vcea.studentclubs@wsu.edu", "509-335-6643", "SEH 202A (Club Hub: SEH 202)"))

page("club-advisors", "Club Advisors & Officers", summary="Everything a club needs to register, fund itself, promote events, and get mail.",
     body=sec("Register or renew as an RSO", p("Voiland College clubs register or renew WSU Registered Student Organization status at the start of each fall semester. New clubs should register as soon as possible, because RSO training dates are limited. Not sure of your status? Email Student Engagement Services at " + mail("getinvolved@wsu.edu") + "."))
     + sec("Funding", p("Student Engagement Services runs the club funding opportunities. Purchase, food and travel requests go through the college's club purchasing system. [TBD: link and current steps]"))
     + sec("Promote your club", details("Digital signage on Voiland College monitors", ol(["Design the flyer at 16:9 (PowerPoint) proportions.", "Add a QR code to a page with dates and details, so one flyer works all term.", "Tell us the date to take it down.", "Say whether you want it printed for physical flyer boards (up to 20 prints per club)."]) + p("Email the flyer to " + mail("vcea.studentclubs@wsu.edu") + "."))
           + details("WSU marketing resources", p("RSOs can use WSU design and printing services. [TBD: link]")))
     + sec("Reserve a room", p("Book a WSU classroom for meetings and events. [TBD: link]"))
     + sec("Safety manual and liability forms", p("[TBD: when finalized]"))
     + sec("Mailing", p("<strong>Packages:</strong> “Club Name” c/o VCEA Club Hub, Washington State University, 100 Dairy Road, 202 SEH, Pullman, WA 99164-2718")
           + p("<strong>Correspondence:</strong> “Club Name” c/o VCEA Club Hub, Washington State University, PO Box 642718, Pullman, WA 99164-2718")),
     contact_card=contact("Club Hub", "Gary Offerdahl, Student Success Coordinator, Clubs and Events", "vcea.studentclubs@wsu.edu", "509-335-6643", "SEH 202"))

page("give", "Give", summary="Gifts support student clubs, the Expo, emergency aid, and Wellness.", button=("Give now", "#"),
     body=sec("Support a club", p("A gift can cover travel to a national competition or project materials. Choose a club on the giving site. [TBD: giving link]. To donate materials, equipment or services, contact Fernanda Amaral at " + mail("f.amaral@wsu.edu") + "."))
     + sec("Donor impact story", p("[TBD]")))

page("get-involved/maker-spaces", "Maker Spaces & FIZ", "get-involved", "Three places to build, with trained staff and real equipment.", None, None,
     '<div class="cards">'
     + f'<article class="card"><h3>Frank Innovation Zone (FIZ)</h3><dl><dt>What it is</dt><dd>A maker space with fabrication tools to bring ideas to life.</dd><dt>Who can use it</dt><dd>WSU students, faculty and staff</dd><dt>Access / training</dt><dd>[TBD]</dd><dt>Hours</dt><dd>[TBD]</dd><dt>Location</dt><dd>Dana Hall, ground floor</dd></dl>{btn("FIZ website", "#", True)}</article>'
     + f'<article class="card"><h3>Fabrication Labs</h3><dl><dt>What it is</dt><dd>About 3,500 square feet of maker space with digital fabrication run by trained shop technicians, plus a Model Shop with scale analog machines.</dd><dt>Who can use it</dt><dd>[TBD]</dd><dt>Access / training</dt><dd>[TBD]</dd><dt>Hours</dt><dd>[TBD]</dd><dt>Location</dt><dd>Next to Carpenter Hall</dd></dl>{btn("Fabrication Labs", "#", True)}</article>'
     + f'<article class="card"><h3>Voiland College Shops</h3><dl><dt>What it is</dt><dd>Shops that fabricate parts, tools and machines for research and competitions.</dd><dt>Who can use it</dt><dd>Faculty, graduate students and student clubs</dd><dt>Access / training</dt><dd>[TBD]</dd><dt>Hours</dt><dd>[TBD]</dd><dt>Location</dt><dd>Dana Hall, ground floor</dd></dl></article>'
     + "</div>",
     contact("Miles Pepper", "[VERIFY: the staff directory lists Maynard Siev as FIZ Manager, Dana Hall 15, maynard.siev@wsu.edu, 509-335-7229]", "mpepper@wsu.edu", "509-335-8550", "Dana 46"))

page("wellness", "Wellness", summary="A free space in Voiland College to relax, recharge, or talk with a trained peer supporter. It is not therapy or long-term counseling.",
     where="Daggy Hall 101, Monday to Friday, 9 a.m. to 4 p.m. Closed weekends, university holidays and closures. After hours, call (509) 335-2159 for Counseling and Psychological Services.",
     body='<div class="crisis" role="note"><strong>In crisis?</strong> Call or text <a href="tel:988">988</a>, call <a href="tel:911">911</a>, or go to your nearest emergency room. After-hours counseling: <a href="tel:5093352159">(509) 335-2159</a></div>'
     + sec("Wellness rooms", '<div class="cards">'
           '<article class="card"><h3>Relaxation Room</h3><p>A quiet room for mindfulness, with a massage chair, aromatherapy, relaxation sounds and soft lighting.</p></article>'
           '<article class="card"><h3>Art Room</h3><p>Drop in and make something. Art supplies are on hand to help you decompress.</p></article>'
           '<article class="card"><h3>Game Room</h3><p>The largest room, with LED lighting, a TV, floor gaming chairs, tables and a Wii for active games.</p></article></div>')
     + sec("How to use the center", ol(["Ask a Peer Supporter at the front desk which room is open.", "Check in with the QR code at the desk.", "Head to your room and settle in."]))
     + sec("Peer support conversations", p("Talk with a trained Peer Supporter or practicum student from psychology, human development and related fields. Good topics: exam or homework stress, time management, lack of sleep, life changes and basic needs.")
           + p("The center is a place to connect and de-stress. It does not replace counseling."))
     + sec("Become a peer supporter or practicum student", p("Psychology, social work and similar majors, or anyone who wants to support fellow Cougs, are welcome to apply. [TBD: how to apply]")),
     contact_card='<aside class="contact"><h2>Contacts</h2><p><strong>Alena Hume</strong>, Director<br>Daggy Hall 130<br><a href="mailto:alena.hume@wsu.edu">alena.hume@wsu.edu</a><br>(509) 335-5376</p>'
                  '<p><strong>Ria Dominic</strong>, Graduate Assistant<br>Daggy Hall 133<br><a href="mailto:ria.dominic@wsu.edu">ria.dominic@wsu.edu</a></p></aside>')

page("paying-for-school/scholarships", "Scholarships", "paying-for-school",
     "One application, the WSU General Scholarship Application, puts you in the running for the Distinguished Dean's, Dean's and WUEE scholarships.",
     ("Apply at WSU Scholarships", "#"), "Priority deadline: January 31 for the following academic year. [TBD: confirm year]",
     sec("Distinguished Dean's Scholarship", p("The college's top award: full tuition, renewable for up to four years. Finalists come from Dean's Scholarship applicants and are chosen for academic excellence, curiosity, leadership, and a clear sense of purpose."))
     + sec("Dean's Scholarship", p("More than 300 awarded each year to incoming first-year and transfer students. First-years are considered on high school GPA and test scores. Pullman transfer students need the calculus series and either the calculus-based physics or chemistry series, with a 3.4 GPA or higher. Apply early, since funds are limited."))
     + sec("WUEE Scholarship", p("Out-of-state engineering and computer science students at WSU Pullman can add $2,000 a year to their Dean's Scholarship for each year they qualify."))
     + sec("School and department scholarships", p("Open to students certified in a major. Dates and methods vary, so check with your school.") + ul(["Civil and Environmental Engineering", "Voiland School of Chemical Engineering and Bioengineering", "School of Design and Construction", "Electrical Engineering and Computer Science", "Mechanical and Materials Engineering"]))
     + sec("More opportunities", ul(["Air Force ROTC Scholarships", "LSAMP Research Scholarship", "Washington State Opportunity Scholarship", L("#", "WSU Scholarships")])),
     contact("[TBD: scholarship contact]", "The live page only says to contact your school or department", "[TBD]"))

page("get-involved/entrepreneurship", "Entrepreneurship", "get-involved", "The Harold Frank Engineering Entrepreneurship Institute brings engineering, business and communications students together to build technology ventures.",
     ("Visit the Frank Institute", "#"), None, p("[TBD: competitions, funding, mentoring details]"))

page("get-involved/spotlights", "Student Spotlights", "get-involved", "Stories from Voiland College students.", ("Nominate a student", "#"), None,
     ul(["Betty Mitchell, civil engineering", "Alex Brown, materials science", "Connor Reschke, civil engineering", "Lauren Hoyt, Wings Club Scholarship recipient", "Trinity Middleton, materials science and engineering", "Ashley McCoy, architectural studies", "David Montes-Vilanova, computer science", "Brian Romero Gomez, mechanical engineering", "Brandon Swinger, civil engineering"])
     + p("[TBD: link each name to its story and add photos]"))

page("faculty-staff", "Faculty & Staff", summary="Ways to connect your students with support.",
     body=sec("Refer a student (EARS)", p("Early Academic Referral System. What happens after a referral: [TBD]"))
     + sec("Invite Career Services to your class or club", p("Missing a class? Career Services can cover internships and how to find one, résumés and cover letters, interviewing, professional etiquette and networking. A visit can last from 5 minutes to a full hour (up to 50 minutes for clubs).") + p(btn("Request a presentation", "#"))
           + p("<small>Form fields: name, email, phone, class or group, topic, location, participants, date, time, length. [TBD: embed or link]</small>"))
     + sec("Refer students to tutoring", p("Send them to " + L("@@/academic-help/tutoring/", "Tutoring") + " in SEH 130."))
     + sec("Capstone and Expo involvement", p("[TBD]")), contact_card=contact("Student Success", None, "vcea.info@wsu.edu", "509-335-5050"))

page("employers", "Employers", summary="Recruit Voiland College students.", button=("Post jobs on Handshake", "https://wsu.joinhandshake.com/"),
     body=sec("Interview on campus or online", p("Career Services provides interview space on the Pullman campus. Schedule on-campus and virtual interviews through Handshake."))
     + sec("Host an event", p("Request an information session, pre-interview night, table in a high-traffic area, coffee chat, virtual tour or networking night through Handshake. For on-campus events the Employer Relations Team follows up on space and parking."))
     + sec("Recruit at college events", p("Career Expo each fall and spring, the Career Networking Mixer, and club-sponsored Evening with Industry events."))
     + sec("Host a ProPEL intern", p("Students earn credit for paid internships. Complete the " + L("https://wsu.co1.qualtrics.com/jfe/form/SV_0ibm16Vtjuxd8lU", "employer form") + " when a student asks.") )
     + sec("Volunteer", ul(["Workshop presentations", "Career and alumni panels", "Mock interviews and portfolio reviews", "Job shadowing", "Career Trek and industry tours for student groups"]))
     + sec("Professional Applicant Profile Portal", p("Browse approved student and alumni profiles. [TBD: link]"))
     + sec("Recruiting guidelines", p("Open and fair access for all undergraduate and graduate students. Recruiters follow the WSU Non-Discrimination Policy and NACE principles. [TBD: link]"))
     + sec("Sponsor a club or Expo", p("[TBD]")),
     contact_card=contact("Employer Relations Team", "Career Services", "vcea.internships@wsu.edu", "509-335-8726"))

ACTION_VERBS = ["Analyzed", "Assembled", "Built", "Calibrated", "Coordinated", "Designed", "Developed", "Directed", "Evaluated", "Fabricated", "Improved", "Installed", "Led", "Managed", "Modeled", "Organized", "Programmed", "Reduced", "Researched", "Supervised", "Tested", "Trained", "Wrote"]
page("careers/toolkit/resumes-cover-letters", "Résumés & Cover Letters", "careers/toolkit", "Build a résumé that fits the job, then get it reviewed.", None, None,
     check(["List education and experience that fits the job", "Start each bullet with an action verb and add a result", "Proofread, then ask someone else to proofread", "Drop in for a review, then upload to Handshake and set your profile to visible"])
     + details("Getting started", p("Write down a professional inventory of your projects, jobs, clubs and skills first. Build your own document instead of a template, because templates are hard to change when you add experience."))
     + details("The bullet formula", p("Action verb, plus what you did, plus the result.") + table(["Basic", "Stronger"], [["Assisted with inventory", "Assisted with weekly and monthly inventory of 500+ medical supplies"], ["Worked to revise website", "Reduced site load time by 5 seconds, increasing page traffic by 25 percent"]]))
     + details("Action verbs", p(", ".join(ACTION_VERBS) + "."))
     + details("Cover letters", ul(["Write it after your résumé and tailor it to each posting.", "Show how your experience solves the employer's problem.", "Use numbers, dollars or percentages.", "Use your own words and let your personality show.", "Use a clear font such as Times New Roman, Arial or Helvetica."]))
     + TK_BTN)

page("careers/toolkit/interviews-offers", "Interviews & Offers", "careers/toolkit", "From the first screen to the signed offer.", None, None,
     check(["Know the format", "Practice common questions", "Research the company", "Send a thank-you note"])
     + details("Types of interviews", ul(["Screening call, 30 to 45 minutes", "One-way recorded video", "Live video or phone: quiet place, charged device, résumé and notes in reach", "On-site: keep receipts if the company covers travel", "Panel or peer group: speak to everyone", "Over a meal: manners count", "Second interview: longer, more people"]))
     + details("Before", p("Read the job description and prepare an example for each requirement. Learn the organization's mission and recent news. Do a dry run of the route or the video link."))
     + details("During", p("Arrive about 15 minutes early. Be honest, emphasize the positive, and when asked about a weakness, name something you are improving. Ask about next steps and do not raise salary first."))
     + details("What to wear", p("Dress professionally. The Career Cougar Closet at the Academic Success and Career Center lends professional clothing."))
     + details("Thank-you notes", p("[TBD: short guidance]"))
     + details("Negotiating salary and benefits", p("[TBD: salary research sites]"))
     + details("Accepting or declining an offer", p("[TBD]"))
     + '<p>' + btn("Schedule a mock interview", COACH_BOOK, True) + "</p>" + TK_BTN)

page("careers/toolkit/job-search", "Job & Internship Search", "careers/toolkit", "Tools in three groups.", None, None,
     sec("Search", ul([L("https://wsu.joinhandshake.com/", "Handshake") + ": the main place for WSU internships, co-ops and jobs", L("https://voiland.careershift.com/", "CareerShift") + ": company research and contacts, plus email campaigns you can track",
                       "Job Search Tracker: a daily-updated spreadsheet by major, with a WSU login", L("https://info.parkerdewey.com/vcea.wsu/students", "Parker Dewey") + ": paid micro-internships", L("https://www.theforage.com/", "The Forage") + ": free job simulations",
                       "Company career pages", "LinkedIn Jobs and Internships", "Internships abroad", "Regional boards: Washington WorkSource, Idaho Works, state and federal government jobs, Aerospace Career Hub"]))
     + sec("Explore careers", ul(["Vault: employer rankings, company reviews and industry guides", "O*NET Interest Profiler (My Next Move): matches your interests to occupations", "What Can I Do With This Major?: careers by major (external site, majors may differ from WSU)", "CareerOneStop: U.S. Department of Labor tools for careers, training and jobs"]))
     + sec("Track and network", ul(["Job Search Tracker", "Email finders such as hunter.io and Anymail Finder for reaching alumni", "Professional Applicant Profile Portal for employers to find you"])) + TK_BTN)

page("careers/career-fairs", "Career Fairs", "careers", "Meet employers, practice your pitch, and find your next internship.", ("Register for the Career Expos", "https://ascc.wsu.edu/resources/wsu-career-expos/"), None,
     sec("Upcoming fairs", p("No fairs listed yet. [TBD: spring 2027 dates, one Handshake link per fair. Fall 2026 fairs, the Sept 9 Internship Pop-Up and the Oct 6 Technical Fair, are past.]"))
     + sec("What to expect", p("WSU Career Expos run every fall and spring through the Academic Success and Career Center, and Voiland College hosts a Technical Fair. The Virtual Expo runs on Handshake with group sessions and one-on-one chats with recruiters. It is an introduction, not an interview. Freshmen are welcome and encouraged to come."))
     + sec("Prepare in 5 steps", ol(["Update your résumé and get it reviewed in SEH 102", "Complete your Handshake profile", "Pick the employers you want to meet and read up on them", "Practice a 30-second introduction", "Plan your outfit"]))
     + sec("At the fair", ul(["Arrive early and start with shorter lines.", "Shake hands, introduce yourself and hand over your résumé.", "Ask about the application process and collect a contact name from everyone you meet.", "Be considerate of the students waiting behind you.", "Skip salary and benefits questions."]))
     + sec("Good questions to ask", ul(["What do you look for in candidates?", "What training is there for entry-level hires?", "What assignments would I get?", "What skills matter most for success here?"]))
     + sec("After the fair", p("Send a thank-you note with your résumé attached, keep researching the company, and book a mock interview."))
     + sec("FAQ", faq([("How often are fairs held?", "Every fall and spring. [VERIFY: Voiland pages say both bi-annual and tri-annual]"),
                       ("What should I wear?", "Professional clothing. The Career Cougar Closet at the Academic Success and Career Center can help."),
                       ("When can I register?", "Until the event starts on the day of the event."),
                       ("What browser works for the virtual fair?", "Chrome, with pop-ups allowed."),
                       ("What if audio or video fails?", "Get the recruiter's email so you can send your materials."),
                       ("Where do I get help at the in-person fair?", "Help booths on both floors of the venue. [VERIFY: current venue]")])),
     contact_card=contact("Career Services", None, "vcea.internships@wsu.edu", "509-335-8726", "SEH Welcome Center, Room 102"))

TEAM = [("Partha Pratim Pande", "Dean", "pande@wsu.edu<br>509-335-5593<br>SEH 230P"), ("Krishnamoorthy Sivakumar", "Associate Dean, Academic Affairs", "siva@wsu.edu<br>509-335-4969<br>SEH 230R"),
        ("Steve Saunders", "Associate Dean for Student Success", "[TBD: email, phone, office]")]
page("about/team", "Our Team", "about", "[TBD: one-line mission]", None, None,
     sec("Leadership", person_grid([(n, r, e, PERSON) for n, r, e in TEAM]))
     + sec("Recruiting", person_grid([("Lisa Carmack", "Student Success Coordinator, Future Cougs", "lisa.carmack@wsu.edu<br>509-335-4823<br>SEH 102A", PERSON)]))
     + sec("First-Year Programs", person_grid([("Kimberlee Hughes", "Instructor, First-Year Engineering", "kimberlee.hughes@wsu.edu<br>509-335-2888<br>SEH 126E", PERSON)]))
     + sec("Advising", person_grid([("Kasey Schertenleib", "Director, Advising and Enrollment Management", "kasey@wsu.edu<br>509-335-6613<br>SEH 126C", PERSON),
                                     ("Alena Hume", "Academic Advisor and Transfer Coordinator", "alena.hume@wsu.edu<br>509-335-5376<br>SEH 126A", PERSON),
                                     ("Brenda Schuster", "Academic Success Advisor", "brenda.schuster@wsu.edu<br>509-335-3060<br>SEH 124A", PERSON)]))
     + sec("Tutoring & Retention", p("[TBD: tutoring coordinator]"))
     + sec("Career Services", person_grid([("Lisa Hathaway", "Director of Internships and Career Services", "vcea.internships@wsu.edu<br>509-335-8726<br>SEH 126D [VERIFY: directory shows a different email address]", PERSON)]))
     + sec("Clubs and Events", person_grid([("Gary Offerdahl", "Student Success Coordinator, Clubs and Events", "gary.offerdahl@wsu.edu<br>509-335-6643<br>SEH 202A", PERSON)]))
     + sec("Frank Innovation Zone", person_grid([("Maynard Siev", "FIZ Manager", "maynard.siev@wsu.edu<br>509-335-7229<br>Dana Hall 15", PERSON)]))
     + sec("Wellness", person_grid([("Alena Hume", "Director, VCEA Wellness Center", "alena.hume@wsu.edu<br>(509) 335-5376<br>Daggy Hall 130", PERSON), ("Ria Dominic", "Graduate Assistant", "ria.dominic@wsu.edu<br>Daggy Hall 133", PERSON)]))
     + p("<small>Photos [TBD]. Alena Hume is listed as Advisor/Transfer Coordinator in the staff directory and as Wellness Center Director on the Wellness page; confirm both roles.</small>"))

PAGES["academic-help/advising"]["contact"] = contact("Kasey Schertenleib", "Director, Advising and Enrollment Management", "kasey@wsu.edu", "509-335-6613", "SEH 126C")
PAGES["first-year-transfer/first-year-program"]["contact"] = contact("Kimberlee Hughes", "Instructor, First-Year Engineering", "kimberlee.hughes@wsu.edu", "509-335-2888", "SEH 126E")
PAGES["first-year-transfer/transfer-students"]["contact"] = contact("Alena Hume", "Academic Advisor and Transfer Coordinator", "alena.hume@wsu.edu", "509-335-5376", "SEH 126A")
PAGES["careers"]["contact"] = contact("Lisa Hathaway", "Director, Internships and Career Services", "vcea.internships@wsu.edu", "509-335-8726", "SEH 126D; front desk SEH 102")


REDIRECTS = [("/advising/", "academic-help/advising"), ("/tutoring/", "academic-help/tutoring"), ("/tutoring/tutoring-schedule/", "academic-help/tutoring"),
 ("/tutoring/meet-your-tutors/", "academic-help/tutoring"), ("/mentorship-programs/", "academic-help/mentoring"), ("/internships-careers/", "careers"),
 ("/internships-careers/propel/", "careers/internships-propel"), ("/?page_id=254", "careers/internships-propel"),
 ("/internships-careers/career-fairs/", "careers/career-fairs"), ("/internships-careers/career-fairs/preparation/", "careers/career-fairs"),
 ("/internships-careers/career-fairs/faqs/", "careers/career-fairs"), ("/internships-careers/resumes-and-cover-letters/", "careers/toolkit/resumes-cover-letters"),
 ("/internships-careers/interview-prep/", "careers/toolkit/interviews-offers"), ("/internships-careers/job-search/", "careers/toolkit/job-search"),
 ("/internships-careers/resources/", "careers/toolkit"), ("/internships-careers/employer-information/", "employers"),
 ("/internships-careers/professional-applicant-profile-portal/", "employers"), ("/internships-careers/presentation-request/", "faculty-staff"),
 ("/scholarships/", "paying-for-school/scholarships"), ("/entrepreneurship/", "get-involved/entrepreneurship"), ("/club-hub/", "get-involved/clubs"),
 ("/club-hub/join-a-student-club/", "get-involved/clubs"), ("/club-hub/resources/", "club-advisors"), ("/club-hub/support/", "give"),
 ("/maker-spaces/", "get-involved/maker-spaces"), ("/vcea-wellness-center/", "wellness"), ("/contact-us/", "about")]

# ---------- rendering ----------
def rel(slug): return "../" * (slug.count("/") + 1) if slug else ""
def url(slug, base): return base + (slug + "/" if slug else "")

def layout(slug, title, main, crumbs=""):
    base = rel(slug) if slug else ""
    top = slug.split("/")[0] if slug else ""
    def sub(s):
        kids = [(k, v["title"]) for k, v in PAGES.items() if v["parent"] == s]
        return kids
    items = []
    for i, (t, s) in enumerate(NAV):
        cur = ' aria-current="page"' if s == top else ""
        kids = sub(s)
        if kids:
            lis = "".join(f'<li><a href="{url(k, base)}">{escape(kt)}</a></li>' for k, kt in kids)
            items.append(f'<li class="has-sub"><a href="{url(s, base)}"{cur}>{escape(t)}</a>'
                         f'<button type="button" class="sub-toggle" aria-expanded="false" aria-controls="sub{i}" aria-label="Show {escape(t)} pages"></button>'
                         f'<ul class="sub" id="sub{i}">{lis}</ul></li>')
        else:
            items.append(f'<li><a href="{url(s, base)}"{cur}>{escape(t)}</a></li>')
    nav = "".join(items)
    util = "".join(f'<li><a href="{url(s, base)}">{t}</a></li>' for t, s in UTIL)
    quick = "".join(f'<li><a href="{url(s, base)}">{t}</a></li>' for t, s in FOOTER_QUICK)
    doc = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{escape(title)} | {SITE_TITLE}</title><link rel="preconnect" href="https://fonts.googleapis.com"><link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;700;800&display=swap" rel="stylesheet"><meta name="color-scheme" content="light"><meta name="robots" content="noindex, nofollow"><link rel="stylesheet" href="{base}css/site.css?v=@@VER@@"></head>
<body><a class="skip" href="#main">Skip to content</a>
<div class="wsu-bar"><div><span>Washington State University</span><ul>{util}</ul></div></div>
<header class="site-header">
 <div class="brand"><div class="titles"><span class="kicker">Voiland College of Engineering and Architecture</span><a class="site-title" href="{base or './'}">{SITE_TITLE}</a><span class="byline">{BYLINE}</span></div>
  <form class="search" role="search" action="#"><label class="sr" for="q">Search</label><input id="q" type="search" placeholder="Search"><button>Search</button></form>
  <button type="button" class="menu-toggle" aria-expanded="false" aria-controls="menu" aria-label="Open menu"></button></div>
 <nav aria-label="Primary" id="primary"><button type="button" class="menu-close">Close Menu</button><ul id="menu">{nav}</ul><ul class="util-mobile">{util}</ul></nav>
</header>
<div class="backdrop" hidden></div>
<main id="main">{crumbs}{main}</main>
<footer class="site-footer"><div class="band" aria-hidden="true"></div>
 <div class="foot-main"><h2>More information</h2>
  <div class="cols">
   <div><h3>Get help</h3><ul><li><a href="{url('academic-help/tutoring', base)}">Tutoring</a></li><li><a href="{url('academic-help/advising', base)}">Advising</a></li><li><a href="{url('academic-help/mentoring', base)}">Mentoring</a></li><li><a href="{url('wellness', base)}">Wellness Center</a></li></ul></div>
   <div><h3>Careers</h3><ul><li><a href="{url('careers/coaching', base)}">Career coaching</a></li><li><a href="{url('careers/internships-propel', base)}">Internships &amp; ProPEL</a></li><li><a href="{url('careers/career-fairs', base)}">Career fairs</a></li><li><a href="{url('careers/toolkit', base)}">Career toolkit</a></li></ul></div>
   <div><h3>Get involved</h3><ul><li><a href="{url('get-involved/clubs', base)}">Clubs</a></li><li><a href="{url('get-involved/maker-spaces', base)}">Maker spaces</a></li><li><a href="{url('get-involved/events', base)}">Events</a></li><li><a href="{url('paying-for-school/scholarships', base)}">Scholarships</a></li></ul></div>
   <div><h3>For</h3><ul><li><a href="{url('employers', base)}">Employers</a></li><li><a href="{url('faculty-staff', base)}">Faculty &amp; Staff</a></li><li><a href="{url('club-advisors', base)}">Club Advisors</a></li><li><a href="{url('give', base)}">Give</a></li></ul></div>
  </div>
  <p class="social"><a href="https://www.facebook.com/WSUVoilandSS">Facebook</a> <a href="https://x.com/WSUVoilandPPEL">X</a> <a href="https://www.linkedin.com/groups/14355576/">LinkedIn</a> Instagram [TBD]</p>
  <p class="small">Student Success Team, Voiland College of Engineering and Architecture<br>PO Box 642250, Pullman, WA 99164-2250, 509-335-5050, <a href="mailto:vcea.info@wsu.edu">vcea.info@wsu.edu</a></p></div>
 <div class="foot-bottom"><span>&copy; Washington State University</span><ul><li>Access</li><li>Policies</li><li>MyWSU</li><li>Follow WSU</li></ul></div></footer>
<script>
@@JS@@
</script>
</body></html>"""
    return mark(doc.replace("@@VER@@", VERSION).replace("@@JS@@", JS).replace("@@/", base))

def render(slug, d):
    crumbs = ""
    if d["parent"]:
        trail = []
        parts = d["parent"].split("/")
        for i in range(len(parts)):
            s = "/".join(parts[:i + 1])
            trail.append(f'<a href="@@/{s}/">{escape(PAGES[s]["title"])}</a>')
        crumbs = '<nav class="crumbs" aria-label="Breadcrumb">' + " › ".join(trail) + f" › {escape(d['title'])}</nav>"
    h = f"<h1>{d['title']}</h1>"
    if d["summary"]: h += f'<p class="lede">{d["summary"]}</p>'
    if d["button"]: h += f'<p>{btn(*d["button"])}</p>'
    if d["where"]: h += f'<div class="where"><strong>Where and when:</strong> {d["where"]}</div>'
    main = h + d["body"]
    if d["contact"]: main += d["contact"]
    if d["related"]:
        main += '<aside class="related"><h2>Related</h2><ul>' + "".join(f'<li><a href="@@/{s}/">{t}</a></li>' for t, s in d["related"][:4]) + "</ul></aside>"
    return layout(slug, d["title"], main, crumbs)

ICON = {'📚': 'M4 5a2 2 0 0 1 2-2h13v16H6a2 2 0 0 0-2 2zM4 21V5M9 7h6', '🧭': 'M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18zM15.5 8.5l-2 5-5 2 2-5z', '💼': 'M3 8h18v12H3zM9 8V5h6v3M3 13h18', '🎓': 'M12 3v18M16 7c0-1.7-1.8-3-4-3s-4 1.3-4 3 1.8 2.5 4 3 4 1.3 4 3-1.8 3-4 3-4-1.3-4-3', '🤝': 'M9 11a3 3 0 1 0 0-6 3 3 0 0 0 0 6zM3 20c0-3 2.7-5 6-5s6 2 6 5M17 10a2.5 2.5 0 1 0 0-5M18 15c2 .4 3 2 3 5', '🛠️': 'M14 6a4 4 0 0 0 4 4l-9 9a2 2 0 0 1-3-3l9-9a4 4 0 0 0-1-1zM4 20l3-3', '💚': 'M12 20s-8-5-8-11a4.5 4.5 0 0 1 8-2.5A4.5 4.5 0 0 1 20 9c0 6-8 11-8 11z', '👋': 'M5 21V4M5 4h12l-2 4 2 4H5'}

def render_home():
    tasks = [("📚", "Get help with a class", "Free drop-in tutoring, SEH 130", "academic-help/tutoring"),
             ("🧭", "Meet with my advisor", "Find your advisor, plan your degree", "academic-help/advising"),
             ("💼", "Find an internship or job", "Coaching, fairs, ProPEL", "careers"),
             ("🎓", "Pay for school", "Scholarships and emergency aid", "paying-for-school/scholarships"),
             ("🤝", "Join a club", "40+ student clubs", "get-involved/clubs"),
             ("🛠️", "Build something", "FIZ, shops, fabrication labs", "get-involved/maker-spaces"),
             ("💚", "Take a break or talk to someone", "Wellness Center, Daggy Hall", "wellness"),
             ("👋", "New to Voiland College?", "First-year and transfer start here", "first-year-transfer")]
    t = "".join(f'<li><a class="task" href="@@/{s}/"><svg class="ico" viewBox="0 0 24 24" aria-hidden="true"><path d="{ICON[i]}"/></svg><span><strong>{x}</strong><small>{h}</small></span></a></li>' for i, x, h, s in tasks)
    main = f"""<section class="hero-slim"><div><h1>{SITE_TITLE}</h1>
<p class="lede">Free support to help you succeed in class, on your career path, and beyond.</p></div></section>
<h2 class="sr">I want to…</h2><ul class="tasks">{t}</ul>
<ul class="today" aria-label="Today at a glance">
 <li><strong>Tutoring</strong> SEH 130, Mon–Fri, <a href="https://tutoring.wsu.edu/">see today's tutors</a></li>
 <li><strong>Career drop-in today</strong> <span id="career-today">SEH 102, see <a href="@@/careers/">hours</a></span></li>
 <li><strong>Wellness Center</strong> Daggy Hall, Mon–Fri 9–4, <a href="tel:988">Crisis? Call/text 988</a></li>
</ul>
<div class="strip">
 <section data-autohide="empty"><h2>Upcoming events</h2><p>[TBD: auto feed, 3–4 items; hide section when empty]</p><a class="arrow-link" href="@@/get-involved/events/">More events</a></section>
 <section data-autohide="empty"><h2>Student Spotlights</h2><p>[TBD: rotating profile]</p><a class="arrow-link" href="@@/get-involved/spotlights/">Browse all spotlights</a></section>
 <section data-autohide="older-than-semester"><h2>News</h2><p>[TBD: latest 3 posts; auto-hide older than one semester]</p></section>
</div>
<script>(function(){{var d={{1:"Mon 2–3 pm",2:"Tue 12–1 pm",3:"Wed 3–4 pm",4:"Thu 12–1 pm",5:"Fri 2–3 pm"}}[new Date().getDay()];
var e=document.getElementById("career-today");if(e)e.innerHTML=d?"SEH 102, "+d:"None today, <a href=\\"@@/careers/\\">weekday hours</a>";}})();</script>"""
    return layout("", "Home", main)

SVG = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" role="img"><rect width="100%" height="100%" fill="{bg}"/><text x="50%" y="50%" fill="{fg}" font-family="sans-serif" font-size="{fs}" text-anchor="middle" dominant-baseline="middle">{t}</text></svg>'
IMAGES = {  # name: (w, h, bg, label)
 "hero.svg": (1400, 420, "#5e6a71", "HERO IMAGE 1400x420"), "card-academic.svg": (600, 300, "#981e32", "ACADEMIC"),
 "card-firstyear.svg": (600, 300, "#4a5a63", "FIRST-YEAR"), "card-careers.svg": (600, 300, "#7a1727", "CAREERS"),
 "card-money.svg": (600, 300, "#5e6a71", "PAYING FOR SCHOOL"), "card-involved.svg": (600, 300, "#981e32", "GET INVOLVED"),
 "spotlight-placeholder.svg": (600, 300, "#4a5a63", "SPOTLIGHT PHOTO"), "person-placeholder.svg": (300, 300, "#8a949a", "PHOTO")}

CSS = """:root{--crimson:#A60F2D;--bright:#CA1237;--dark:#7f0b22;--gray:#595959;--light:#F2F2F2;--ink:#262626;--bg:#fff;--card:#fff;--line:#D8D8D8;--charcoal:#333}
*{box-sizing:border-box}body{margin:0;font:16px/1.55 system-ui,sans-serif;color:var(--ink);background:var(--bg)}
a{color:var(--crimson)}main,.site-footer>div,.brand,.util,nav[aria-label=Primary]>ul{max-width:1100px;margin:0 auto;padding:0 16px}main{padding-top:24px;padding-bottom:48px}
.skip{position:absolute;left:-999px}.skip:focus{left:8px;top:8px;background:#fff;padding:8px;z-index:9}.sr{position:absolute;left:-999px}
.site-header{border-bottom:1px solid var(--line)}.util{font-size:.85rem}.util ul{display:flex;gap:16px;justify-content:flex-end;list-style:none;margin:0;padding:6px 0}
.brand{display:flex;flex-wrap:wrap;gap:16px;justify-content:space-between;align-items:center;padding-top:8px;padding-bottom:8px}
.site-title{font-size:1.5rem;font-weight:700;text-decoration:none;color:var(--crimson)}.byline{margin:0;color:var(--gray);font-size:.9rem}
.search{display:flex;gap:4px}.search input{padding:6px 8px;border:1px solid var(--line);border-radius:4px;background:var(--bg);color:var(--ink)}.search button{padding:6px 10px}
.crumbs{font-size:.85rem;margin-bottom:12px;color:var(--gray)}h1{font-size:2rem;margin:.2em 0}h2{margin-top:1.6em}.lede{font-size:1.15rem;color:var(--gray)}
.btn{display:inline-block;background:var(--crimson);color:#fff;padding:10px 18px;border-radius:4px;text-decoration:none;font-weight:600}.btn-2{background:transparent;color:var(--crimson);border:2px solid var(--crimson)}
.where,.contact,.related,.callout{background:var(--light);border-left:4px solid var(--crimson);padding:12px 16px;margin:16px 0;border-radius:4px}
.crisis{background:#fff3cd;color:#3b2f00;border:2px solid #b8860b;padding:14px 16px;font-size:1.1rem;margin:16px 0;border-radius:4px}.crisis a{color:#3b2f00}
.cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:16px;margin:16px 0}.card{border:1px solid var(--line);background:var(--card);border-radius:6px;padding:16px;display:flex;flex-direction:column;gap:6px}
.card img{width:calc(100% + 32px);margin:-16px -16px 8px;border-radius:6px 6px 0 0;height:auto}.card h3{margin:.2em 0}.card .btn{margin-top:auto;align-self:flex-start}
.person img{width:120px;height:120px;border-radius:50%;margin:0 0 8px;object-fit:cover}.program dl,.card dl{margin:0}dt{font-weight:700;margin-top:6px}dd{margin:0}
.hero{position:relative;color:#fff;margin:-24px -16px 24px;overflow:hidden}.hero img{width:100%;max-height:360px;object-fit:cover;display:block}
.hero div{position:absolute;inset:auto 0 0 0;padding:24px 16px;background:linear-gradient(transparent,rgba(0,0,0,.75))}.hero h1,.hero .lede,.hero .byline{color:#fff;margin:0}
.tasks{list-style:none;padding:0;display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:12px}.task{display:block;padding:18px;border:2px solid var(--crimson);border-radius:6px;font-weight:700;text-decoration:none}.task:hover{background:var(--crimson);color:#fff}
.steps li,.checklist li{margin:6px 0}.checklist{list-style:none;padding-left:0}.checklist li:before{content:"";display:inline-block;width:.8em;height:.8em;border:2px solid var(--gray);border-radius:2px;margin-right:.5em}
details{border:1px solid var(--line);border-radius:4px;margin:8px 0;padding:8px 12px}summary{cursor:pointer;font-weight:600}
.tablewrap{overflow-x:auto}table{border-collapse:collapse;width:100%}th,td{border:1px solid var(--line);padding:8px 10px;text-align:left}th{background:var(--light)}
mark.tbd{background:#fff3b0;color:#222}mark.verify{background:#ffc9c9;color:#222}.map-slot{background:var(--light);padding:60px 16px;text-align:center}
.site-footer{background:var(--dark);color:#fff;padding:24px 0}.site-footer a{color:#fff}.quick{display:flex;flex-wrap:wrap;gap:16px;list-style:none;padding:0}.small{font-size:.85rem}.bottom-cta{margin-top:32px}
/* ---- design layer ---- */
:root{--radius:10px;--shadow:0 1px 2px rgba(0,0,0,.06),0 4px 14px rgba(0,0,0,.06)}
body{font-family:"Segoe UI",system-ui,-apple-system,sans-serif;line-height:1.6}
h1,h2,h3{line-height:1.2;letter-spacing:-.01em}h1{font-size:clamp(1.8rem,4vw,2.5rem)}
h2{font-size:1.4rem;padding-bottom:.3em;border-bottom:2px solid var(--line)}
.site-header{background:var(--bg);position:relative;z-index:20}
.util{background:var(--light)}.util a{color:var(--gray);text-decoration:none}.util a:hover{color:var(--crimson);text-decoration:underline}
.brand{padding-top:14px;padding-bottom:14px}.site-title{letter-spacing:-.01em}
.search input{border-radius:999px;padding:8px 14px;min-width:200px}.search button{border:0;background:var(--crimson);color:#fff;border-radius:999px;padding:8px 16px;cursor:pointer}
nav[aria-label=Primary]{background:var(--crimson)}
nav[aria-label=Primary]>ul{display:flex;flex-wrap:wrap;list-style:none;margin:0 auto;padding:0 8px}
nav[aria-label=Primary] li{position:relative;display:flex;align-items:center}
nav[aria-label=Primary] a{color:#fff;padding:14px 12px;text-decoration:none;font-weight:600;font-size:.95rem;display:block}
nav[aria-label=Primary] a:hover,nav[aria-label=Primary] a[aria-current]{background:var(--dark)}
.sub-toggle{background:none;border:0;color:#fff;cursor:pointer;width:26px;align-self:stretch;margin-left:-8px}
.sub-toggle:after{content:"";display:inline-block;border:5px solid transparent;border-top-color:#fff;border-bottom:0;transition:transform .15s}
.sub-toggle[aria-expanded=true]:after{transform:rotate(180deg)}.sub-toggle:hover{background:var(--dark)}
.sub{display:none;position:absolute;top:100%;left:0;min-width:240px;background:var(--bg);list-style:none;margin:0;padding:6px 0;border-radius:0 0 var(--radius) var(--radius);box-shadow:var(--shadow);border:1px solid var(--line);border-top:0}
.sub-toggle[aria-expanded=true]+.sub{display:block}
nav[aria-label=Primary] .sub a{color:var(--ink);font-weight:500;padding:9px 16px;width:100%}.sub a:hover{background:var(--light);color:var(--crimson)}
.menu-toggle{display:none;background:var(--crimson);color:#fff;border:0;border-radius:6px;padding:8px 14px;font-weight:600;cursor:pointer}

.card{border-radius:var(--radius);box-shadow:var(--shadow);transition:box-shadow .15s}.card:hover{}
.card img{border-radius:var(--radius) var(--radius) 0 0}
.btn{border-radius:999px;padding:10px 20px;transition:background .15s}.btn:hover{background:var(--dark)}.btn-2:hover{background:var(--crimson);color:#fff}
.btn:focus-visible,a:focus-visible,button:focus-visible,summary:focus-visible{outline:3px solid #f0a500;outline-offset:2px}
.where,.contact,.related,.callout{border-radius:var(--radius);border-left-width:5px}.contact h2,.related h2{border:0;margin-top:0;font-size:1.1rem}
.hero{border-radius:0 0 var(--radius) var(--radius)}.task{border-radius:var(--radius);transition:all .15s;background:var(--card)}
.tasks .task:hover{box-shadow:var(--shadow)}
section[data-autohide]{border-left:4px dashed var(--line);padding-left:12px}
main>h1:first-of-type{margin-top:.1em}
@media (max-width:820px){
 .menu-toggle{display:inline-block}.brand{align-items:flex-start}.search{width:100%}.search input{flex:1}
 nav[aria-label=Primary]{display:none}nav[aria-label=Primary].open{display:block}
 nav[aria-label=Primary]>ul{flex-direction:column;padding:0}nav[aria-label=Primary]>ul>li{flex-wrap:wrap;border-top:1px solid rgba(255,255,255,.2)}
 nav[aria-label=Primary]>ul>li>a{flex:1}.sub-toggle{width:48px;margin:0}
 .sub{position:static;display:none;width:100%;box-shadow:none;border:0;border-radius:0;background:var(--dark)}
 nav[aria-label=Primary] .sub a{color:#fff;padding-left:28px}.sub a:hover{background:rgba(0,0,0,.25);color:#fff}
 .util ul{justify-content:flex-start;flex-wrap:wrap}
}
@media (prefers-reduced-motion:reduce){*{transition:none!important}}
/* ---- home: no-scroll layout ---- */
.hero-slim{margin:-24px -16px 16px;padding:22px 16px;color:#fff;background:linear-gradient(rgba(94,15,29,.78),rgba(94,15,29,.78)),url(../img/hero-naming-bridge.jpg) center 30%/cover}
.hero-slim div{max-width:1100px;margin:0 auto}.hero-slim h1{color:#fff;margin:0;font-size:clamp(1.5rem,3.2vw,2.1rem)}.hero-slim .lede{color:#fff;margin:.2em 0 0}
.tasks{grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:10px;margin:0 0 12px}
.task{display:flex;gap:12px;align-items:center;padding:14px 16px;border-width:1px;border-left:5px solid var(--crimson);box-shadow:var(--shadow)}
.task .ico{width:30px;height:30px;flex:none;fill:none;stroke:var(--crimson);stroke-width:1.7;stroke-linecap:round;stroke-linejoin:round}.task:hover .ico{stroke:#fff}.task strong{display:block;font-size:1.02rem}.task small{display:block;font-weight:400;color:var(--gray)}
.task:hover small{color:#fff}
.today{list-style:none;margin:0 0 12px;padding:10px 14px;display:flex;flex-wrap:wrap;gap:6px 24px;background:var(--light);border-radius:var(--radius);font-size:.92rem}
.today strong{margin-right:6px}
.strip{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:12px}.strip section{border:1px solid var(--line);border-radius:var(--radius);padding:4px 14px 12px}
.strip h2{font-size:1rem;margin:.6em 0 .2em;border:0;padding:0}.strip p{margin:.2em 0 .4em;font-size:.9rem}
@media (hover:hover) and (min-width:821px){.has-sub:hover>.sub{display:block}.has-sub:hover>.sub-toggle:after{transform:rotate(180deg)}}
@media (min-width:821px){main:has(.tasks){padding-top:24px;padding-bottom:16px}}

/* ---- home polish (overrides above) ---- */
body{overflow-x:hidden}
.hero-slim{width:100vw;margin:-24px 0 0 calc(50% - 50vw);padding:0;min-height:230px;display:flex;align-items:center;
 background:linear-gradient(90deg,rgba(94,15,29,.94) 0%,rgba(152,30,50,.82) 45%,rgba(152,30,50,.25) 100%),url(../img/hero-naming-bridge.jpg) center 28%/cover}
.hero-slim div{width:100%;max-width:1100px;margin:0 auto;padding:28px 16px 64px}
.hero-slim h1{font-size:clamp(1.8rem,4vw,2.9rem);font-weight:800;letter-spacing:-.02em;max-width:16ch;line-height:1.08;text-shadow:0 1px 12px rgba(0,0,0,.25)}
.hero-slim .lede{font-size:clamp(1rem,1.6vw,1.2rem);max-width:38ch;opacity:.95;margin-top:.6em}
.tasks{margin-top:-44px;position:relative;grid-template-columns:repeat(auto-fit,minmax(255px,1fr));gap:14px}
.task{background:var(--card);color:var(--ink);border:1px solid var(--line);border-left:1px solid var(--line);border-radius:14px;padding:16px 18px;gap:14px;
 box-shadow:0 1px 2px rgba(0,0,0,.05),0 8px 24px rgba(40,10,15,.10);position:relative}
.task:after{content:"";margin-left:auto;width:8px;height:8px;border-right:2px solid var(--gray);border-top:2px solid var(--gray);transform:rotate(45deg);transition:margin .15s,border-color .15s;flex:none}
.task:hover{background:var(--card);color:var(--ink);border-color:var(--crimson);box-shadow:0 2px 4px rgba(0,0,0,.06),0 12px 28px rgba(40,10,15,.16)}
.task:hover:after{margin-right:-3px;border-color:var(--crimson)}.task:hover small{color:var(--gray)}
.task .ico{width:46px;height:46px;padding:11px;box-sizing:border-box;border-radius:12px;background:color-mix(in srgb,var(--crimson) 10%,transparent);stroke-width:1.8}
.task:hover .ico{stroke:var(--crimson);background:color-mix(in srgb,var(--crimson) 16%,transparent)}
.task strong{font-size:1.02rem;line-height:1.25}.task small{margin-top:2px;font-size:.86rem}
.today{margin:6px 0 16px;padding:0;background:none;display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:10px;font-size:.9rem}
.today li{background:var(--light);border-radius:10px;padding:10px 14px;display:flex;flex-direction:column;gap:2px}
.today strong{margin:0;font-size:.72rem;letter-spacing:.07em;text-transform:uppercase;color:var(--crimson)}
.strip section{background:var(--card);border-radius:12px;box-shadow:none}.strip h2{font-size:.78rem;letter-spacing:.07em;text-transform:uppercase;color:var(--gray)}
.strip a{font-weight:600;font-size:.9rem}
@media (max-width:820px){.hero-slim{min-height:0}.hero-slim div{padding:22px 16px 56px}.tasks{margin-top:-36px}}

/* ===== WSU-style visual system (overrides) ===== */
body{font:18px/1.65 Montserrat,"Segoe UI",system-ui,sans-serif;color:var(--ink);background:#fff}
a{color:var(--crimson);text-decoration:underline;text-underline-offset:3px}
.btn,.task,nav a,.site-title,.wsu-bar a,.site-footer a,.skip,.arrow-link{text-decoration:none}
:focus-visible{outline:3px solid #262626!important;outline-offset:2px}
.wsu-bar{background:#3F3F3F;border-bottom:3px solid var(--crimson);color:#fff;font-size:.7rem;letter-spacing:.14em;text-transform:uppercase;font-weight:600}
.wsu-bar>div{max-width:1100px;margin:0 auto;padding:7px 16px;display:flex;justify-content:space-between;gap:16px;flex-wrap:wrap}
.wsu-bar ul{display:flex;gap:18px;list-style:none;margin:0;padding:0}.wsu-bar a{color:#fff;opacity:.9}.wsu-bar a:hover{opacity:1;text-decoration:underline}
.site-header{border-bottom:0;background:#fff}
.brand{padding-top:16px;padding-bottom:14px;gap:12px 24px;flex-wrap:nowrap}
.titles{display:flex;flex-direction:column;border-left:0}
.kicker{font-size:.8rem;font-weight:600;color:var(--gray);line-height:1.2}
.site-title{font-size:clamp(1.3rem,3vw,1.9rem);font-weight:800;color:var(--ink);line-height:1.15}
.byline{font-size:.75rem;color:var(--gray);margin-top:2px}
.search{margin-left:auto}.search input{border-radius:4px;border:1px solid #8a8a8a;padding:8px 12px;font:inherit;font-size:.85rem;min-width:190px}
.search button{border-radius:6px;background:var(--crimson);font:600 .85rem Montserrat,sans-serif;padding:8px 16px}
.menu-toggle{display:none}
nav[aria-label=Primary]{background:#fff;border-top:1px solid var(--line);border-bottom:1px solid var(--line)}
nav[aria-label=Primary] a{color:var(--ink);font-weight:600;font-size:.84rem;padding:15px 12px}
nav[aria-label=Primary]>ul>li>a:hover,nav[aria-label=Primary] a[aria-current]{background:none;color:var(--crimson);box-shadow:inset 0 -4px 0 var(--crimson)}
.sub-toggle{color:var(--ink)}.sub-toggle:after{border-top-color:var(--gray)}.sub-toggle:hover{background:none}
.sub{border:0;border-left:5px solid var(--bright);border-radius:0;box-shadow:0 8px 24px rgba(0,0,0,.18);padding:6px 0}
nav[aria-label=Primary] .sub a{font-weight:600;font-size:.85rem;padding:10px 18px}.sub a:hover{background:var(--light);color:var(--crimson);box-shadow:none}
.menu-close{display:none}.backdrop{position:fixed;inset:0;background:rgba(0,0,0,.6);z-index:90}.backdrop[hidden]{display:none}
h1{font-size:2rem;font-weight:700;margin:.2em 0 .6em;position:relative;padding-bottom:.45em}
h1:after{content:"";position:absolute;left:0;bottom:0;width:72px;height:6px;background:var(--crimson)}
h2{font-size:1.5rem;font-weight:700;border:0;border-top:6px solid var(--line);padding-top:14px;margin:0 0 .6em}
h3{font-size:1.15rem;font-weight:600}.lede{font-size:1.1rem;color:#404040;font-weight:400}
main{padding-top:28px}
main>section{padding:30px 0 20px}
main>section:nth-of-type(odd){background:#fff;box-shadow:0 0 0 100vmax #fff;clip-path:inset(0 -100vmax)}
.btn{background:var(--crimson);border-radius:6px;font-weight:600;font-size:.95rem;padding:11px 22px}.btn:hover{background:var(--dark)}
.btn-2{background:#fff;color:var(--crimson);border:2px solid var(--crimson)}.btn-2:hover{background:var(--crimson);color:#fff}
.card{border:0;border-radius:0;box-shadow:0 2px 10px rgba(0,0,0,.16)}.card img{border-radius:0}.card h3{font-size:1.15rem}.card:hover{box-shadow:0 4px 16px rgba(0,0,0,.22)}
.where,.contact,.related,.callout{background:var(--light);border-left:6px solid var(--crimson);border-radius:0}
.crisis{border-radius:0}
.arrow-link{display:inline-flex;align-items:center;gap:.6em;font-weight:600;color:var(--crimson)}
.arrow-link:before,.strip a:before{content:"";width:28px;height:28px;flex:none;background:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 28 28'%3E%3Ccircle cx='14' cy='14' r='14' fill='%23A60F2D'/%3E%3Cpath d='M9 14h9M14 9l5 5-5 5' stroke='white' stroke-width='2' fill='none'/%3E%3C/svg%3E") center/contain no-repeat}
.strip a{display:inline-flex;align-items:center;gap:.6em;font-weight:600;font-size:.9rem;text-decoration:none}
table th{background:var(--light)}
/* home */
.hero-slim{min-height:240px;align-items:flex-end;background:linear-gradient(rgba(38,38,38,.55),rgba(38,38,38,.78)),url(../img/hero-naming-bridge.jpg) center 28%/cover}
.hero-slim div{padding:28px 16px 68px}
.hero-slim h1{font-size:clamp(2rem,5.2vw,3.8rem);font-weight:800;max-width:20ch;line-height:1.05;padding-bottom:.3em}.hero-slim h1:after{background:var(--bright)}
.hero-slim .lede{color:#fff;font-weight:400}
.task{border:0;border-radius:0;box-shadow:0 2px 12px rgba(0,0,0,.2)}
.task .ico{border-radius:50%;background:var(--bright);stroke:#fff;width:48px;height:48px;padding:12px}.task:hover .ico{background:var(--crimson);stroke:#fff}
.task:hover{border:0;box-shadow:0 4px 18px rgba(0,0,0,.28)}.task:after{border-color:var(--crimson)}
.task small{font-weight:400}
.today li{background:var(--light);border-radius:0}.today strong{color:var(--crimson)}
.strip section{border:0;border-top:6px solid var(--line);border-radius:0;padding:12px 0 8px;background:none}
.strip h2{border:0;padding:0;font-size:.8rem;letter-spacing:.1em;text-transform:uppercase;color:var(--gray)}
/* footer */
.site-footer{background:none;padding:0;margin-top:40px;color:#fff}
.site-footer .band{height:56px;background:var(--bright) repeating-linear-gradient(135deg,rgba(0,0,0,.09) 0 14px,transparent 14px 28px)}
.foot-main{background:var(--charcoal);padding:36px 16px 24px}
.foot-main>*{max-width:1100px;margin-left:auto;margin-right:auto}
.foot-main h2{color:#fff;border:0;padding:0;text-transform:uppercase;letter-spacing:.12em;font-size:.95rem;margin-bottom:1.2em}
.cols{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:24px}
.cols h3{text-transform:uppercase;letter-spacing:.08em;font-size:.8rem;font-weight:700;margin:0 0 .6em}
.cols ul{list-style:none;margin:0;padding:0}.cols li{margin:.35em 0}.cols a{color:#fff;font-size:.88rem;opacity:.92}.cols a:hover{text-decoration:underline;opacity:1}
.social{display:flex;gap:20px;flex-wrap:wrap;margin-top:28px;font-size:.85rem}.social a{color:#fff;text-decoration:underline}
.site-footer .small{opacity:.85;font-size:.8rem}.site-footer .small a{text-decoration:underline}
.foot-bottom{background:#262626;display:flex;justify-content:space-between;flex-wrap:wrap;gap:10px;padding:14px max(16px,calc(50% - 534px));font-size:.7rem;letter-spacing:.1em;text-transform:uppercase}
.foot-bottom ul{display:flex;gap:18px;list-style:none;margin:0;padding:0}
@media (max-width:820px){
 body{font-size:17px}
 .brand{flex-wrap:wrap}.search{order:3;width:100%;margin:0}.search input{flex:1}
 .menu-toggle{display:block;margin-left:auto;width:46px;height:46px;border:0;background:none;cursor:pointer;order:2}
 .menu-toggle:before{content:"";display:block;width:26px;height:3px;background:var(--ink);box-shadow:0 8px 0 var(--ink),0 -8px 0 var(--ink);margin:auto}
 nav[aria-label=Primary]{display:block;position:fixed;top:0;right:0;bottom:0;width:min(88vw,360px);z-index:100;background:#fff;border:0;border-left:6px solid var(--bright);
  transform:translateX(105%);transition:transform .25s;overflow-y:auto;box-shadow:-8px 0 24px rgba(0,0,0,.3)}
 nav[aria-label=Primary].open{transform:none}
 .menu-close{display:flex;align-items:center;gap:10px;width:100%;padding:18px;border:0;border-bottom:1px solid var(--line);background:#fff;font:600 .9rem Montserrat,sans-serif;cursor:pointer;color:var(--ink)}
 .menu-close:before{content:"\00d7";display:inline-flex;align-items:center;justify-content:center;width:28px;height:28px;border-radius:50%;background:var(--bright);color:#fff;font-size:1.2rem;line-height:1}
 nav[aria-label=Primary]>ul>li{border-top:0;border-bottom:1px solid var(--line)}
 nav[aria-label=Primary]>ul>li>a{box-shadow:none!important;padding:16px 18px}
 .sub{background:var(--light);border:0;box-shadow:none;padding:0}
 nav[aria-label=Primary] .sub a{color:var(--ink);padding:12px 18px 12px 30px}.sub a:hover{background:#e6e6e6;color:var(--crimson)}
 .sub-toggle{width:52px}
 .wsu-bar ul{display:none}
 .hero-slim{min-height:200px}
}
@media (prefers-reduced-motion:reduce){nav[aria-label=Primary]{transition:none}}
.util-mobile{display:none}
@media (max-width:820px){.util-mobile{display:block;list-style:none;margin:0;padding:10px 0;background:#3F3F3F}.util-mobile a{color:#fff!important;font-size:.8rem!important;padding:10px 18px!important;text-transform:uppercase;letter-spacing:.08em;box-shadow:none!important}}
.filter{width:100%;max-width:360px;padding:8px 12px;margin:8px 0;border:1px solid var(--line);border-radius:999px;background:var(--bg);color:var(--ink)}

/* site-wide light-gray page background; white bands and cards sit on it */
html,body{background:var(--light)}
.site-header,nav[aria-label=Primary]{background:#fff}
.where,.contact,.related,.callout,.today li,details,.tablewrap{background:#fff}
table th{background:var(--light)}
.strip{background:#fff;box-shadow:0 0 0 100vmax #fff;clip-path:inset(0 -100vmax);padding:16px 0 12px;margin-top:20px}
.hero-slim~.tasks{margin-bottom:16px}
main{padding-bottom:24px}
html{color-scheme:light}
main>section.hero-slim{background:linear-gradient(rgba(38,38,38,.55),rgba(38,38,38,.78)),url(../img/hero-naming-bridge.jpg) center 28%/cover;box-shadow:none;clip-path:none}
/* fixes: desktop menu showed the phone-only utility list; equal-height tiles and card buttons */
nav[aria-label=Primary]>ul.util-mobile{display:none}
.tasks{grid-auto-rows:1fr}.tasks>li{display:flex}.task{flex:1;min-height:92px}
.cards{grid-auto-rows:1fr}
.btn{display:inline-flex;align-items:center;justify-content:center;min-height:48px;box-sizing:border-box;line-height:1.2;text-align:center}
.hero-slim h1{font-size:clamp(1.9rem,4.2vw,3.1rem)}
@media (max-width:820px){nav[aria-label=Primary]>ul.util-mobile{display:block}}
"""

JS = """(function(){
var mt=document.querySelector('.menu-toggle'),nav=document.getElementById('primary');
function closeAll(except){document.querySelectorAll('.sub-toggle[aria-expanded=true]').forEach(function(b){if(b!==except){b.setAttribute('aria-expanded','false');}});}
var bd=document.querySelector('.backdrop');
function setMenu(o){nav.classList.toggle('open',o);document.body.classList.toggle('menu-open',o);if(bd)bd.hidden=!o;if(mt)mt.setAttribute('aria-expanded',o);}
if(mt){mt.addEventListener('click',function(){setMenu(!nav.classList.contains('open'));});}
var mc=document.querySelector('.menu-close');if(mc)mc.addEventListener('click',function(){setMenu(false);});
if(bd)bd.addEventListener('click',function(){setMenu(false);});
document.querySelectorAll('.sub-toggle').forEach(function(b){b.addEventListener('click',function(e){e.stopPropagation();var o=b.getAttribute('aria-expanded')!=='true';closeAll(b);b.setAttribute('aria-expanded',o);});});
document.addEventListener('click',function(e){if(!e.target.closest('.has-sub'))closeAll();});
document.addEventListener('keydown',function(e){if(e.key==='Escape'){closeAll();setMenu(false);}});
})();"""

def main():
    global VERSION
    VERSION = hashlib.md5(CSS.encode()).hexdigest()[:10]
    if SITE.exists(): shutil.rmtree(SITE)
    (SITE / "css").mkdir(parents=True); (SITE / "img").mkdir()
    (SITE / "css" / "site.css").write_text(CSS)
    (SITE / "robots.txt").write_text("User-agent: *\nDisallow: /\n")  # draft site: remove before launch
    for n, (w, h, bg, t) in IMAGES.items():
        (SITE / "img" / n).write_text(SVG.format(w=w, h=h, bg=bg, fg="#fff", fs=h // 10 + 8, t=t))
    if ASSETS.exists():  # real photos dropped in Assets/ override placeholders
        for f in ASSETS.iterdir():
            if f.is_file(): shutil.copy(f, SITE / "img" / f.name)
    (SITE / "index.html").write_text(render_home())
    for slug, d in PAGES.items():
        out = SITE / slug / "index.html"; out.parent.mkdir(parents=True, exist_ok=True); out.write_text(render(slug, d))
    base = "/student-success/"
    with open(ROOT / "redirects.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["old", "new"]); [w.writerow([o, base + n + "/"]) for o, n in REDIRECTS]
    (SITE / "_redirects").write_text("".join(f"{o.split('?')[0] if '?' not in o else o} {base}{n}/ 301\n" for o, n in REDIRECTS))
    missing = [n for _, n in REDIRECTS if n not in PAGES]
    print(f"Built {len(PAGES) + 1} pages, {len(REDIRECTS)} redirects", "| BAD REDIRECT TARGETS: %s" % missing if missing else "")

if __name__ == "__main__": main()
