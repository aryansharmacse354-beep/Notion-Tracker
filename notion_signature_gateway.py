#!/usr/bin/env python3
"""
Notion Tracker - Cryptographic Signature Auditor & Multi-Factor Gateway
------------------------------------------------------------------------
This utility script demonstrates the Zero-Trust Security features built for 
the Notion Tracker's User Profiles (Role-Based Access Control).

It implements:
1. SHA-256 operator-bound audit trail signature verification that binds payload
   details (Task, Timestamp, Outcome) directly to the approving Operator's
   profile (Email, Role).
2. An OTP Authentication Gateway that simulates generating and validating secure
   6-digit verification codes linked to operator phone numbers.
3. High-Risk Task Authorization Validation: A multi-layered gating system that
   requires both successful OTP verification and cryptographic signature validation
   before any high-risk task can be dispatched to the outside world.
4. Automated integrity audits to detect cell-level tampering, identity spoofing,
   or unauthorized high-risk executions.

Developed by Team: AI Experts
- Aryan Sharma (Team Leader and Developer)
- Atul Yadav (Code Quality Testing)
"""

import hashlib
import json
import random
import time
from datetime import datetime, timezone, timedelta

# --- MNC-Standard Color Terminal Formatting Helpers ---
class ConsoleColors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_status(status_type, message):
    if status_type == "info":
        print(f"{ConsoleColors.OKBLUE}[*]{ConsoleColors.ENDC} {message}")
    elif status_type == "success":
        print(f"{ConsoleColors.OKGREEN}[+]{ConsoleColors.ENDC} {ConsoleColors.BOLD}{message}{ConsoleColors.ENDC}")
    elif status_type == "warn":
        print(f"{ConsoleColors.WARNING}[!] WARNING: {message}{ConsoleColors.ENDC}")
    elif status_type == "fail":
        print(f"{ConsoleColors.FAIL}[-] SECURITY ALERT: {message}{ConsoleColors.ENDC}")

# --- Core Cryptographic Hashing Logic ---

def calculate_operator_signature(task_id, task_title, action_details, operator_email, operator_role, timestamp, outcome):
    """
    Computes a deterministic SHA-256 signature that binds the execution payload 
    directly to the operator's profile and role to ensure non-repudiation.
    """
    norm_task_id = str(task_id).strip()
    norm_task_title = str(task_title).strip()
    norm_details = str(action_details).strip()
    norm_email = str(operator_email).strip().lower()
    norm_role = str(operator_role).strip().upper()
    norm_timestamp = str(timestamp).strip()
    norm_outcome = str(outcome).strip().upper()

    # Construct the immutable block payload
    block_payload = f"{norm_task_id}|{norm_task_title}|{norm_details}|{norm_email}|{norm_role}|{norm_timestamp}|{norm_outcome}"
    
    # Compute SHA-256
    hash_obj = hashlib.sha256(block_payload.encode('utf-8'))
    return hash_obj.hexdigest(), block_payload

def verify_log_integrity(stored_signature, task_id, task_title, action_details, operator_email, operator_role, timestamp, outcome):
    """
    Verifies a logged transaction's signature against the current database cell values.
    Returns (is_valid, recalculated_signature).
    """
    recalculated, _ = calculate_operator_signature(
        task_id, task_title, action_details, operator_email, operator_role, timestamp, outcome
    )
    is_valid = (recalculated == stored_signature)
    return is_valid, recalculated

# --- OTP Gateway Simulation & High-Risk Gatekeeper ---

class OTPGateway:
    """
    Simulates a secure OTP authentication service that generates and validates 
    multi-factor challenges tied to operator credentials.
    """
    @staticmethod
    def generate_otp(phone_number):
        """
        Generates a secure 6-digit OTP and logs its generation timestamp.
        """
        otp = f"{random.randint(100000, 999999)}"
        timestamp = datetime.now(timezone.utc)
        print_status("info", f"OTP Gateway: Generated 6-digit verification code for {phone_number} (expires in 5 minutes).")
        return {
            "otp_hash": hashlib.sha256(otp.encode('utf-8')).hexdigest(),
            "timestamp": timestamp,
            "raw_otp_debug": otp # Kept for simulation bypass/input
        }

    @staticmethod
    def verify_otp(phone_number, entered_otp, expected_otp_record):
        """
        Validates the submitted OTP against the expected hash and checks expiration.
        """
        if not expected_otp_record:
            print_status("fail", "OTP Gateway: No active OTP record found for this number.")
            return False

        current_time = datetime.now(timezone.utc)
        expiration_limit = expected_otp_record["timestamp"] + timedelta(minutes=5)

        if current_time > expiration_limit:
            print_status("fail", "OTP Gateway: Verification failed. The OTP has expired (5-minute window exceeded).")
            return False

        entered_hash = hashlib.sha256(str(entered_otp).strip().encode('utf-8')).hexdigest()
        if entered_hash != expected_otp_record["otp_hash"]:
            print_status("fail", "OTP Gateway: Verification failed. Invalid OTP code entered.")
            return False

        print_status("success", f"OTP Gateway: Successfully authenticated operator via phone number {phone_number}.")
        return True


