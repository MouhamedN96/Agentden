use anyhow::Result;

#[derive(Debug, Default)]
pub struct TaskJournal;

impl TaskJournal {
    pub fn append_jsonl(&self, _line: &str) -> Result<()> {
        Ok(())
    }
}
