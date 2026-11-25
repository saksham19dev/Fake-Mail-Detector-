"""Seed script populating database with 10 genuine and 10 fake sample emails."""
import asyncio
import os
import sys

# Ensure project root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

os.environ.setdefault("DISABLE_SQLALCHEMY_CEXT", "1")

from backend.app.db.session import AsyncSessionLocal, init_db
from backend.app.models.report import Report
from backend.app.models.finding import Finding
from backend.app.models.domain import Domain

GENUINE_SAMPLES = [
    {
        "company": "Cisco",
        "sender": "sudeepta.chauhan@bennett.edu.in",
        "subject": "Bennett Campus Recruitment 2026: Cisco Summer Internship Online Coding Round",
        "score": 10,
        "verdict": "low_risk",
        "text": (
            "Dear B.Tech CSE Students,\n\n"
            "Greetings from the Career Development Centre (CDC), Bennett University.\n\n"
            "Initial screening for the Cisco Summer Internship Program has been finalized. "
            "Shortlisted students are invited to take the Online Technical Assessment round on HackerRank.\n"
            "Test Window: Saturday, 10:00 AM - 11:30 AM.\n"
            "Official Portal: Review specifications at https://careers.cisco.com/jobs/intern-in.\n\n"
            "Important Note: Bennett University and Cisco never charge any registration fee, training deposit, "
            "or courier fee at any stage. Do not share passwords or OTPs.\n\n"
            "Best regards,\nSudeepta Chauhan\nHead - CDC, Bennett University"
        )
    },
    {
        "company": "Microsoft",
        "sender": "sudeepta.chauhan@bennett.edu.in",
        "subject": "CDC Announcement: Microsoft Explore Internship - Virtual Interview Shortlist",
        "score": 10,
        "verdict": "low_risk",
        "text": (
            "Dear Candidates,\n\n"
            "Candidates who completed the initial online coding assessment have been shortlisted for the Virtual Technical Interview.\n"
            "Platform: Microsoft Teams. You can track your status directly on Microsoft Careers at https://careers.microsoft.com.\n"
            "Reminder: Neither Bennett University nor Microsoft will ever request security deposits or money transfers.\n\n"
            "Warm regards,\nSudeepta Chauhan\nBennett University"
        )
    },
    {
        "company": "Google",
        "sender": "sudeepta.chauhan@bennett.edu.in",
        "subject": "Google STEP Internship 2026: Official Technical Schedule",
        "score": 10,
        "verdict": "low_risk",
        "text": (
            "Dear Students,\n\n"
            "The Google STEP Internship drive is now officially open for first and second year B.Tech CSE students.\n"
            "Recruitment Stages: 1. Online Coding Assessment 2. Two technical interview rounds.\n"
            "Apply via Google Careers: https://careers.google.com/jobs/results.\n"
            "Bennett University CDC maintains a zero-tolerance policy against fees. Google never demands payments.\n\n"
            "Best wishes,\nSudeepta Chauhan\nBennett University"
        )
    },
    {
        "company": "Infosys",
        "sender": "instep@infosys.com",
        "subject": "Infosys InStep 2026: Internship Application Status Update",
        "score": 15,
        "verdict": "low_risk",
        "text": (
            "Hello,\n\n"
            "Thank you for applying to the Infosys InStep Global Internship program. "
            "Your profile has been selected for the Technical Mentorship Round. Please select an interview slot "
            "on the official portal at https://infy.com/instep-portal.\n"
            "Infosys strictly prohibits any monetary collection during recruitment.\n\n"
            "InStep Recruitment Team\nInfosys Limited"
        )
    },
    {
        "company": "Tata Consultancy Services",
        "sender": "careers@tcs.com",
        "subject": "TCS CodeVita Season 12: Interview Invitation for High Scorers",
        "score": 10,
        "verdict": "low_risk",
        "text": (
            "Dear Candidate,\n\n"
            "Based on your performance in TCS CodeVita Round 1, you have been invited for a technical interview "
            "for the TCS Research Internship program. Login to TCS NextStep at https://nextstep.tcs.com to book your slot.\n"
            "TCS does not ask for money or security deposits at any stage of recruitment.\n\n"
            "TCS Talent Acquisition Team"
        )
    },
    {
        "company": "Amazon",
        "sender": "university-recruiting@amazon.com",
        "subject": "Amazon WOW Internship 2026: Online Assessment Instructions",
        "score": 15,
        "verdict": "low_risk",
        "text": (
            "Hello,\n\n"
            "You are invited to complete the Amazon Online Assessment for the Software Development Engineer Intern role. "
            "The assessment includes coding on HackerRank and a work simulation. Complete it within 5 days on our portal at "
            "https://amazon.jobs/en/teams/student-programs.\n"
            "Amazon never asks candidates to pay fees for laptops, training, or onboarding.\n\n"
            "Amazon Student Programs"
        )
    },
    {
        "company": "Adobe",
        "sender": "universitytalent@adobe.com",
        "subject": "Adobe SheCodes Mentorship & Summer Trainee Program 2026",
        "score": 10,
        "verdict": "low_risk",
        "text": (
            "Dear Applicant,\n\n"
            "Your application for the Adobe Research Trainee drive has advanced to the project evaluation round. "
            "Please review the assignment details on the Adobe Career Portal at https://adobe.wd5.myworkdayjobs.com.\n"
            "Adobe does not charge any processing or examination fees.\n\n"
            "Adobe Talent Acquisition"
        )
    },
    {
        "company": "Flipkart",
        "sender": "earlycareers@flipkart.com",
        "subject": "Flipkart Runway Season 4: Coding Challenge Access Link",
        "score": 15,
        "verdict": "low_risk",
        "text": (
            "Hi Candidate,\n\n"
            "Get ready for the Flipkart Runway engineering evaluation. The coding test starts this Sunday at 2:00 PM on Unstop. "
            "Shortlisted finalists will proceed directly to virtual panel interviews with Flipkart engineers.\n"
            "Flipkart never solicits payments for internship placement.\n\n"
            "Flipkart Early Careers"
        )
    },
    {
        "company": "Oracle",
        "sender": "campus-india@oracle.com",
        "subject": "Oracle Cloud Infrastructure (OCI) Internship Drive 2026",
        "score": 10,
        "verdict": "low_risk",
        "text": (
            "Dear Student,\n\n"
            "Oracle OCI engineering team is conducting a technical screening for summer intern candidates. "
            "Details regarding test credentials have been provisioned on the Oracle Taleo candidate portal at "
            "https://oracle.taleo.net/careersection.\n"
            "Oracle never asks for registration fees or financial deposits.\n\n"
            "Oracle Campus Relations"
        )
    },
    {
        "company": "IBM",
        "sender": "quantum-interns@ibm.com",
        "subject": "IBM Quantum & AI Student Internship Program 2026",
        "score": 15,
        "verdict": "low_risk",
        "text": (
            "Greetings,\n\n"
            "We are pleased to invite you to the technical interview round for the IBM Quantum Computing Internship. "
            "Please confirm your attendance via the IBM Careers candidate dashboard at https://www.ibm.com/careers.\n"
            "IBM adheres to ethical hiring and never charges fees of any kind.\n\n"
            "IBM Research Talent Team"
        )
    }
]

