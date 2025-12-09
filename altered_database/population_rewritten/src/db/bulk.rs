use anyhow::{Context, Result};
use bytes::Bytes;
use futures::{stream, SinkExt};
use serde::Serialize;
use tokio_postgres::{Client, CopyInSink};

pub struct BulkInserter<'a> {
    client: &'a Client,
}

impl<'a> BulkInserter<'a> {
    pub fn new(client: &'a Client) -> Self {
        Self { client }
    }

    /// Generic insert using COPY protocol via CSV format.
    /// T must implement Serialize.
    pub async fn insert<T>(&self, table_name: &str, columns: &[&str], data: &[T]) -> Result<()>
    where
        T: Serialize + Send + Sync,
    {
        if data.is_empty() {
            return Ok(());
        }

        let col_string = columns.join(", ");
        // Important: Specify FORMAT CSV to match the serializer output
        let query = format!(
            "COPY {} ({}) FROM STDIN (FORMAT CSV)",
            table_name, col_string
        );

        // Explicitly type the sink to fix compiler inference error
        let sink: CopyInSink<Bytes> = self
            .client
            .copy_in(&query)
            .await
            .context("Failed to prepare COPY statement")?;

        // We use a pin-boxed sink writer
        let mut writer = Box::pin(sink);

        // Serialize data to CSV buffer in chunks to avoid massive RAM spikes
        let mut wtr = csv::WriterBuilder::new()
            .has_headers(false)
            .from_writer(Vec::new());

        for row in data {
            wtr.serialize(row)
                .context("Failed to serialize row to CSV")?;
        }

        let csv_bytes = wtr.into_inner().context("Failed to flush CSV buffer")?;

        // Convert to Bytes and send
        writer
            .send(Bytes::from(csv_bytes))
            .await
            .context("Failed to send data to PG sink")?;

        // Close the sink to commit transaction
        writer.close().await.context("Failed to close COPY sink")?;

        Ok(())
    }
}
