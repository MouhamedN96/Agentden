use chrono::{DateTime, Utc};

#[derive(Debug, Clone)]
pub struct ScheduledJob {
    pub name: String,
    pub next_run_at: DateTime<Utc>,
}
