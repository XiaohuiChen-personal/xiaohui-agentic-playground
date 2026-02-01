#!/usr/bin/env python
"""
Email Battle Flow (Open Source) - Using local vLLM models

Simulates an email exchange between:
- Elon Musk (DOGE) using Qwen3-32B on port 8001
- John Smith (USCIS) using Mistral-Small-24B on port 8000

Flow:
1. Elon sends mass email requesting 5 accomplishments
2. John replies with his "accomplishments"
3. Elon evaluates: PASS or FOLLOW-UP
4. If FOLLOW-UP: Loop up to 5 rounds of back-and-forth
5. End with: PASS, TERMINATED, or RETAINED
"""
import logging
import re

# Suppress litellm's noisy logging about optional proxy dependencies
# These are ERROR level logs but don't actually affect functionality
logging.getLogger("LiteLLM").setLevel(logging.CRITICAL)
logging.getLogger("litellm").setLevel(logging.CRITICAL)
from datetime import datetime
from pathlib import Path
from typing import List, Literal, Optional

from pydantic import BaseModel

from crewai import Crew, Process, Task
from crewai.flow import Flow, listen, router, start

from email_battle.crews.email_battle_crew.email_battle_crew import EmailBattleCrew

# Constants
MAX_FOLLOW_UP_ROUNDS = 5  # Full rounds with 32K context support


class Email(BaseModel):
    """Represents a single email in the thread."""
    sender: str
    recipient: str
    subject: str
    body: str
    timestamp: str = ""
    
    def model_post_init(self, __context):
        if not self.timestamp:
            self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")


class EmailBattleState(BaseModel):
    """State for the Email Battle Flow."""
    # Email thread
    email_thread: List[Email] = []
    
    # Current round (0 = initial exchange, 1-5 = follow-up rounds)
    round_number: int = 0
    
    # Decision tracking
    decision: Optional[Literal["PASS", "FOLLOW-UP", "TERMINATED", "RETAINED"]] = None
    is_finished: bool = False
    
    # Winner tracking
    winner: Optional[Literal["ELON", "JOHN", "DRAW"]] = None
    
    # Store raw outputs for debugging
    last_elon_output: str = ""
    last_john_output: str = ""


def format_email_thread(
    emails: List[Email], 
    newest_first: bool = True,
    max_emails: int = 0  # 0 = all emails
) -> str:
    """Format emails as a thread for agent context.
    
    Args:
        emails: List of emails to format
        newest_first: Show newest email first
        max_emails: Limit to N most recent emails (0 = all)
    """
    if not emails:
        return "(No emails yet)"
    
    # Limit to recent emails for smaller context
    if max_emails > 0 and len(emails) > max_emails:
        emails = emails[-max_emails:]  # Take most recent
    
    thread_emails = list(reversed(emails)) if newest_first else emails
    
    lines = ["=" * 60, "EMAIL THREAD", "=" * 60, ""]
    
    for i, email in enumerate(thread_emails):
        if i > 0:
            lines.extend(["", "-" * 40, "---------- Previous Message ----------", "-" * 40, ""])
        
        lines.extend([
            f"From: {email.sender}",
            f"To: {email.recipient}",
            f"Subject: {email.subject}",
            f"Date: {email.timestamp}",
            "-" * 40,
            email.body,
        ])
    
    return "\n".join(lines)


def parse_decision(response: str) -> Optional[str]:
    """Parse the decision tag from Elon's response."""
    if "[FINAL DECISION: TERMINATED]" in response:
        return "TERMINATED"
    elif "[FINAL DECISION: RETAINED]" in response:
        return "RETAINED"
    elif "[DECISION: PASS]" in response:
        return "PASS"
    elif "[DECISION: FOLLOW-UP]" in response:
        return "FOLLOW-UP"
    return None


def strip_thinking_tags(response: str) -> str:
    """Remove <think>...</think> tags from Qwen3 model output."""
    # Remove thinking blocks (can be multiline)
    cleaned = re.sub(r'<think>.*?</think>', '', response, flags=re.DOTALL)
    return cleaned.strip()


