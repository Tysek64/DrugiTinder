pub mod bulk;

use crate::config::Config;
use anyhow::{Context, Result};
use deadpool_postgres::{Manager, ManagerConfig, Pool, RecyclingMethod};
use tokio_postgres::NoTls;

pub fn create_pool(config: &Config) -> Pool {
    // Note: In a real app, don't hardcode env var fallback inside library code if config is passed,
    // but here we align with the provided shell script env vars.
    let mut pg_config = tokio_postgres::Config::new();

    // We expect these to be set by populate_rust.sh
    pg_config.host(&std::env::var("DB_HOST").unwrap_or("localhost".to_string()));
    pg_config.port(
        std::env::var("DB_PORT")
            .unwrap_or("5432".to_string())
            .parse()
            .unwrap(),
    );
    pg_config.user(&std::env::var("DB_USER").unwrap_or("postgres".to_string()));
    pg_config.password(&std::env::var("DB_PASS").unwrap_or("password".to_string()));
    pg_config.dbname(&std::env::var("DB_NAME").unwrap_or("pdb_demo".to_string()));

    let mgr_config = ManagerConfig {
        recycling_method: RecyclingMethod::Fast,
    };
    let mgr = Manager::from_config(pg_config, NoTls, mgr_config);
    Pool::builder(mgr).max_size(16).build().unwrap()
}
