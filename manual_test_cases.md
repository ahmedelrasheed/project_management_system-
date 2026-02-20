# Manual Test Cases - Task & Project Management Module
# حالات الاختبار اليدوية - نظام إدارة المهام والمشروعات

> Test after upgrading the module: `-u task_project_management`
> Odoo URL: http://localhost:8069

---

## Pre-Test Setup

### Users Needed
| User | Login | Password | Role |
|------|-------|----------|------|
| Administrator | admin | admin | Admin Manager |
| PM User (create manually OR via member sync) | pm@test.com | 123456 | Project Manager |
| Member User (create via Admin → Members) | member1@test.com | 123456 | Member |
| Member 2 (create via Admin → Members) | member2@test.com | 123456 | Member |
| Plain User (create from Settings → Users, no TM group) | plain@test.com | 123456 | Internal User only |

---

## SECTION 1: Member ↔ User Bidirectional Sync

### TEST 1.1 — Admin creates a Member → User auto-created
1. Login as **admin**
2. Go to **Task Management → Members → Members**
3. Click **New**
4. Fill in: Name = "Test Sync User", Email = "sync@test.com"
5. Click **Save**

**Expected:**
- [x] Member is saved successfully
- [x] The "Related User" field is automatically filled with a new user
- [x] The auto-created user has login = "sync@test.com"

**Verify:** Go to **Settings → Users** and search for "sync@test.com"
- [x] User exists with name "Test Sync User"
- [x] User has the "Member" group under Task Management

### TEST 1.2 — Auto-created user can log in
1. Log out from admin
2. Go to login page
3. Login with: Email = "sync@test.com", Password = "123456"

**Expected:**
- [x] Login succeeds
- [x] User sees the Task Management menu

### TEST 1.3 — Admin creates a User from Settings → Member auto-created
1. Login as **admin**
2. Go to **Settings → Users & Companies → Users**
3. Click **New**
4. Fill in: Name = "Settings User", Email = "settings@test.com"
5. Save

**Verify:** Go to **Task Management → Members → Members**
- [x] A member named "Settings User" exists with email "settings@test.com"
- [x] The member's "Related User" field links to the user you just created

### TEST 1.4 — Creating a Member with an existing user's email → links them
1. Login as **admin**
2. First, create a user from Settings: Name = "Existing User", Email = "existing@test.com"
3. Go to **Task Management → Members → Members**
4. Note: a member was auto-created for "existing@test.com" (from TEST 1.3 logic)
5. Delete that auto-created member (if exists) — or use a fresh email for this test
6. Alternative: Create user "link@test.com" from Settings, delete the auto-created member, then create a new member with email "link@test.com"

**Expected:**
- [x] The member is linked to the existing user (no duplicate user created)

### TEST 1.5 — No recursion / no duplicates
1. Login as **admin**
2. Create a member with email "nodup@test.com"
3. Go to Settings → Users, search "nodup@test.com"

**Expected:**
- [x] Exactly ONE user with login "nodup@test.com" (not two)
- [x] Exactly ONE member with email "nodup@test.com" (not two)

---

## SECTION 2: Role-Based UI Restrictions

### TEST 2.1 — PM cannot create Projects
1. Login as **PM user** (pm@test.com)
2. Go to **Task Management → Projects → Projects**

**Expected:**
- [x] The "New" button is NOT visible (no create permission)
- [x] PM can see and open existing projects they manage
- [x] PM can edit project fields (write is still allowed)

### TEST 2.2 — PM cannot create Members
1. Still logged in as **PM user**
2. Go to **Task Management → Members → Members**

**Expected:**
- [x] The "New" button is NOT visible
- [x] PM can see members in their managed projects
- [x] PM can view member details (read allowed)

### TEST 2.3 — Admin CAN create Projects and Members
1. Login as **admin**
2. Go to **Task Management → Projects → Projects**
- [x] "New" button IS visible
3. Go to **Task Management → Members → Members**
- [x] "New" button IS visible

