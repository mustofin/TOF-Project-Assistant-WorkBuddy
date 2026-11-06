# Project Template — Web Application Development

> Template untuk project pengembangan web application.
> Gunakan sebagai starting point untuk Planner.

## Standard Phases

### Fase 1: Core Architecture & Authentication
- Setup project structure (frontend + backend)
- Database schema setup
- Authentication system
- Base routing/navigation

### Fase 2: Core Features — Data Management
- CRUD operations untuk entity utama
- List views dengan pagination/filter
- Form validation
- Error handling

### Fase 3: Core Features — Business Logic
- Business workflow implementation
- Integration antar modul
- Calculation/processing logic
- Notification system (jika ada)

### Fase 4: UI/UX Polish
- Responsive design
- Loading states & error boundaries
- User feedback (toast, modal, dll)
- Accessibility check

### Fase 5: Testing & QA
- Unit testing
- Integration testing
- End-to-end (UAT)
- Bug fixing

### Fase 6: Deployment & Documentation
- Production deployment
- Documentation (user guide, technical doc)
- Knowledge transfer
- Go-live

## Task Priority Guide

| Priority | Meaning | Example |
|----------|---------|---------|
| P0 - Kritis | Blocking, harus selesai untuk project jalan | Database setup, auth, core CRUD |
| P1 - Tinggi | Penting untuk MVP | Business logic, main UI |
| P2 - Menengah | Nice to have untuk v1 | Dashboard, reports, polish |
| P3 - Finalisasi | Post-MVP atau finishing | QA, deployment, documentation |

## Effort Estimation Guide

| Task Complexity | Estimasi Hari | Contoh |
|------------------|---------------|--------|
| Simple | 0.5 - 1 | Form CRUD sederhana, static page |
| Medium | 1 - 2 | Feature dengan business logic, integration |
| Complex | 2 - 4 | Multi-entity workflow, real-time feature |
| Very Complex | 4 - 7 | Full module dengan 5+ entities |

## Dependency Patterns

- Auth → selalu pertama (semua feature butuh auth)
- Database schema → sebelum CRUD
- Backend API → sebelum frontend yang consume
- Core CRUD → sebelum business logic
- Business logic → sebelum UI polish
- All features → sebelum QA
- QA → sebelum deployment
