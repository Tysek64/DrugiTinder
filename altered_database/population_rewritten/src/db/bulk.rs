use anyhow::{Context, Result};
use bytes::Bytes;
use futures::SinkExt;
use serde::Serialize;
use tokio_postgres::{Client, CopyInSink};

pub struct BulkInserter<'a> {
    client: &'a Client,
}

impl<'a> BulkInserter<'a> {
    pub fn new(client: &'a Client) -> Self {
        Self { client }
    }

    pub async fn insert<T>(&self, table_name: &str, columns: &[&str], data: &[T]) -> Result<()>
    where
        T: Serialize + Send + Sync,
    {
        if data.is_empty() {
            return Ok(());
        }

        let col_string = columns.join(", ");
        let query = format!(
            "COPY {} ({}) FROM STDIN (FORMAT CSV)",
            table_name, col_string
        );

        let sink: CopyInSink<Bytes> = self
            .client
            .copy_in(&query)
            .await
            .context("Failed to prepare COPY statement")?;

        let mut writer = Box::pin(sink);

        let mut wtr = csv::WriterBuilder::new()
            .has_headers(false)
            .from_writer(Vec::new());

        for row in data {
            wtr.serialize(row)
                .context("Failed to serialize row to CSV")?;
        }

        let csv_bytes = wtr.into_inner().context("Failed to flush CSV buffer")?;

        writer
            .send(Bytes::from(csv_bytes))
            .await
            .context("Failed to send data to PG sink")?;
        writer.close().await.context("Failed to close COPY sink")?;

        Ok(())
    }
}