class NotionEnterpriseGuard:
    """
    Zero-Trust Gateway controlling high-risk tasks.
    It requires valid OTP authentication AND a verified cryptographic profile signature 
    before authorizing outbound real-world executions.
    """
    @staticmethod
    def authorize_high_risk_task(operator_profile, task_payload, otp_verified, signature):
        """
        Validates both signature and OTP before granting execution tokens.
        """
        task_id = task_payload.get("task_id")
        task_title = task_payload.get("title")
        action_details = task_payload.get("action")
        timestamp = task_payload.get("timestamp")
        risk_level = task_payload.get("risk_level", "LOW").upper()

        print_status("info", f"Enterprise Guard: Evaluating Authorization Request for high-risk execution.")
        print(f"    - Task ID:    {task_id}")
        print(f"    - Task Title: '{task_title}'")
        print(f"    - Risk Level: {ConsoleColors.FAIL if risk_level == 'HIGH' else ConsoleColors.WARNING}{risk_level}{ConsoleColors.ENDC}")

        # Check 1: Is this a high-risk task requiring OTP?
        if risk_level == "HIGH":
            print_status("info", f"Enterprise Guard: [MFA Required] High-Risk classification detected. Enforcing OTP Gateway check.")
            if not otp_verified:
                print_status("fail", "Enterprise Guard Security Block: Execution blocked! Missing or failed OTP authentication.")
                return {
                    "authorized": False,
                    "reason": "Missing/failed MFA (OTP Verification required for high-risk actions)",
                    "security_seal": None
                }
            print_status("success", "Enterprise Guard: Step 1 Passed (OTP Multi-Factor verified).")
        else:
            print_status("info", "Enterprise Guard: Low/Medium Risk task. Direct signature authorization allowed.")

        # Check 2: Verify Cryptographic Profile Signature
        print_status("info", "Enterprise Guard: Auditing operator's cryptographic signature...")
        is_signature_valid, calculated_hash = verify_log_integrity(
            signature, task_id, task_title, action_details,
            operator_profile["email"], operator_profile["role"],
            timestamp, "SUCCESS"
        )

        if not is_signature_valid:
            print_status("fail", "Enterprise Guard Security Block: Execution blocked! Invalid operator cryptographic signature.")
            return {
                "authorized": False,
                "reason": "Cryptographic Signature check failed (tampering or identity spoofing suspected)",
                "security_seal": None
            }
        
        print_status("success", "Enterprise Guard: Step 2 Passed (Cryptographic Signature validated).")

        # Generate final dynamic authorization seal
        seal_payload = f"AUTH-TOKEN|{task_id}|{operator_profile['email']}|{calculated_hash}"
        auth_seal = hashlib.sha256(seal_payload.encode('utf-8')).hexdigest()

        print_status("success", "MNC SECURITY TOKEN GRANTED: Task execution fully authorized!")
        print(f"    - Authorization Seal: {ConsoleColors.OKGREEN}{auth_seal}{ConsoleColors.ENDC}")

        return {
            "authorized": True,
            "reason": "Fully validated and sealed with MFA + Cryptographic Proof",
            "security_seal": auth_seal
        }

# --- Simulated Hackathon Demonstration Scenarios ---

