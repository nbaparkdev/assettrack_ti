# Implementation Plan - Kanban Notifications (Real-time & Dashboard)

Implement a real-time notification system for Kanban projects, notifying users when they are added to a project, assigned to cards, when cards move between columns, and when attachments are added. The system includes DB persistence, a global Header Bell widget, and a Dashboard widget.

## User Requirements Confirmed
1. **Scope of Events**: User added to project, card assignment, card movement between columns, and new attachments.
2. **Persistence & Real-time**: Hybrid model (Database storage + real-time polling every 10s).
3. **UI Display**: Global Header Bell dropdown on all pages + Dashboard (`/dashboard`) widget.

## Proposed Changes

### 1. Database Model
- Add `KanbanNotification` model in `app/models/kanban.py`.
- Includes fields: `id`, `user_id`, `project_id`, `card_id`, `autor_id`, `tipo`, `titulo`, `mensagem`, `link`, `lida`, `created_at`.

### 2. Notification Service
- Create `app/services/kanban_notification_service.py` with helper methods:
  - `notify_users_added_to_project`
  - `notify_card_assigned`
  - `notify_card_moved`
  - `notify_attachment_added`

### 3. API & Web Endpoints
- Add notification routes in `app/web/endpoints/kanban.py`:
  - `GET /kanban/notifications/unread-count` (JSON)
  - `GET /kanban/notifications/list` (HTML/JSON)
  - `POST /kanban/notifications/{id}/read`
  - `POST /kanban/notifications/read-all`
- Hook notification triggers into project creation/update, card creation/assignment/movement, and attachment upload routes.

### 4. UI Components
- Update `app/templates/base.html`:
  - Header bell icon with badge count.
  - Dropdown menu showing unread and recent Kanban notifications.
  - Polling JavaScript script (every 10s).
- Update `app/templates/dashboard.html`:
  - Kanban project notifications & progress widget.

## Verification Plan
1. Run python syntax compilation check.
2. Execute existing test suite with `pytest`.
3. Create test cases for Kanban notifications.