FAKE_SAMPLES = [
    {
        "company": "Academic Phishing Syndicate",
        "sender": "musaddiquealam511d_2022@umeschandracollege.ac.in",
        "subject": "[Final Reminder] Academic Internship Program – Enrollment Update",
        "score": 85,
        "verdict": "likely_fake",
        "text": (
            "Dear Saksham Giri,\n\n"
            "Records show that your enrollment for the Training Program is still pending.\n\n"
            "Final Deadline: Tomorrow, 7:30 pm\n"
            "Registration Link: https://docs.google.com/forms/d/e/1FAIpQLSf.../viewform?usp=publish_editor\n\n"
            "Failure to register before the deadline will result in:\n"
            "• Removal from the current training batch\n"
            "• No Training & Certification for this cycle.\n"
            "• No access to the Internship & Placement Support associated with this program.\n\n"
            "No further reminders or deadline extensions will be provided.\n"
            "Complete your registration before 7:30 PM to avoid disqualification.\n\n"
            "Regards,\nTraining & Internship Program Team"
        )
    },
    {
        "company": "Bennett Lookalike Impersonator",
        "sender": "sudeepta.chauhan@bennett-careers.org",
        "subject": "Urgent: Confirmation of Bennett University Internship Offer - Deposit Required",
        "score": 95,
        "verdict": "likely_fake",
        "text": (
            "Dear Student,\n\n"
            "I am writing to inform you that you have been shortlisted directly for the Bennett Off-Campus Trainee Placement.\n"
            "To confirm your seat, you must pay a mandatory document verification charge of Rs. 1500 to the desk "
            "UPI id: deskverify@upi within 24 hours. Failure to respond immediately will result in forfeiture of your slot.\n\n"
            "Regards,\nSudeepta Chauhan\nBennett Placement Desk"
        )
    },
    {
        "company": "TechSolutions India",
        "sender": "recruitment@techsolutions-india.org",
        "subject": "CONGRATULATIONS: Selected as Web Developer Intern (Immediate Joining)",
        "score": 95,
        "verdict": "likely_fake",
        "text": (
            "Dear Candidate,\n\n"
            "Congratulations! You have been selected directly without any interview for the Web Development Virtual Internship at TechSolutions India.\n"
            "Stipend: Rs. 45,000 per month (Guaranteed 100% placement). Work from home: 2 hours daily, no skills required!\n\n"
            "To confirm your slot within 24 hours, you must pay a mandatory refundable security and laptop courier fee of Rs. 999 "
            "via UPI to upi-id: hrtech@upi or scan the attached QR code. Send the payment screenshot immediately to our HR on Telegram: t.me/techsolutions_interns.\n\n"
            "Please also send your Aadhaar card photo, PAN card number, and bank account details for stipend processing.\n"
            "Hurry! Only 3 slots left. Offer expires today.\n\n"
            "Regards,\nRahul Verma\nHR Recruitment Lead, TechSolutions"
        )
    },
    {
        "company": "FastData Careers",
        "sender": "pooja.careers2026@gmail.com",
        "subject": "Urgent Freelance Data Entry Interns Required - Earn Rs 40,000/month",
        "score": 80,
        "verdict": "likely_fake",
        "text": (
            "Dear Job Seeker,\n\n"
            "We have immediate requirements for remote part-time interns. Work 1 hour daily and earn Rs. 40,000 per month. "
            "No prior skills or experience required! 100% placement guarantee.\n\n"
            "Do not reply to this email. Contact our recruitment manager only on Telegram: t.me/fastdata_interns. "
            "Send your resume and Aadhaar card copy to begin today. Limited seats available.\n\n"
            "Regards,\nPooja Malhotra\nOnline Hiring Team"
        )
    },
    {
        "company": "Global Remote Systems",
        "sender": "robert.miller.recruiting@gmail.com",
        "subject": "Remote Equipment Cheque Delivery for Student Intern Onboarding",
        "score": 85,
        "verdict": "likely_fake",
        "text": (
            "Dear Applicant,\n\n"
            "You have been accepted directly as a remote research assistant without interview. "
            "We will courier an advance cashier's cheque of $2,500 to your home address. You must deposit the cheque in your bank "
            "account, keep $500 as your first week stipend, and transfer the remaining $2,000 via wire transfer or UPI to our approved equipment vendor.\n\n"
            "Respond with your bank account number and residential address immediately.\n\n"
            "Robert Miller\nGlobal Remote Systems"
        )
    },
    {
        "company": "Apex Digital Labs",
        "sender": "hiring@apex-digitallabs.biz",
        "subject": "Offer Letter: Direct Appointment as Junior AI Engineer (No Interview Needed)",
        "score": 80,
        "verdict": "likely_fake",
        "text": (
            "Dear Candidate,\n\n"
            "Based on your profile, you have been granted direct selection without any interview for the AI Specialist Internship. "
            "Stipend: Rs. 60,000 per month. No prior experience needed.\n"
            "To activate your employee portal, pay the seat booking fee of Rs. 1,200 to hr@upi within 12 hours. "
            "Failure to respond immediately will result in disqualification.\n\n"
            "Apex Hiring Desk"
        )
    },
    {
        "company": "FastTrack Analytics",
        "sender": "screening-desk@yahoo.com",
        "subject": "Urgent: Complete your WhatsApp Interview for Data Science Internship",
        "score": 75,
        "verdict": "likely_fake",
        "text": (
            "Dear Applicant,\n\n"
            "Your internship resume has been shortlisted. We conduct all screening exclusively on WhatsApp. "
            "Click here to message our hiring team: wa.me/919876543210. Do not send emails to this address.\n"
            "Please have your PAN card details ready on chat.\n\n"
            "FastTrack Analytics HR"
        )
    },
    {
        "company": "Global Edutech Certifications",
        "sender": "admin@edutech-certifications.info",
        "subject": "Mandatory Training Certificate Required for Cloud Internship Onboarding",
        "score": 85,
        "verdict": "likely_fake",
        "text": (
            "Dear Student,\n\n"
            "Congratulations on your selection for the Cloud Developer Internship. Before joining, you are required "
            "to complete our proprietary certification. Please pay the mandatory processing fee of Rs. 2,999 at http://bit.ly/edutech-pay. "
            "Failure to pay within 24 hours will lead to offer cancellation.\n\n"
            "Edutech Certification Authority"
        )
    },
    {
        "company": "QuickHire Recruitment",
        "sender": "quickhire2026@outlook.com",
        "subject": "Urgent Document Verification: Send Aadhaar and Net Banking Details",
        "score": 80,
        "verdict": "likely_fake",
        "text": (
            "Dear Fresher,\n\n"
            "You have been shortlisted for an immediate virtual internship. To expedite your appointment letter, "
            "reply immediately with your Aadhaar card photo, PAN card number, and cancelled cheque for bank transfer details.\n"
            "Offer expires today. Limited slots available.\n\n"
            "QuickHire HR Team"
        )
    },
    {
        "company": "NextGen Software Solutions",
        "sender": "hr-eval@nextgen-solutions.net",
        "subject": "Download and Run Coding Assessment Tool (assessment.exe)",
        "score": 85,
        "verdict": "likely_fake",
        "text": (
            "Dear Candidate,\n\n"
            "To proceed with your technical round, you must download and run the attached assessment tool (setup.exe). "
            "Please disable your antivirus software temporarily during installation to avoid false alarms.\n"
            "You have 2 hours to install our portal to proceed.\n\n"
            "NextGen IT Support"
        )
    }
]