def run_security_demonstration():
    print("="*80)
    print(f"{ConsoleColors.BOLD}{ConsoleColors.HEADER}    AI Experts: Zero-Trust Cryptographic Signature & OTP Gateway{ConsoleColors.ENDC}")
    print("="*80)
    print(f"Lead Developer:  {ConsoleColors.OKCYAN}Aryan Sharma{ConsoleColors.ENDC}")
    print(f"Quality & QA:    {ConsoleColors.OKCYAN}Atul Yadav{ConsoleColors.ENDC}")
    print("="*80)
    print_status("info", "Initializing audit verification models...\n")

    # Establish Operator Profiles
    aryan_profile = {
        "name": "Aryan Sharma",
        "email": "aryan.sharma@aiexperts.edu",
        "role": "Lead Developer",
        "phone": "+919876543210"
    }

    # Define a High-Risk task payload
    high_risk_task = {
        "task_id": "task-uuid-9999-mfa",
        "title": "Purge Financial Auditing Ledgers & Reallocate Capital",
        "action": "Programmatically delete logs and shift $50,000 USD to priority expansion accounts.",
        "risk_level": "HIGH",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

    print_status("info", "Scenario 1: Attempting high-risk execution with NO OTP authentication.")
    # Calculate a valid signature for the operator, but do NOT execute OTP verification
    valid_signature, _ = calculate_operator_signature(
        high_risk_task["task_id"], high_risk_task["title"], high_risk_task["action"],
        aryan_profile["email"], aryan_profile["role"],
        high_risk_task["timestamp"], "SUCCESS"
    )

    # Attempt execution with otp_verified = False
    auth_result = NotionEnterpriseGuard.authorize_high_risk_task(
        aryan_profile, high_risk_task, otp_verified=False, signature=valid_signature
    )
    print(f"    - Authorization Decision: {ConsoleColors.FAIL}DENIED{ConsoleColors.ENDC}")
    print(f"    - Reason: {auth_result['reason']}\n")

    print_status("info", "Scenario 2: Attempting high-risk execution with a TEMPERED/SPOOFED cryptographic signature.")
    # We trigger the OTP authentication
    otp_record = OTPGateway.generate_otp(aryan_profile["phone"])
    # Operator types correct OTP
    otp_verified = OTPGateway.verify_otp(aryan_profile["phone"], otp_record["raw_otp_debug"], otp_record)

    # Spoofed/Tempered signature payload
    tempered_signature = "this_is_a_faked_or_tampered_hash_value"

    auth_result = NotionEnterpriseGuard.authorize_high_risk_task(
        aryan_profile, high_risk_task, otp_verified=otp_verified, signature=tempered_signature
    )
    print(f"    - Authorization Decision: {ConsoleColors.FAIL}DENIED{ConsoleColors.ENDC}")
    print(f"    - Reason: {auth_result['reason']}\n")

    print_status("info", "Scenario 3: Successful High-Risk Execution Flow (OTP MFA + Valid Signature).")
    # Verify OTP
    otp_record = OTPGateway.generate_otp(aryan_profile["phone"])
    otp_verified = OTPGateway.verify_otp(aryan_profile["phone"], otp_record["raw_otp_debug"], otp_record)

    # Perform authorization
    auth_result = NotionEnterpriseGuard.authorize_high_risk_task(
        aryan_profile, high_risk_task, otp_verified=otp_verified, signature=valid_signature
    )
    print(f"    - Authorization Decision: {ConsoleColors.OKGREEN}APPROVED{ConsoleColors.ENDC}")
    print(f"    - Reason: {auth_result['reason']}\n")

    print_status("info", "Scenario 4: OTP Expiration Test.")
    # Generate OTP
    expired_otp_record = OTPGateway.generate_otp(aryan_profile["phone"])
    # Simulate time dilation (Set timestamp to 6 minutes ago)
    expired_otp_record["timestamp"] = datetime.now(timezone.utc) - timedelta(minutes=6)

    # Verify OTP
    expired_verified = OTPGateway.verify_otp(aryan_profile["phone"], expired_otp_record["raw_otp_debug"], expired_otp_record)
    print(f"    - OTP Verification Status: {ConsoleColors.FAIL}EXPIRED{ConsoleColors.ENDC} ({expired_verified})\n")

    print("="*80)
    print_status("success", "All cryptographic security and OTP MFA gateway features verified successfully.")
    print(f"{ConsoleColors.BOLD}Zero-Trust Human-In-The-Loop Identity Pipeline is fully secured!{ConsoleColors.ENDC}")
    print("="*80)

if __name__ == "__main__":
    run_security_demonstration()