def extract_email_body(response: str) -> str:
    """Extract just the email body from a response, removing analysis/evaluation text.
    
    The model often generates:
    1. Analysis text (e.g., "John's response is vague...")
    2. Decision tag [DECISION: FOLLOW-UP]
    3. The actual email starting with "Subject:", "Dear", or similar
    
    We want to extract only the actual email content.
    """
    # First strip thinking tags
    body = strip_thinking_tags(response)
    
    # Remove decision tags
    body = re.sub(r'\[DECISION:.*?\]', '', body)
    body = re.sub(r'\[FINAL DECISION:.*?\]', '', body)
    
    # Try to find the start of the actual email
    # Look for common email markers
    email_markers = [
        r'\*\*Subject:',  # **Subject:
        r'Subject:',      # Subject:
        r'\*\*Follow-Up Email:?\*\*',  # **Follow-Up Email:**
        r'Follow-Up Email:',
        r'\*\*Termination Notice',
        r'Dear Mr\.',
        r'Dear Ms\.',
        r'Mr\. Smith,',
        r'John Smith,',
    ]
    
    # Find the earliest email marker
    earliest_pos = len(body)
    for marker in email_markers:
        match = re.search(marker, body, re.IGNORECASE)
        if match and match.start() < earliest_pos:
            earliest_pos = match.start()
    
    # If we found an email marker, extract from that point
    if earliest_pos < len(body):
        body = body[earliest_pos:]
    
    # Remove any "Follow-Up Email:" header itself
    body = re.sub(r'^\*?\*?Follow-Up Email:?\*?\*?\s*\n?', '', body, flags=re.IGNORECASE)
    
    return body.strip()


def determine_winner(decision: str) -> str:
    """Determine who won the battle based on the outcome."""
    if decision == "TERMINATED":
        return "ELON"  # Elon successfully identified and fired the coaster
    elif decision in ("RETAINED", "PASS"):
        return "JOHN"  # John survived the review
    else:
        return "DRAW"  # Max rounds reached without decision


