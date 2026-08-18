# Emergency Alert Feature (Botão Emergencial)

> Historical implementation note. It documents the original rollout in the previous stack and may mention Python files, template paths and legacy endpoint names.

## Goal
Implement a real-time emergency alert system with a high-visibility red button on the common user dashboard, allowing users to send alerts with a reason, saving the alert to the DB and broadcasting a real-time popup modal to Administrators, Technicians, and Managers containing the user's name, sector, assigned active asset(s), and reason text.

## Tasks
- [x] Task 1: Create `EmergencyAlert` model in `app/models/emergency_alert.py` and register in `app/models/__init__.py` → Verify: DB table `emergency_alerts` is created properly.
- [x] Task 2: Create real-time broadcaster (SSE / WebSockets event manager) in `app/services/alert_broadcaster.py` to stream alerts to connected staff sessions.
- [x] Task 3: Create backend endpoints in `app/web/endpoints/alerts.py` (`POST /emergencia/alertar` to save and broadcast alert, `GET /emergencia/stream` for SSE real-time listener) and register router in `app/web/__init__.py`.
- [x] Task 4: Add the Emergency Button & Modal to the Common User Dashboard in `app/templates/dashboard.html` adhering to current industrial/brutalist design guidelines.
- [x] Task 5: Add global real-time SSE event listener and Emergency Alert Modal to `app/templates/base.html` for staff users (Admins, Technicians, Managers) to receive real-time popup modals.
- [x] Task 6: Test end-to-end flow with tests or manual verification via python scripts/curl → Verify: Alert submission triggers modal popup with complete user, sector, asset, and reason details.

## Done When
- [x] Common users see a red emergency button on the dashboard.
- [x] Clicking the button opens a modal asking "Por qual motivo?" with an input field, "Enviar", and "Cancelar" buttons.
- [x] Submitting the alert stores the alert in DB and broadcasts in real-time.
- [x] Admins, Technicians, and Managers see an immediate real-time modal popup containing User Name, Sector, Active Asset, and Reason text.