async def seed_database():
    """Seeds the database with 10 genuine and 10 fake sample reports."""
    print("Initializing database...")
    await init_db()

    async with AsyncSessionLocal() as session:
        # Seed Trusted Domains
        trusted = [
            ("bennett.edu.in", 3650, "ERNET India", False),
            ("cisco.com", 12000, "MarkMonitor Inc.", False),
            ("microsoft.com", 11000, "Corporation Service Company", False),
            ("google.com", 10000, "MarkMonitor Inc.", False),
            ("bennett-careers.org", 5, "NameCheap Inc.", True),  # Blocklisted lookalike
            ("umeschandracollege.ac.in", 4500, "ERNET India", True),  # Flagged compromised
        ]

        for dom, age, reg, blocked in trusted:
            existing = await session.get(Domain, dom)
            if not existing:
                session.add(Domain(domain=dom, age_days=age, registrar=reg, blocklisted=blocked))

        # Seed Genuine Reports
        print("Seeding 10 genuine offer reports...")
        for s in GENUINE_SAMPLES:
            dom = s["sender"].split("@")[-1]
            rep = Report(
                sender_domain=dom,
                company=s["company"],
                score=s["score"],
                verdict=s["verdict"],
                status="completed",
                redacted_text=s["text"]
            )
            session.add(rep)
            await session.flush()

            # Add finding
            f = Finding(
                report_id=rep.id,
                rule_id="verified_company_domain",
                weight=-20,
                confidence=1.0,
                evidence="Verified official company / university placement communication"
            )
            session.add(f)

        # Seed Fake Reports
        print("Seeding 10 fake offer reports...")
        for s in FAKE_SAMPLES:
            dom = s["sender"].split("@")[-1]
            rep = Report(
                sender_domain=dom,
                company=s["company"],
                score=s["score"],
                verdict=s["verdict"],
                status="completed",
                redacted_text=s["text"]
            )
            session.add(rep)
            await session.flush()

            # Add findings
            f1 = Finding(
                report_id=rep.id,
                rule_id="fee_demand" if "fee" in s["text"].lower() or "deposit" in s["text"].lower() else "suspicious_messaging",
                weight=50,
                confidence=0.95,
                evidence="Critical scam red flag pattern identified in message body"
            )
            session.add(f1)

        await session.commit()
        print("Database seeded successfully with 10 genuine and 10 fake benchmark reports!")


if __name__ == "__main__":
    asyncio.run(seed_database())