### TEST 2.4 — Menu labels are correct
1. Login as **PM user** or **admin**
2. Open **Task Management** menu

**Expected:**
- [x] Menu says "Projects" (not "All Projects")
- [x] Menu says "Members" (not "All Members")

### TEST 2.5 — "My Tasks" menu restricted to Members
1. Login as **plain user** (plain@test.com, no Task Management group)
2. Go to Task Management (if visible)

**Expected:**
- [x] "My Tasks" parent menu is NOT visible to plain users
- [x] "Archive / Portfolio" IS visible to any internal user

---

## SECTION 3: Archive Without Member Requirement

### TEST 3.1 — Any logged-in user can create an archive entry
1. Login as **plain user** (plain@test.com — internal user, NOT a member)
2. Go to **Task Management → Archive / Portfolio → My Archive**
3. Click **New**
4. Fill in: Project Name = "Personal Project", Visibility = "Private"
5. Click **Save**

**Expected:**
- [x] Archive entry is created successfully
- [x] "User" field shows the current user (plain@test.com)
- [x] "Member" field is empty (since this user has no member record) or hidden

### TEST 3.2 — Member user creates archive → both user_id and member_id populated
1. Login as **member1** (member1@test.com)
2. Go to **Task Management → Archive / Portfolio → My Archive**
3. Click **New**, fill in Project Name = "My Portfolio Entry"
4. Save

**Expected:**
- [x] "User" field = member1 user
- [x] "Member" field = member1's member record (auto-defaulted)

### TEST 3.3 — Users can only edit/delete their own archive entries
1. Login as **member1**
2. Create an archive entry
3. Log out, login as **member2**
4. Go to **Archive / Portfolio → Browse Public Archives** (if member1's entry is public)
   OR try to access member1's archive entry directly via URL

**Expected:**
- [x] member2 CANNOT edit member1's archive entry (AccessError)
- [x] member2 CANNOT delete member1's archive entry (AccessError)

### TEST 3.4 — Admin can edit/delete any archive entry
1. Login as **admin**
2. Browse any user's archive entry
3. Try to edit and save

**Expected:**
- [x] Admin can edit any archive entry without error
- [x] Admin can delete any archive entry

### TEST 3.5 — My Archive shows only current user's entries
1. Login as **member1**, create 2 archive entries
2. Login as **member2**, create 1 archive entry
3. As member2, go to **My Archive**

**Expected:**
- [x] Only member2's archive entry is shown (not member1's)

### TEST 3.6 — Public archives visible to everyone
1. Login as **member1**, create archive with Visibility = "Public"
2. Login as **member2**, go to **Browse Public Archives**

**Expected:**
- [x] member1's public entry is visible
- [x] member1's private entries are NOT visible

---

## SECTION 4: Hidden Discuss & Apps Menus

### TEST 4.1 — Discuss menu is hidden
1. Login as **any user** (admin, PM, member)
2. Look at the top-level menu bar

**Expected:**
- [x] "Discuss" (or messaging icon) is NOT in the top menu
- [x] No way to access the Discuss/Messaging app

### TEST 4.2 — Apps menu is hidden
1. Login as **admin**
2. Look at the top-level menu bar

**Expected:**
- [x] "Apps" menu is NOT in the top menu
- [x] Module installation/management is not accessible from the UI

### TEST 4.3 — All other menus still work
1. Login as **admin**
2. Check that these menus are still visible and functional:
- [x] Task Management
- [x] Settings
- [x] Contacts (if installed)

---

## SECTION 5: Simplified User Profile Dropdown

### TEST 5.1 — User dropdown shows only essential items
1. Login as **any user**
2. Click on the **user avatar/name** in the top-right corner

**Expected:**
- [x] "My Account" (or "Preferences") IS visible
- [x] "Log out" IS visible
- [x] "Documentation" is NOT visible
- [x] "Support" is NOT visible
- [x] "Shortcuts" is NOT visible
- [x] "My Odoo.com Account" is NOT visible

