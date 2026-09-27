# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from google.cloud import firestore

# Hardcoded GCP Project ID as specified
PROJECT_ID = "qwiklabs-gcp-02-05ea477ba8ab"

def seed_database():
    print(f"Initializing Firestore client for project: {PROJECT_ID}")
    db = firestore.Client(project=PROJECT_ID)

    # 1. Seed Knowledge Base Articles
    kb_articles = [
        {
            "article_id": "KB-001",
            "title": "VPN Connection Drops & Authentication Failures",
            "category": "Network",
            "content": "If GlobalProtect or Cisco AnyConnect drops repeatedly, check MTU size settings, clear stale kerberos tokens via `klist purge`, or restart the VPN agent service. Verify DNS resolution for internal gateway vpn.company.com.",
            "tags": ["vpn", "network", "connectivity"],
            "views": 42
        },
        {
            "article_id": "KB-002",
            "title": "SSO & Okta Multi-Factor Authentication Lockout",
            "category": "Identity",
            "content": "For 403 Forbidden or MFA loop errors on Okta SSO, verify system clock synchronization (NTP). Reset session tokens using admin portal or clear browser cookies for *.okta.com.",
            "tags": ["sso", "okta", "auth", "mfa"],
            "views": 89
        },
        {
            "article_id": "KB-003",
            "title": "Docker Container Out of Memory (OOM) Killed",
            "category": "DevOps",
            "content": "When Docker services crash with exit code 137 (OOMKilled), inspect container memory limits in docker-compose.yml or Kubernetes manifest. Increase RAM allocation or tune JVM heap flags `-Xmx`.",
            "tags": ["docker", "devops", "oom", "memory"],
            "views": 115
        },
        {
            "article_id": "KB-004",
            "title": "Database Connection Pool Exhaustion (PostgreSQL)",
            "category": "Database",
            "content": "If applications receive `fatal: sorry, too many clients already`, inspect active connections via `SELECT count(*) FROM pg_stat_activity`. Ensure connection pooling (e.g., PgBouncer) is enabled and idle timeouts are configured.",
            "tags": ["database", "postgres", "connection", "pool"],
            "views": 67
        }
    ]

    print("Seeding Knowledge Base articles...")
    for article in kb_articles:
        doc_ref = db.collection("knowledge_base").document(article["article_id"])
        doc_ref.set(article)
        print(f"  - Seeded KB article: {article['article_id']} ({article['title']})")

    # 2. Seed Support Tickets
    support_tickets = [
        {
            "ticket_id": "TICKET-101",
            "title": "GlobalProtect VPN failing for Remote Users in EMEA",
            "category": "Network",
            "severity": "High",
            "status": "Open",
            "description": "EMEA engineers reporting gateway timeout when connecting to vpn-emea.company.com.",
            "assigned_team": "Network-Ops",
            "created_at": "2026-09-27 08:30:00 UTC",
            "updated_at": "2026-09-27 08:30:00 UTC"
        },
        {
            "ticket_id": "TICKET-102",
            "title": "PostgreSQL DB connection timeout on Staging Environment",
            "category": "Database",
            "severity": "Medium",
            "status": "In Progress",
            "description": "Staging web service experiencing intermittent 504 Gateway Timeout due to database pool exhaustion.",
            "assigned_team": "Database-Team",
            "created_at": "2026-09-27 09:15:00 UTC",
            "updated_at": "2026-09-27 09:45:00 UTC"
        },
        {
            "ticket_id": "TICKET-103",
            "title": "Okta MFA sync issue for newly onboarded contractors",
            "category": "Identity",
            "severity": "Low",
            "status": "Resolved",
            "description": "Contractor accounts created today were missing default SMS MFA factor. Policy re-synced.",
            "assigned_team": "Identity-IAM",
            "created_at": "2026-09-26 14:00:00 UTC",
            "updated_at": "2026-09-26 16:30:00 UTC"
        }
    ]

    print("Seeding Support Tickets...")
    for ticket in support_tickets:
        doc_ref = db.collection("support_tickets").document(ticket["ticket_id"])
        doc_ref.set(ticket)
        print(f"  - Seeded Ticket: {ticket['ticket_id']} ({ticket['title']})")

    print("\n✅ Firestore seeding complete!")

if __name__ == "__main__":
    seed_database()
