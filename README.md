# AIORI-3 Hackathon Evaluation Platform (`hack_eval`)

This is a custom Frappe v15 application built to manage tracks, teams, mentors, and the multi-round evaluation process for the AIORI-3 Hackathon.

## Overview
The application uses Frappe's native architecture to provide:
- **Track-Based Evaluation**: Mentors are assigned to 1 of 5 tracks. They evaluate all teams within their track.
- **Blind Grading**: Mentors grade independently. `Chief Mentor`s have global track visibility.
- **Three-Round System**: 
  - Level 1: Screening (20 pts)
  - Level 2: Technical Evaluation (70 pts)
  - Level 3: Grand Finale (10 pts)
- **Leaderboards & Scorecards**: Automated calculation of aggregate scores per team.

## Prerequisites
- **Frappe Framework**: Version 15
- **Python**: 3.11+
- **Database**: MariaDB
- **Redis & Node.js (18+)**

## Installation

Run these commands from your `frappe-bench` directory:

1. **Fetch the app from GitHub:**
   ```bash
   bench get-app https://github.com/YOUR_GITHUB_USERNAME/hack_eval.git
   ```
2. **Install the app onto your site (e.g., `test.hackathon.local`):**
   ```bash
   bench --site test.hackathon.local install-app hack_eval
   ```
3. **Run database migrations to ensure everything is synced:**
   ```bash
   bench --site test.hackathon.local migrate
   bench --site test.hackathon.local clear-cache
   ```

## Setup & Seeding

### Manual Data Seeding (Dev/Test Environment)
If you want to populate the system with dummy data for testing purposes, you can manually trigger the seed script. This creates:
- 4 sample mentors with distinct profiles.
- 2 sample faculty members.
- 10 sample teams with valid team compositions.

Run this command from your bench directory:
```bash
bench --site test.hackathon.local execute hack_eval.seed_data.run
```

### Manual CSV Data Import
The app fully aligns with the 37-column Google Form layout for the Hackathon registrations. 
- You can use the standard Frappe **Data Import** tool to import new `Hackathon Team` and `Mentor Profile` records. 
- There are also whitelisted backend functions for importing mentors and teams inside `hack_eval/hackathon_eval/import_data.py`.

## Roles and Permissions
To manage the platform, assign users to these roles:
- **Hackathon Organizer**: Full system access, round toggling, settings configuration.
- **Mentor**: Blind grading (sees only assigned evaluations).
- **Chief Mentor**: Can view all evaluations in their track and make adjustments.
- **Reviewer**: Can audit results.

## Contributing
Ensure all schema changes are committed to GitHub by running `bench export-fixtures` (if applicable) and tracking `hack_eval/` folder changes strictly. Never bypass standard Frappe APIs!
