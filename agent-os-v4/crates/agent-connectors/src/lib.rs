use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GitHubIssueRef {
    pub number: u64,
    pub title: String,
}
