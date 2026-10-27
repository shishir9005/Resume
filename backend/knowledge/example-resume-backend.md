# Example Resume: Backend Engineering Intern

**Lin Wei**
Shanghai, China | lin.wei@example.com | +86 138-0000-0001 | github.com/linwei-dev | linkedin.com/in/linwei-dev

## Summary
Computer science junior focused on backend development with Python and Go. Built and deployed a FastAPI service used by 600+ students on campus. Seeking a summer 2026 backend engineering internship.

## Education
**B.Eng. in Computer Science and Technology** | Example University of Technology | Sep 2023 – Jun 2027 (expected)
- GPA 3.7/4.0, top 10% of 240 students
- Relevant courses: Data Structures, Databases, Operating Systems, Computer Networks

## Projects
**Campus Canteen Ordering API** | Python, FastAPI, PostgreSQL, Redis, Docker | github.com/linwei-dev/canteen-api
- Built a REST API for pre-ordering canteen meals, used by 600+ students during a 4-week pilot
- Designed a PostgreSQL schema of 11 tables with indexes on order lookups, cutting the slowest query from 900 ms to 40 ms
- Added Redis caching for menu endpoints, reducing average response time by 65% at peak lunch hours
- Containerized the service with Docker and deployed it on a 2 GB Linux cloud server with GitHub Actions CI/CD
- Wrote 85 Pytest unit tests, raising coverage from 40% to 88%

**Distributed Key-Value Store** | Go, gRPC, Raft | github.com/linwei-dev/kvstore
- Implemented a 3-node key-value store with Raft leader election and log replication in 3,000 lines of Go
- Benchmarked 12K writes per second on a single machine and survived the loss of any 1 node without data loss

## Experience
**Teaching Assistant, Database Systems** | Example University of Technology | Sep 2024 – Jan 2025
- Led weekly MySQL labs for 45 students and reviewed 120 assignments on schema design and query optimization
- Created 6 practice problems on joins and indexing that were added to the official course materials

## Skills
- Languages: Python, Go, SQL
- Backend: FastAPI, REST API, gRPC, PostgreSQL, MySQL, Redis
- Tools: Git, Docker, Linux, GitHub Actions, Pytest
- Languages spoken: Chinese (native), English (fluent, IELTS 7.5)