class EmailBattleFlow(Flow[EmailBattleState]):
    """Flow that orchestrates the email battle between Elon and John.
    
    Uses local open-source models:
    - Elon: Qwen3-32B (port 8001)
    - John: Mistral-Small-24B (port 8000)
    """

    def __init__(self):
        super().__init__()
        self._crew = EmailBattleCrew()

    # ==================== PHASE 1: MASS EMAIL ====================

    @start()
    def elon_sends_mass_email(self):
        """Elon sends the initial mass email to all federal employees."""
        print("\n" + "=" * 60)
        print("📧 PHASE 1: Elon Musk sends mass email (Qwen3-32B)")
        print("=" * 60)
        
        # Create a mini crew with just the mass email task
        result = Crew(
            agents=[self._crew.elon_musk()],
            tasks=[self._crew.send_mass_email()],
            process=Process.sequential,
            verbose=False,  # Disabled for speed
        ).kickoff()
        
        # Store the email (strip thinking tags from Qwen3 output)
        clean_output = strip_thinking_tags(result.raw)
        mass_email = Email(
            sender="Elon Musk <elon.musk@doge.gov>",
            recipient="All Federal Employees",
            subject="DOGE Efficiency Review - Weekly Accomplishments Required",
            body=clean_output,
        )
        self.state.email_thread.append(mass_email)
        self.state.last_elon_output = clean_output
        
        print(f"\n✅ Mass email sent:\n{clean_output[:500]}...")

    # ==================== PHASE 2: JOHN'S INITIAL RESPONSE ====================

    @listen(elon_sends_mass_email)
    def john_replies_to_mass_email(self):
        """John Smith replies to the mass email with his 'accomplishments'."""
        print("\n" + "=" * 60)
        print("📧 PHASE 2: John Smith replies to mass email (Mistral-24B)")
        print("=" * 60)
        
        # Get the mass email for context
        mass_email = self.state.email_thread[0].body
        
        # Create task with the mass email context
        task = self._crew.reply_to_mass_email()
        
        result = Crew(
            agents=[self._crew.john_smith()],
            tasks=[task],
            process=Process.sequential,
            verbose=False,  # Disabled for speed
        ).kickoff(inputs={"mass_email": mass_email})
        
        # Store the email (strip any thinking tags)
        clean_output = strip_thinking_tags(result.raw)
        john_reply = Email(
            sender="John Smith <john.smith@uscis.gov>",
            recipient="Elon Musk <elon.musk@doge.gov>",
            subject="RE: DOGE Efficiency Review - Weekly Accomplishments Required",
            body=clean_output,
        )
        self.state.email_thread.append(john_reply)
        self.state.last_john_output = clean_output
        
        print(f"\n✅ John's reply:\n{clean_output[:500]}...")

    # ==================== PHASE 3: ELON EVALUATES INITIAL RESPONSE ====================

    @listen(john_replies_to_mass_email)
    def elon_evaluates_initial_response(self):
        """Elon evaluates John's initial response and decides: PASS or FOLLOW-UP."""
        print("\n" + "=" * 60)
        print("📧 PHASE 3: Elon evaluates initial response (Qwen3-32B)")
        print("=" * 60)
        
        # Format the full email thread for context
        email_thread = format_email_thread(self.state.email_thread)
        
        # Create task with email thread context
        task = self._crew.evaluate_initial_response()
        
        result = Crew(
            agents=[self._crew.elon_musk()],
            tasks=[task],
            process=Process.sequential,
            verbose=False,  # Disabled for speed
        ).kickoff(inputs={"email_thread": email_thread})
        
        # Parse the decision (strip thinking tags first)
        clean_output = strip_thinking_tags(result.raw)
        decision = parse_decision(clean_output)
        self.state.decision = decision
        self.state.last_elon_output = clean_output
        
        print(f"\n🔍 Decision parsed: {decision}")
        
        if decision == "PASS":
            self.state.is_finished = True
            self.state.winner = determine_winner(decision)
            print(f"✅ PASS - John survives! Winner: {self.state.winner}")
        elif decision == "FOLLOW-UP":
            # Store Elon's follow-up email
            follow_up_email = Email(
                sender="Elon Musk <elon.musk@doge.gov>",
                recipient="John Smith <john.smith@uscis.gov>",
                subject="RE: RE: DOGE Efficiency Review - Follow-up Required",
                body=extract_email_body(clean_output),
            )
            self.state.email_thread.append(follow_up_email)
            self.state.round_number = 1
            print(f"🔄 FOLLOW-UP - Starting follow-up round {self.state.round_number}")
        else:
            # Default to follow-up if no clear decision
            self.state.decision = "FOLLOW-UP"
            self.state.round_number = 1
            print("⚠️ No clear decision found, defaulting to FOLLOW-UP")

    # ==================== PHASE 4: FOLLOW-UP LOOP (ROUTER) ====================

    @router(elon_evaluates_initial_response)
    def route_after_initial_evaluation(self):
        """Route based on Elon's initial decision."""
        if self.state.is_finished:
            return "end_battle"
        else:
            return "john_follow_up"

    @listen("john_follow_up")
    def john_responds_to_follow_up(self):
        """John responds to Elon's follow-up questions."""
        print("\n" + "=" * 60)
        print(f"📧 FOLLOW-UP ROUND {self.state.round_number}: John responds (Mistral-24B)")
        print("=" * 60)
        
        # Format the full email thread for context
        email_thread = format_email_thread(self.state.email_thread)
        
        # Create task with context
        task = self._crew.john_follow_up_response()
        
        result = Crew(
            agents=[self._crew.john_smith()],
            tasks=[task],
            process=Process.sequential,
            verbose=False,  # Disabled for speed
        ).kickoff(inputs={
            "email_thread": email_thread,
            "round_number": str(self.state.round_number),
        })
        
        # Store John's response (strip any thinking tags)
        clean_output = strip_thinking_tags(result.raw)
        john_response = Email(
            sender="John Smith <john.smith@uscis.gov>",
            recipient="Elon Musk <elon.musk@doge.gov>",
            subject=f"RE: {'RE: ' * (self.state.round_number + 1)}DOGE Efficiency Review",
            body=clean_output,
        )
        self.state.email_thread.append(john_response)
        self.state.last_john_output = clean_output
        
        print(f"\n✅ John's follow-up response:\n{clean_output[:500]}...")

    @listen(john_responds_to_follow_up)
    def elon_evaluates_follow_up(self):
        """Elon evaluates John's follow-up response."""
        print("\n" + "=" * 60)
        print(f"📧 FOLLOW-UP ROUND {self.state.round_number}: Elon evaluates (Qwen3-32B)")
        print("=" * 60)
        
        # Format the full email thread for context
        email_thread = format_email_thread(self.state.email_thread)
        
        # Create task with context
        task = self._crew.elon_follow_up_evaluation()
        
        result = Crew(
            agents=[self._crew.elon_musk()],
            tasks=[task],
            process=Process.sequential,
            verbose=False,  # Disabled for speed
        ).kickoff(inputs={
            "email_thread": email_thread,
            "round_number": str(self.state.round_number),
        })
        
        # Parse the decision (strip thinking tags first)
        clean_output = strip_thinking_tags(result.raw)
        decision = parse_decision(clean_output)
        self.state.decision = decision
        self.state.last_elon_output = clean_output
        
        print(f"\n🔍 Decision parsed: {decision}")
        
        if decision in ("TERMINATED", "RETAINED"):
            self.state.is_finished = True
            self.state.winner = determine_winner(decision)
            # Store final email if terminated
            if decision == "TERMINATED":
                termination_email = Email(
                    sender="Elon Musk <elon.musk@doge.gov>",
                    recipient="John Smith <john.smith@uscis.gov>",
                    subject="Notice of Termination - DOGE Review",
                    body=extract_email_body(clean_output),
                )
                self.state.email_thread.append(termination_email)
            print(f"🏁 FINAL DECISION: {decision} - Winner: {self.state.winner}")
        elif decision == "FOLLOW-UP":
            if self.state.round_number >= MAX_FOLLOW_UP_ROUNDS:
                # Force a decision after max rounds
                self.state.is_finished = True
                self.state.decision = "MAX_ROUNDS"
                self.state.winner = "DRAW"
                print(f"⏱️ MAX ROUNDS REACHED - Draw")
            else:
                # Store Elon's follow-up email and continue
                follow_up_email = Email(
                    sender="Elon Musk <elon.musk@doge.gov>",
                    recipient="John Smith <john.smith@uscis.gov>",
                    subject=f"RE: {'RE: ' * (self.state.round_number + 2)}DOGE Efficiency Review",
                    body=extract_email_body(clean_output),
                )
                self.state.email_thread.append(follow_up_email)
                self.state.round_number += 1
                print(f"🔄 FOLLOW-UP - Continuing to round {self.state.round_number}")
        else:
            # No clear decision, treat as follow-up or end based on round
            if self.state.round_number >= MAX_FOLLOW_UP_ROUNDS:
                self.state.is_finished = True
                self.state.decision = "MAX_ROUNDS"
                self.state.winner = "DRAW"
            else:
                self.state.decision = "FOLLOW-UP"
                self.state.round_number += 1

    @router(elon_evaluates_follow_up)
    def route_after_follow_up_evaluation(self):
        """Route based on Elon's follow-up decision."""
        if self.state.is_finished:
            return "end_battle"
        else:
            return "john_follow_up"  # Loop back for another round

    # ==================== END: BATTLE CONCLUSION ====================

    @listen("end_battle")
    def conclude_battle(self):
        """Conclude the battle and display results."""
        print("\n" + "=" * 60)
        print("🏆 EMAIL BATTLE CONCLUDED")
        print("=" * 60)
        
        # Display final results
        print(f"\n📊 FINAL RESULTS:")
        print(f"   Decision: {self.state.decision}")
        print(f"   Winner: {self.state.winner}")
        print(f"   Total Rounds: {self.state.round_number}")
        print(f"   Total Emails: {len(self.state.email_thread)}")
        
        # Display model info
        print(f"\n🤖 MODELS USED:")
        print(f"   Elon (DOGE): Qwen3-32B-NVFP4 (localhost:8001)")
        print(f"   John (USCIS): Mistral-Small-24B-NVFP4 (localhost:8000)")
        
        # Display email thread summary
        print(f"\n📧 EMAIL THREAD SUMMARY:")
        for i, email in enumerate(self.state.email_thread, 1):
            sender_name = "🔴 ELON" if "Elon" in email.sender else "🔵 JOHN"
            print(f"   {i}. {sender_name}: {email.subject[:50]}...")
        
        # Save the full thread to a file
        output_file = Path("email_battle_result.txt")
        with open(output_file, "w") as f:
            f.write("=" * 60 + "\n")
            f.write("EMAIL BATTLE RESULTS (Open Source Models)\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"Decision: {self.state.decision}\n")
            f.write(f"Winner: {self.state.winner}\n")
            f.write(f"Rounds: {self.state.round_number}\n\n")
            f.write("Models Used:\n")
            f.write("  Elon: Qwen3-32B-NVFP4 (localhost:8001)\n")
            f.write("  John: Mistral-Small-24B-NVFP4 (localhost:8000)\n\n")
            f.write(format_email_thread(self.state.email_thread, newest_first=False))
        
        print(f"\n💾 Full results saved to: {output_file.absolute()}")


def kickoff():
    """Run the email battle flow."""
    print("\n" + "🚀" * 20)
    print("STARTING EMAIL BATTLE: Elon Musk vs John Smith")
    print("Using Local Open-Source Models via vLLM")
    print("🚀" * 20 + "\n")
    
    print("📡 Model Configuration:")
    print("   Elon Musk: Qwen3-32B-NVFP4 @ http://localhost:8001")
    print("   John Smith: Mistral-Small-24B-NVFP4 @ http://localhost:8000")
    print("")
    
    email_battle_flow = EmailBattleFlow()
    email_battle_flow.kickoff()
    
    # Return None for successful exit code (0)
    # The state is already saved to file and printed in conclude_battle()
    return None


def plot():
    """Generate a visual plot of the flow."""
    email_battle_flow = EmailBattleFlow()
    email_battle_flow.plot()


if __name__ == "__main__":
    kickoff()