---

## SECTION 6: Chatter Removed from Forms

### TEST 6.1 — Member form has no chatter
1. Login as **admin**
2. Go to **Task Management → Members → Members**
3. Open any member's form

**Expected:**
- [x] No "Send Message" button at the bottom
- [x] No "Log Note" button
- [x] No "Schedule Activity" button
- [x] No message thread / conversation area
- [x] All other fields and tabs (Managed Projects, Member Projects, Tasks) still work

### TEST 6.2 — Project form has no chatter
1. Go to **Task Management → Projects → Projects**
2. Open any project form

**Expected:**
- [x] No "Send Message" / "Log Note" / "Activities" section
- [x] Status bar still works (Active, On Hold, Completed, Archived)
- [x] All tabs still work (Project Managers, Members, Removed Members, Tasks)

### TEST 6.3 — Task form has no chatter
1. Go to **Task Management → My Tasks → My Tasks**
2. Open any task form

**Expected:**
- [x] No "Send Message" / "Log Note" / "Activities" section
- [x] Approve/Reject buttons still visible (for PM/Admin)
- [x] Status bar (Pending/Approved/Rejected) still works
- [x] **Audit Trail tab STILL shows** (this is a custom One2many, not chatter)
- [x] All fields still editable (for pending/rejected tasks)

### TEST 6.4 — Internal notifications still work (mail.thread)
1. Login as **member1**, create a new task in a project
2. Login as the **PM** of that project

**Expected:**
- [x] PM receives a notification (bell icon) about the new task submission
- [x] Even though chatter UI is removed, message_post() still works internally

---

## SECTION 7: Core Functionality Regression Tests

> These ensure existing features didn't break after the changes.

### TEST 7.1 — Task Creation (Happy Path)
1. Login as **member1**
2. Go to **My Tasks → My Tasks → New**
3. Fill: Date = today, Project = (an active project), Time From = 09:00, Time To = 12:00, Description = "Test task"
4. Save

**Expected:**
- [x] Task saved with status "Pending"
- [x] Duration = 3:00 hours (auto-calculated)
- [x] Audit trail shows one entry: status = "Pending"

### TEST 7.2 — Overlapping Time Blocked
1. As **member1**, create task: Date = today, Project A, Time 09:00-12:00
2. Create another task: Date = today, Project B, Time 11:00-14:00

**Expected:**
- [x] Second task is BLOCKED with overlap error
- [x] Changing time to 12:00-14:00 should work (adjacent = OK)

### TEST 7.3 — Approval Workflow
1. **member1** creates a task (status = Pending)
2. Login as **PM** of that project
3. Open the task → click "Reject" → add comment "Please fix description"
4. Login as **member1** → edit the task description → save
5. Login as **PM** → open the task → click "Approve"

**Expected:**
- [x] After rejection: status = "Rejected", member can edit
- [x] After member edit: status resets to "Pending"
- [x] After approval: status = "Approved", task is LOCKED
- [x] Audit trail shows full cycle: Pending → Rejected → Pending → Approved

### TEST 7.4 — PM sees only managed project tasks
1. Create Project A (PM = pm_user) and Project B (PM = another_pm)
2. member1 creates tasks in both projects
3. Login as **pm_user**

**Expected:**
- [x] pm_user sees tasks in Project A (managed)
- [x] pm_user does NOT see tasks in Project B (not managed)

### TEST 7.5 — Project Status Effects
1. As **admin**, set a project to "On Hold"
2. As **member1**, try to create a task in that project

**Expected:**
- [x] Task creation is BLOCKED (project on hold)

3. As **admin**, set the project to "Completed"
- [x] Members BLOCKED from creating tasks
- [x] Admin CAN still create tasks

4. As **admin**, set the project to "Archived"
- [x] Project disappears from non-admin views
- [x] Admin can see it under Administration → Archived Projects

