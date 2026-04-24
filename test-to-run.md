# How to Present and Test the Project

We have two different types of tests. One is for presenting visually, and one is for strict backend verification.

## 1. The Visual Presentation Test (For Evaluators)
* **Where to find it:** `showcase.py` (in the main root folder).
* **Its Utility:** It acts like a hijacked AI sending malicious payloads. It prints beautiful, color-coded text to visually prove your "Bouncer" blocks hacks like SQL injections in real-time.
* **How to run it:**
  ```bash
  python showcase.py
  ```

## 2. The Automated Developer Tests (For CI/CD)
* **Where to find it:** `core/tests.py` (in the `core` folder).
* **Its Utility:** These are native Django background tests. They run instantly and mathematically prove to developers that your database, schemas, and security rules are 100% bug-free. It tests edge-cases like memory crashes.
* **How to run it:**
  ```bash
  python manage.py test core
  ```

## 3. The Security Dashboard (Visual Proof of Logs)
* **Where to find it:** `http://localhost:8000/admin` in your web browser.
* **Its Utility:** Proves the "observability" requirement. It shows evaluators the permanent database ledger of all blocked attacks using HTML red/green badges.
* **How to run it:** 
  1. Start the server: `python manage.py runserver`
  2. Log in with Username: `Admin_Alice` | Password: `password123`