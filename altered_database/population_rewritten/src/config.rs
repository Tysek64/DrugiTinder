use serde::Deserialize;
use std::fs;
use anyhow::Result;

#[derive(Debug, Deserialize, Clone)]
pub struct Config {
    pub database_name: String,
    pub username: String,
    pub users_number: usize,
    pub admins_number: usize,
    pub enable_locale: bool,
    pub migration_ratio: f64,
    pub domestic_migration_ratio: f64,
    pub international_migration_ratio: f64,
    pub oldest_current_photo: i64,
    pub oldest_unverified_photo: i64,
    pub subscription_ratio: f64,
    pub auto_renewal_ratio: f64,
    pub max_admin_hiring_difference: i64,
    pub user_report_ratio: f64,
    pub report_ban_ratio: f64,
    pub max_report_ban_difference: i64,
    pub min_ban_length: i64,
    pub max_ban_length: i64,
    pub max_user_swipes: usize,
    pub right_swipe_ratio: f64,
    pub match_probability: f64, // Note: Config says 1000? Assuming basis points (0-10000) or raw percent?
    pub match_block_ratio: f64,
    pub max_match_block_difference: i64,
    pub user_block_ratio: f64,
    pub min_block_length: i64,
    pub max_block_length: i64,
    pub max_conversation_length: usize,
    pub reply_ratio: f64,
}

impl Config {
    pub fn load(path: &str) -> Result<Self> {
        let contents = fs::read_to_string(path)?;
        let config: Config = serde_yaml::from_str(&contents)?;
        Ok(config)
    }
}
