import uuid
from datetime import datetime, timezone, timedelta
from app.extensions import db
from app.models.user import User
from app.models.form import Form
from app.models.question import Question
from app.models.response import Response
from app.models.answer import Answer


def seed_database():
    """Seeds the database with default creator user, sample published forms and responses."""
    # 1. Create or get default demo creator user
    admin_user = User.query.filter_by(email="demo@scaler.ai").first()
    if not admin_user:
        admin_user = User(email="demo@scaler.ai", name="Scaler Product Team")
        admin_user.set_password("scaler2026")
        db.session.add(admin_user)
        db.session.commit()

    # Check if forms already exist
    if Form.query.first():
        print("Database already contains forms. Skipping seeding.")
        return

    print("Seeding sample forms and responses...")

    # ================= Form 1: Customer Satisfaction & Feedback =================
    csat_form = Form(
        user_id=admin_user.id,
        title="Customer Experience Survey 2026",
        description="Help us shape the future of our product with your candid feedback.",
        slug="customer-feedback",
        status="published",
        views_count=142,
        submissions_count=28,
        theme_settings={
            "font_family": "Inter",
            "text_color": "#18181B",
            "background_color": "#F8FAFC",
            "button_color": "#4F46E5",
            "button_text_color": "#FFFFFF",
            "is_bold": False,
            "is_italic": False,
            "progress_bar": "percentage",
        },
        settings={
            "show_progress_bar": True,
            "show_question_numbers": True,
            "letters_on_answers": True,
        },
    )
    db.session.add(csat_form)
    db.session.flush()

    # Question 0: Welcome Screen (with time to complete badge)
    q0_welcome = Question(
        form_id=csat_form.id,
        order_index=0,
        question_type="welcome",
        title="Welcome to our Annual Experience Survey",
        description="Takes less than 2 minutes. Your feedback directly impacts our 2026 roadmap.",
        required=False,
        properties={
            "button_text": "Let's Begin",
            "stat_badge_type": "time_to_complete",  # Exactly one of: "time_to_complete" or "submissions"
            "estimated_time_minutes": 2,
        },
        media={
            "media_type": "image",
            "media_url": "https://images.unsplash.com/photo-1557804506-669a67965ba0?w=1200&q=80",
            "desktop_orientation": "right_split_1_3",
            "mobile_orientation": "top",
            "alt_text": "Team collaboration",
        },
    )

    # Question 1: Rating (Max 5 stars)
    q1_rating = Question(
        form_id=csat_form.id,
        order_index=1,
        question_type="rating",
        title="How would you rate your overall experience with our platform?",
        description="Rate from 1 to 5 stars.",
        required=True,
        properties={
            "icon": "star",  # "star", "thumbs_up", "heart", "number"
            "max_rating": 5,
        },
        media={
            "media_type": "image",
            "media_url": "https://images.unsplash.com/photo-1516321318423-f06f85e504b3?w=800&q=80",
            "desktop_orientation": "left_box",
            "mobile_orientation": "top",
            "alt_text": "Star rating",
        },
    )

    # Question 2: Yes / No Question with Branching
    q2_yesno = Question(
        form_id=csat_form.id,
        order_index=2,
        question_type="yes_no",
        title="Did our recent AI feature improvements save you time?",
        description="Think about your daily workflow over the past month.",
        required=True,
        properties={
            "branching": {
                "yes": None,  # Continue to next (multiple choice)
                "no": None,
            }
        },
        media={
            "media_type": None,
            "media_url": None,
            "desktop_orientation": "right_split_1_3",
            "mobile_orientation": "top",
            "alt_text": "",
        },
    )

    # Question 3: Multiple Choice (with branching, 'Other', 'None', and single selection)
    q3_mc = Question(
        form_id=csat_form.id,
        order_index=3,
        question_type="multiple_choice",
        title="Which department do you primarily work in?",
        description="Choose the team that best describes your primary responsibility.",
        required=True,
        properties={
            "choices": [
                {"id": "dept_eng", "label": "Engineering & Technology"},
                {"id": "dept_prod", "label": "Product & Design"},
                {"id": "dept_sales", "label": "Sales & Business Development"},
                {"id": "dept_ops", "label": "Operations & Support"},
            ],
            "allow_multiple": False,
            "allow_other": True,
            "allow_none": True,
            "randomize": False,
            "branching": [],
        },
        media={
            "media_type": "image",
            "media_url": "https://images.unsplash.com/photo-1522071820081-009f0129c71c?w=800&q=80",
            "desktop_orientation": "right_box",
            "mobile_orientation": "top",
            "alt_text": "Department team",
        },
    )

    # Question 4: Dropdown Question
    q4_dropdown = Question(
        form_id=csat_form.id,
        order_index=4,
        question_type="dropdown",
        title="How frequently do you log in to your account?",
        description="Select the cadence that best represents your usage.",
        required=True,
        properties={
            "choices": [
                {"id": "cad_daily", "label": "Daily (multiple times a day)"},
                {"id": "cad_weekly", "label": "Weekly (2-3 times a week)"},
                {"id": "cad_monthly", "label": "Monthly"},
                {"id": "cad_rare", "label": "Rarely / Only when needed"},
            ],
            "placeholder": "Choose your usage frequency...",
        },
        media={
            "media_type": None,
            "media_url": None,
            "desktop_orientation": "left_split_1_3",
            "mobile_orientation": "top",
            "alt_text": "",
        },
    )

    # Question 5: Contact Page (with subfields, validation, regex)
    q5_contact = Question(
        form_id=csat_form.id,
        order_index=5,
        question_type="contact",
        title="Where can we send your thank-you swag voucher?",
        description="Leave your contact details so our team can follow up.",
        required=False,
        properties={
            "fields": {
                "first_name": {
                    "enabled": True,
                    "required": True,
                    "placeholder": "e.g. Alex",
                    "regex": "",
                },
                "last_name": {
                    "enabled": True,
                    "required": False,
                    "placeholder": "e.g. Smith",
                    "regex": "",
                },
                "email": {
                    "enabled": True,
                    "required": True,
                    "placeholder": "alex@company.com",
                    "regex": "^[^@]+@[^@]+\\.[^@]+$",
                },
                "phone_number": {
                    "enabled": True,
                    "required": False,
                    "placeholder": "+1 (555) 234-5678",
                    "regex": "^\\+?[0-9\\-\\s()]{7,20}$",
                },
                "company": {
                    "enabled": True,
                    "required": False,
                    "placeholder": "e.g. Scaler AI Labs",
                    "regex": "",
                },
            }
        },
        media={
            "media_type": "image",
            "media_url": "https://images.unsplash.com/photo-1497215728101-856f4ea42174?w=800&q=80",
            "desktop_orientation": "left_split_1_3",
            "mobile_orientation": "top",
            "alt_text": "Contact workspace",
        },
    )

    # Question 6: Long Text with Max Character Limit
    q6_longtext = Question(
        form_id=csat_form.id,
        order_index=6,
        question_type="long_text",
        title="Any additional thoughts or suggestions for our engineering team?",
        description="Feel free to share what we can do better.",
        required=False,
        properties={
            "placeholder": "Type your suggestions here...",
            "max_length": 500,
        },
        media={
            "media_type": None,
            "media_url": None,
            "desktop_orientation": "right_split_1_3",
            "mobile_orientation": "top",
            "alt_text": "",
        },
    )

    # Question 7: End Page (Thank You Screen with socials and button)
    q7_thankyou = Question(
        form_id=csat_form.id,
        order_index=7,
        question_type="thank_you",
        title="You're all done! Thank you so much.",
        description="We've received your responses. Connect with us on social media for early feature releases.",
        required=False,
        properties={
            "button_text": "Visit Scaler AI",
            "button_url": "https://scaler.com",
            "social_links": {
                "twitter": "https://twitter.com/scaler_official",
                "linkedin": "https://linkedin.com/company/scaler-academy",
                "github": "https://github.com",
            },
            "show_reload_button": True,
        },
        media={
            "media_type": "image",
            "media_url": "https://images.unsplash.com/photo-1517245386807-bb43f82c33c4?w=1200&q=80",
            "desktop_orientation": "background",
            "mobile_orientation": "background",
            "alt_text": "Thank you celebration",
        },
    )

    csat_questions = [
        q0_welcome,
        q1_rating,
        q2_yesno,
        q3_mc,
        q4_dropdown,
        q5_contact,
        q6_longtext,
        q7_thankyou,
    ]
    db.session.add_all(csat_questions)
    db.session.flush()

    # Branching: Set yes/no branching in Q2
    # If Yes -> jump directly to Q3 (dept)
    # If No -> jump directly to Q4 (cadence)
    q2_yesno.properties = {
        "branching": {
            "yes": q3_mc.id,
            "no": q4_dropdown.id,
        }
    }

    # ================= Seed Responses for Form 1 =================
    sample_users = [
        {
            "session": uuid.uuid4().hex,
            "ip": "192.168.1.101",
            "duration": 65,
            "r1": 5,
            "r2": "Yes",
            "r3": "Engineering & Technology",
            "r4": "Daily (multiple times a day)",
            "r5": {
                "first_name": "Sarah",
                "last_name": "Connor",
                "email": "sarah@cyberdyne.io",
                "company": "Cyberdyne",
                "phone_number": "+1 555-0192",
            },
            "r6": "The keyboard shortcuts are fantastic! Keep improving the speed.",
        },
        {
            "session": uuid.uuid4().hex,
            "ip": "192.168.1.102",
            "duration": 90,
            "r1": 4,
            "r2": "No",
            "r3": "Product & Design",
            "r4": "Weekly (2-3 times a week)",
            "r5": {
                "first_name": "David",
                "last_name": "Kim",
                "email": "david.kim@designco.com",
                "company": "Design Co",
                "phone_number": "",
            },
            "r6": "Would love more color palette customisation options.",
        },
        {
            "session": uuid.uuid4().hex,
            "ip": "192.168.1.103",
            "duration": 48,
            "r1": 5,
            "r2": "Yes",
            "r3": "Sales & Business Development",
            "r4": "Daily (multiple times a day)",
            "r5": {
                "first_name": "Elena",
                "last_name": "Rostova",
                "email": "elena@ventures.ai",
                "company": "Ventures AI",
                "phone_number": "+1 555-9831",
            },
            "r6": "The one-question-at-a-time experience has boosted our conversion rate!",
        },
        {
            "session": uuid.uuid4().hex,
            "ip": "192.168.1.104",
            "duration": 110,
            "r1": 3,
            "r2": "No",
            "r3": "Operations & Support",
            "r4": "Monthly",
            "r5": {
                "first_name": "Marcus",
                "last_name": "Aurelius",
                "email": "marcus@rome.org",
                "company": "Stoic Inc",
                "phone_number": "",
            },
            "r6": "More CRM integrations would be super helpful.",
        },
    ]

    for su in sample_users:
        sub_time = datetime.now(timezone.utc) - timedelta(hours=len(su["session"]) % 48)
        resp = Response(
            form_id=csat_form.id,
            session_id=su["session"],
            ip_address=su["ip"],
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0",
            status="completed",
            started_at=sub_time - timedelta(seconds=su["duration"]),
            submitted_at=sub_time,
            time_taken_seconds=su["duration"],
        )
        db.session.add(resp)
        db.session.flush()

        # Add answers
        a1 = Answer(response_id=resp.id, question_id=q1_rating.id, question_type="rating", value=su["r1"])
        a2 = Answer(response_id=resp.id, question_id=q2_yesno.id, question_type="yes_no", value=su["r2"])
        a3 = Answer(response_id=resp.id, question_id=q3_mc.id, question_type="multiple_choice", value=su["r3"])
        a4 = Answer(response_id=resp.id, question_id=q4_dropdown.id, question_type="dropdown", value=su["r4"])
        a5 = Answer(response_id=resp.id, question_id=q5_contact.id, question_type="contact", value=su["r5"])
        a6 = Answer(response_id=resp.id, question_id=q6_longtext.id, question_type="long_text", value=su["r6"])
        db.session.add_all([a1, a2, a3, a4, a5, a6])

    csat_form.submissions_count = len(sample_users)

    # ================= Form 2: Event Registration & RSVP =================
    event_form = Form(
        user_id=admin_user.id,
        title="AI Innovators Summit 2026 RSVP",
        description="Register your spot for the premier AI systems conference.",
        slug="ai-summit-rsvp",
        status="published",
        views_count=85,
        submissions_count=12,
        theme_settings={
            "font_family": "Inter",
            "text_color": "#0F172A",
            "background_color": "#FFFFFF",
            "button_color": "#0EA5E9",
            "button_text_color": "#FFFFFF",
            "is_bold": False,
            "is_italic": False,
            "progress_bar": "percentage",
        },
    )
    db.session.add(event_form)
    db.session.flush()

    # Welcome screen showing number of submissions
    e_q0 = Question(
        form_id=event_form.id,
        order_index=0,
        question_type="welcome",
        title="AI Innovators Summit 2026",
        description="Join 500+ AI practitioners and researchers in San Francisco.",
        required=False,
        properties={
            "button_text": "RSVP Now",
            "stat_badge_type": "submissions",  # Shows number of submissions!
            "estimated_time_minutes": 1,
        },
        media={
            "media_type": "image",
            "media_url": "https://images.unsplash.com/photo-1540575467063-178a50c2df87?w=1200&q=80",
            "desktop_orientation": "left_split_1_3",
            "mobile_orientation": "top",
            "alt_text": "Conference Stage",
        },
    )

    # Standalone Contact
    e_q1 = Question(
        form_id=event_form.id,
        order_index=1,
        question_type="contact",
        title="What is your contact information?",
        description="We will send your badge and entry pass to this email.",
        required=True,
        properties={
            "fields": {
                "first_name": {"enabled": True, "required": True, "placeholder": "Jane", "regex": ""},
                "last_name": {"enabled": True, "required": True, "placeholder": "Smith", "regex": ""},
                "email": {"enabled": True, "required": True, "placeholder": "jane@tech.org", "regex": "^[^@]+@[^@]+\\.[^@]+$"},
                "company": {"enabled": True, "required": True, "placeholder": "Organization Name", "regex": ""},
                "phone_number": {"enabled": False, "required": False, "placeholder": "", "regex": ""},
            }
        },
    )

    # Multiple selection multiple choice
    e_q2 = Question(
        form_id=event_form.id,
        order_index=2,
        question_type="multiple_choice",
        title="Which session tracks are you interested in?",
        description="Select all topics you plan to attend.",
        required=True,
        properties={
            "choices": [
                {"id": "tr_llm", "label": "Large Language Models & Agentic Workflows"},
                {"id": "tr_infra", "label": "GPU Infrastructure & Distributed Training"},
                {"id": "tr_vision", "label": "Multimodal Vision & Robotics"},
                {"id": "tr_ethics", "label": "Safety, Alignment & Governance"},
            ],
            "allow_multiple": True,  # Multiple selections enabled! (branching disabled automatically)
            "allow_other": True,
            "allow_none": False,
        },
    )

    # Thank you page
    e_q3 = Question(
        form_id=event_form.id,
        order_index=3,
        question_type="thank_you",
        title="Registration Confirmed!",
        description="See you at the Summit! Check your inbox for calendar invites and venue directions.",
        required=False,
        properties={
            "button_text": "Add to Google Calendar",
            "button_url": "https://calendar.google.com",
            "social_links": {
                "twitter": "https://twitter.com",
                "linkedin": "https://linkedin.com",
            },
            "show_reload_button": False,
        },
    )
    db.session.add_all([e_q0, e_q1, e_q2, e_q3])

    db.session.commit()
    print("Seeding completed successfully!")
