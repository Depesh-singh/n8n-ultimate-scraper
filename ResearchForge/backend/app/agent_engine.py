import os
import re
import datetime
import logging
from typing import List, Dict, Optional, Any
from .techgium_adapter import (
    get_active_session_token,
    login_techgium,
    verify_techgium_otp,
    fetch_techgium_challenges
)
from .pdf_generator import generate_problem_statements_pdf
from .searcher import perform_search

logger = logging.getLogger(__name__)

PDF_EXPORT_PATH = os.path.join(os.getenv("EXPORTS_DIR", "./exports"), "Techgium_Problem_Statements_All.pdf")

class InteractiveAgentSession:
    def __init__(self):
        self.state: str = "idle"  # "idle", "working", "waiting_for_otp", "waiting_for_credentials", "done", "error"
        self.pending_email: str = os.getenv("TECHGIUM_EMAIL", "")
        self.auth_token: Optional[str] = None
        self.credential_prompt: Optional[Dict[str, Any]] = None
        self.current_goal: str = "Extract all official Techgium problem statements and compile to PDF"
        self.challenges: List[Dict[str, Any]] = []
        self.all_challenges_cache: List[Dict[str, Any]] = []
        self.pdf_available: bool = False
        self.live_logs: List[Dict[str, str]] = []
        self.chat_history: List[Dict[str, str]] = []

        # Auto-initialize session if active token exists in Brave browser
        self._auto_initialize()

    def log(self, message: str, level: str = "info"):
        entry = {
            "time": datetime.datetime.now().strftime("%H:%M:%S"),
            "text": message,
            "level": level  # "info", "action", "success", "warning", "error"
        }
        self.live_logs.append(entry)
        logger.info(f"[Agent] {message}")

    def add_message(self, role: str, content: str):
        self.chat_history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.datetime.now().strftime("%H:%M:%S")
        })

    def _auto_initialize(self):
        """Automatically checks for active Brave browser session on startup."""
        self.log("Initializing Autonomous Problem Statements Scraping Agent...", level="info")
        token = get_active_session_token()
        if token:
            self.auth_token = token
            self.log("Active Techgium authenticated session detected via Brave browser storage!", level="success")
            success, msg, challenges = fetch_techgium_challenges(token)
            if success and challenges:
                self.challenges = challenges
                self.all_challenges_cache = list(challenges)
                self.compile_pdf(challenges)
                self.state = "done"
                self.log(f"Successfully extracted {len(challenges)} official problem statements across all tracks!", level="success")
                self.add_message(
                    "agent",
                    f"🎉 **Techgium Problem Statements Agent Ready!**\n\n"
                    f"I detected your active **Techgium session** and automatically extracted all **{len(challenges)} official problem statements** across AI, Manufacturing, MedTech, Energy, Cyber Security, Mobility, and Robotics.\n\n"
                    f"📄 **Unified Compendium**: Compiled a comprehensive 60+ page PDF with industrial backgrounds, challenge statements, and deliverables.\n"
                    f"📥 **Download**: Click the green **'Download PDF'** button at the top to save it!\n\n"
                    f"💬 *You can also ask me to filter by domain (e.g. 'Show only AI & Robotics') or adjust anything!*"
                )
                return

        # Fallback greeting if no token detected yet
        self.add_message(
            "agent",
            "Hello! I am your Autonomous Research & Scraping Agent. I can extract all problem statements from Techgium, compile them into a unified PDF, or search across any target website. You can talk to me, give feedback, or correct me at any point!"
        )

    def handle_user_message(self, message: str) -> Dict[str, Any]:
        """Main entry point for handling user messages, OTPs, credentials, and conversational corrections."""
        self.add_message("user", message)
        text_clean = message.strip()
        text_lower = text_clean.lower()

        # 1. Check for 6-digit OTP (e.g. "504000", "OTP: 123456", "my otp is 654321")
        otp_match = re.search(r'\b(\d{6})\b', text_clean)
        if otp_match and (self.state == "waiting_for_otp" or "otp" in text_lower or len(text_clean) <= 10):
            otp = otp_match.group(1)
            self.log(f"Detected 6-digit OTP: {otp}. Verifying with Techgium backend...", level="action")
            return self.process_credentials(email=self.pending_email, otp=otp)

        # 2. Automatic JWT Bearer Token Detection (e.g. user pastes raw eyJ... token)
        jwt_match = re.search(r'eyJ[a-zA-Z0-9_\-]{8,}\.[a-zA-Z0-9_\-]{8,}(?:\.[a-zA-Z0-9_\-]+)?', message)
        if jwt_match:
            self.log("Detected JWT Bearer token in message. Validating...", level="action")
            return self.process_credentials(token=jwt_match.group(0))

        # 3. Check if user provided email/password in chat
        email_match = re.search(r'([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)', message)
        pass_match = re.search(r'(?:pass|password|pwd)[:=\s]+([^\s,;]+)', message, re.IGNORECASE)

        if email_match and pass_match:
            email = email_match.group(1)
            pwd = pass_match.group(1)
            return self.process_credentials(email=email, password=pwd)

        # 4. Check if user provided bearer token with keyword
        token_match = re.search(r'(?:token|bearer)[:=\s]+([a-zA-Z0-9\-_.]+)', message, re.IGNORECASE)
        if token_match and len(token_match.group(1)) > 15:
            return self.process_credentials(token=token_match.group(1))

        # 5. Check if user asks for "all problem statements", "all challenges", "start", "continue", etc.
        all_problems_keywords = [
            "all problem", "all problems", "all challenge", "all challenges", 
            "every problem", "more problems", "list of the problem", "techgium",
            "start", "continue", "download", "pdf", "proceed", "fix", "solve"
        ]
        if any(k in text_lower for k in all_problems_keywords):
            # Check if active token is available or can be retrieved from browser
            token = self.auth_token or get_active_session_token()
            if token:
                self.auth_token = token
                self.log("Active session available. Pulling all official problem statements...", level="action")
                return self.execute_techgium_fetch(token)
            else:
                # Attempt auto-login with user's provided credentials
                if self.pending_email:
                    fallback_pwd = os.getenv("TECHGIUM_PASSWORD", "")
                    if fallback_pwd:
                        self.log(f"Attempting login for {self.pending_email}...", level="action")
                        return self.process_credentials(email=self.pending_email, password=fallback_pwd)

        # 6. Check if user is issuing a correction or filter
        if any(w in text_lower for w in ["wrong", "correct", "instead", "only", "filter", "not that", "focus", "show"]):
            return self.handle_user_correction(message)

        # Default conversational response
        if self.challenges:
            response = (
                f"I currently have all **{len(self.challenges)} Techgium problem statements** loaded and compiled into your PDF.\n\n"
                f"- To download the complete PDF, click the **'Download PDF'** button.\n"
                f"- To filter by track, say: *'Show only AI problems'* or *'Filter MedTech'*.\n"
                f"- To refresh from your Techgium account, say *'Refresh'*."
            )
        else:
            response = (
                "I am ready to fetch all problem statements from Techgium! "
                "I can auto-connect to your Brave session, or you can enter your 6-digit OTP / credentials."
            )
        self.add_message("agent", response)
        return self.get_status()

    def process_credentials(self, email: str = None, password: str = None, token: str = None, otp: str = None) -> Dict[str, Any]:
        """Processes credentials, OTP verification, or direct tokens."""
        self.state = "working"

        # Case A: User provided OTP
        if otp:
            target_email = email or self.pending_email or os.getenv("TECHGIUM_EMAIL", "")
            self.log(f"Verifying OTP {otp} for {target_email}...", level="action")
            success, msg, auth_token = verify_techgium_otp(target_email, otp)
            if success and auth_token:
                self.auth_token = auth_token
                self.state = "done"
                self.credential_prompt = None
                self.log(f"OTP verified successfully! Received Bearer token: {auth_token[:15]}...", level="success")
                return self.execute_techgium_fetch(auth_token)
            else:
                self.state = "waiting_for_otp"
                self.log(f"OTP verification failed: {msg}", level="error")
                agent_reply = f"❌ **OTP Verification Failed**: {msg}\n\nPlease check your email for the latest 6-digit OTP code and enter it again."
                self.add_message("agent", agent_reply)
                return self.get_status()

        # Case B: Direct Token
        if token:
            self.log("Received direct session Bearer token. Validating...", level="action")
            self.auth_token = token
            self.credential_prompt = None
            return self.execute_techgium_fetch(token)

        # Case C: Email & Password login
        if email and password:
            self.pending_email = email.strip()
            self.log(f"Authenticating with Techgium for account: {email}...", level="action")
            success, msg, auth_token, requires_otp = login_techgium(email, password)

            if requires_otp or "otp" in msg.lower():
                self.state = "waiting_for_otp"
                self.credential_prompt = {
                    "target": "Techgium OTP",
                    "message": f"Techgium sent an OTP to {email}. Enter the 6-digit OTP to complete authentication.",
                    "fields": ["otp"]
                }
                self.log(f"OTP sent to {email}. Awaiting 6-digit code...", level="info")
                agent_reply = (
                    f"📩 **OTP Sent to Your Email!**\n\n"
                    f"Techgium sent a 6-digit verification code to **{email}**.\n\n"
                    f"👉 Please enter the **6-digit OTP** right here in the chat, and I will immediately pull all 60 problem statements and build your PDF!"
                )
                self.add_message("agent", agent_reply)
                return self.get_status()

            elif success and auth_token:
                self.auth_token = auth_token
                self.credential_prompt = None
                self.log("Login successful without OTP. Fetching challenges...", level="success")
                return self.execute_techgium_fetch(auth_token)
            else:
                # Check if we can fall back to browser session token
                browser_token = get_active_session_token()
                if browser_token:
                    self.auth_token = browser_token
                    self.log("Direct login required OTP, but discovered active Brave browser session token! Using it...", level="success")
                    return self.execute_techgium_fetch(browser_token)

                self.state = "error"
                self.log(f"Authentication failed: {msg}", level="error")
                agent_reply = f"⚠️ Login failed: *{msg}*."
                self.add_message("agent", agent_reply)
                return self.get_status()

        return self.get_status()

    def execute_techgium_fetch(self, token: str) -> Dict[str, Any]:
        """Fetches challenges using token and builds the compendium."""
        self.state = "working"
        self.log("Invoking Techgium API /api/challenges/getChallenges...", level="action")
        success, msg, challenges = fetch_techgium_challenges(token)

        if success and challenges:
            self.challenges = challenges
            self.all_challenges_cache = list(challenges)
            self.log(f"Retrieved {len(challenges)} official Techgium problem statements!", level="success")
            self.compile_pdf(challenges)
            self.state = "done"
            agent_reply = (
                f"🎉 **Success!** Retrieved all **{len(challenges)} official Techgium problem statements** directly from the portal!\n\n"
                f"📄 **Unified Compendium**: Compiled a comprehensive 60+ page PDF with industrial backgrounds, challenge statements, and deliverables.\n"
                f"📥 **Download**: Click the green **'Download PDF'** button at the top to save your copy!"
            )
            self.add_message("agent", agent_reply)
        else:
            self.state = "error"
            self.log(f"Failed to fetch challenges: {msg}", level="error")
            agent_reply = f"Could not retrieve challenges: *{msg}*."
            self.add_message("agent", agent_reply)

        return self.get_status()

    def compile_pdf(self, challenges: List[Dict]):
        """Generates the unified PDF document."""
        self.log("Compiling unified problem statements PDF with ReportLab...", level="action")
        try:
            generate_problem_statements_pdf(challenges, output_path=PDF_EXPORT_PATH)
            self.pdf_available = True
            self.log(f"PDF successfully generated at: {PDF_EXPORT_PATH} ({len(challenges)} challenges included)", level="success")
        except Exception as e:
            self.log(f"Failed to generate PDF: {e}", level="error")
            logger.error(f"PDF generation error: {e}", exc_info=True)

    def handle_user_correction(self, correction: str) -> Dict[str, Any]:
        """Dynamically filters or adjusts the problem statements based on user instructions."""
        self.log(f"Processing user request / filter: '{correction}'", level="action")
        corr_lower = correction.lower()

        base_list = self.all_challenges_cache if self.all_challenges_cache else self.challenges

        # Reset filter
        if any(w in corr_lower for w in ["all", "reset", "show everything", "clear filter", "entire"]):
            self.challenges = list(base_list)
            self.compile_pdf(self.challenges)
            self.state = "done"
            agent_reply = f"🔄 Reset filter! Showing all **{len(self.challenges)} problem statements**. Updated PDF is ready to download."
            self.add_message("agent", agent_reply)
            return self.get_status()

        # Domain keywords mapping
        domain_keywords = {
            "ai": ["ai", "artificial intelligence", "machine learning", "computer vision", "llm", "genai"],
            "manufacturing": ["manufacturing", "cad", "cam", "plant", "factory", "assembly", "cleansing"],
            "medtech": ["medtech", "medical", "health", "biomedical", "pharma", "patient", "clinical"],
            "energy": ["energy", "battery", "power", "solar", "grid", "thermal"],
            "cyber security": ["cyber", "security", "cryptography", "encryption", "vulnerability"],
            "mobility": ["mobility", "ev", "electric vehicle", "automotive", "vehicle"],
            "robotics": ["robotics", "robot", "uav", "drone", "autonomous"],
            "digital platforms": ["digital platform", "cloud", "software", "api", "platform"],
            "sustainability": ["sustainability", "carbon", "green", "clean energy"]
        }

        matched_tracks = []
        for track, keywords in domain_keywords.items():
            if any(k in corr_lower for k in keywords):
                matched_tracks.append(track)

        if matched_tracks:
            filtered = []
            for c in base_list:
                domain_val = str(c.get("domain", "")).lower()
                title_val = str(c.get("title", "")).lower()
                desc_val = str(c.get("challenge", "") or c.get("background", "")).lower()

                for track in matched_tracks:
                    if any(k in domain_val or k in title_val or k in desc_val for k in domain_keywords[track]):
                        filtered.append(c)
                        break

            if filtered:
                self.challenges = filtered
                self.compile_pdf(filtered)
                self.state = "done"
                agent_reply = (
                    f"✅ Filter applied! Found **{len(filtered)} problem statements** matching `{', '.join(matched_tracks).upper()}`.\n\n"
                    f"The PDF compendium has been regenerated with these {len(filtered)} challenges. Click **Download PDF** to save it!"
                )
                self.add_message("agent", agent_reply)
                return self.get_status()

        agent_reply = f"Acknowledged: '{correction}'. You can filter by track (e.g., AI, Manufacturing, MedTech) or ask me to reset."
        self.add_message("agent", agent_reply)
        return self.get_status()

    def get_status(self) -> Dict[str, Any]:
        return {
            "state": self.state,
            "current_goal": self.current_goal,
            "chat_history": self.chat_history,
            "live_logs": self.live_logs[-30:],
            "challenges_count": len(self.challenges),
            "challenges": self.challenges,
            "credential_prompt": self.credential_prompt,
            "pdf_available": self.pdf_available,
            "pdf_filename": "Techgium_Problem_Statements_All.pdf"
        }

# Global singleton session
agent_session = InteractiveAgentSession()