### TEST 7.6 — Past Date Entry Limit
1. Check Settings → Task Management → Past Date Limit (default: 3 days)
2. As **member1**, try to create a task with date = 10 days ago

**Expected:**
- [x] BLOCKED for members (beyond 3-day limit)
- [x] Task is flagged as "Late Entry" if within limit but in the past

3. As **PM or Admin**, try the same 10-day-ago date
- [x] ALLOWED (PMs/Admins bypass the limit)

### TEST 7.7 — Member removed from project
1. As **admin**, remove member1 from Project A (edit project → remove from Members tab)
2. As **member1**, try to create a task in Project A

**Expected:**
- [x] Project A no longer appears in member1's project dropdown
- [x] member1's old tasks in Project A are still visible (not deleted)
- [x] member1 appears in Project A's "Removed Members" tab

### TEST 7.8 — Settings (Admin Only)
1. Login as **admin** → Task Management → Configuration → Settings
2. Change "Past Date Limit" to 5
3. Toggle "After-Midnight Tasks"
4. Save

**Expected:**
- [x] Settings are saved and applied
- [x] PM and Member users CANNOT access Settings (menu hidden / access denied)

---

## SECTION 8: Dashboard Smoke Tests

### TEST 8.1 — Member Dashboard
1. Login as **member1** → Task Management → My Tasks → My Dashboard

**Expected:**
- [x] Dashboard loads without errors
- [x] Shows task summary, hours worked

### TEST 8.2 — PM Dashboard
1. Login as **PM** → Task Management → Projects → PM Dashboard

**Expected:**
- [x] Dashboard loads without errors
- [x] Shows project progress, member activity, pending approvals

### TEST 8.3 — Admin Dashboard
1. Login as **admin** → Task Management → Administration → Admin Dashboard

**Expected:**
- [x] Dashboard loads without errors
- [x] Shows organization-wide overview

---

## Quick Checklist Summary

| # | Test | Status |
|---|------|--------|
| 1.1 | Create Member → User auto-created | ☐ |
| 1.2 | Auto-created user can log in | ☐ |
| 1.3 | Create User → Member auto-created | ☐ |
| 1.4 | Member with existing user email → linked | ☐ |
| 1.5 | No duplicate users/members | ☐ |
| 2.1 | PM cannot create Projects | ☐ |
| 2.2 | PM cannot create Members | ☐ |
| 2.3 | Admin CAN create both | ☐ |
| 2.4 | Menu labels renamed | ☐ |
| 2.5 | My Tasks hidden from non-members | ☐ |
| 3.1 | Plain user creates archive entry | ☐ |
| 3.2 | Member archive has both user_id + member_id | ☐ |
| 3.3 | Can only edit/delete own archive | ☐ |
| 3.4 | Admin can edit any archive | ☐ |
| 3.5 | My Archive filtered to current user | ☐ |
| 3.6 | Public archives visible to all | ☐ |
| 4.1 | Discuss menu hidden | ☐ |
| 4.2 | Apps menu hidden | ☐ |
| 4.3 | Other menus still work | ☐ |
| 5.1 | User dropdown simplified | ☐ |
| 6.1 | Member form — no chatter | ☐ |
| 6.2 | Project form — no chatter | ☐ |
| 6.3 | Task form — no chatter, audit trail stays | ☐ |
| 6.4 | Internal notifications still work | ☐ |
| 7.1 | Task creation happy path | ☐ |
| 7.2 | Overlapping time blocked | ☐ |
| 7.3 | Full approval workflow cycle | ☐ |
| 7.4 | PM visibility scoped to managed projects | ☐ |
| 7.5 | Project status effects | ☐ |
| 7.6 | Past date limit enforced | ☐ |
| 7.7 | Removed member behavior | ☐ |
| 7.8 | Admin-only settings | ☐ |
| 8.1 | Member dashboard loads | ☐ |
| 8.2 | PM dashboard loads | ☐ |
| 8.3 | Admin dashboard loads | ☐ |
