use crate::config::Config;
use crate::models::*;
use chrono::{Duration, NaiveDateTime, Utc}; // Added NaiveDateTime
use fake::faker::lorem::en::Sentence;
use fake::Fake;
use rand::Rng;
use rayon::prelude::*;
// Removed unused HashSet import

pub fn generate_admins(user_ids: &[i32]) -> Vec<DbAdministrator> {
    user_ids
        .par_iter()
        .map(|&uid| {
            let mut rng = rand::thread_rng();
            DbAdministrator {
                fk_user_id: uid,
                hiring_date: Utc::now().naive_utc() - Duration::days(rng.gen_range(100..2000)),
                reports_handled: rng.gen_range(0..500),
            }
        })
        .collect()
}

// Fixed version that takes ID tuples
pub fn generate_chat_flow(
    match_data: &[(i32, i32, i32)], // (id, p1, p2)
    _config: &Config,               // Prefixed _ to silence unused
) -> (Vec<DbConversation>, Vec<DbMessage>) {
    let mut rng = rand::thread_rng();
    let mut conversations = Vec::new();
    let messages = Vec::new(); // Removed mut as it was unused in this scope

    for &(match_id, _p1, _p2) in match_data {
        // Prefixed _p1, _p2
        if !rng.gen_bool(0.6) {
            continue;
        } // 60% of matches talk

        // Conversation
        conversations.push(DbConversation {
            fk_match_id: match_id,
            chat_theme: "General".to_string(),
            chat_reaction: 0,
            created_at: Utc::now().naive_utc(),
            updated_at: Utc::now().naive_utc(),
        });
    }

    (conversations, messages)
}

pub fn generate_messages_for_convos(
    convo_data: &[(i32, i32, i32)], // (ConvoID, Person1, Person2)
    config: &Config,
) -> Vec<DbMessage> {
    let mut messages = Vec::new();
    let mut rng = rand::thread_rng();

    for &(cid, p1, p2) in convo_data {
        let count = rng.gen_range(1..config.max_conversation_length);
        let mut time = Utc::now().naive_utc() - Duration::days(10);

        for i in 0..count {
            let sender = if i % 2 == 0 { p1 } else { p2 };
            time = time + Duration::minutes(rng.gen_range(1..60));

            messages.push(DbMessage {
                send_time: time,
                contents: Sentence(1..10).fake(),
                reaction: None,
                fk_sender_id: Some(sender),
                fk_conversation_id: cid,
                fk_replying_to_message_id: None,
            });
        }
    }
    messages
}

/// Generates Reports.
pub fn generate_reports(user_ids: &[i32], admin_ids: &[i32], config: &Config) -> Vec<DbReport> {
    let report_count = (user_ids.len() as f64 * (config.user_report_ratio / 100.0)) as usize;
    if report_count == 0 {
        return vec![];
    }

    (0..report_count)
        .into_par_iter()
        .map(|_| {
            let mut rng = rand::thread_rng();

            let reporter = user_ids[rng.gen_range(0..user_ids.len())];
            let mut reported = user_ids[rng.gen_range(0..user_ids.len())];

            while reported == reporter {
                reported = user_ids[rng.gen_range(0..user_ids.len())];
            }

            let admin = if !admin_ids.is_empty() {
                Some(admin_ids[rng.gen_range(0..admin_ids.len())])
            } else {
                None
            };

            DbReport {
                reason: Sentence(3..10).fake(),
                report_date: Utc::now().naive_utc() - Duration::days(rng.gen_range(0..30)),
                fk_reporting_user_details_id: reporter,
                fk_reported_user_details_id: reported,
                fk_administrator_id: admin,
            }
        })
        .collect()
}

pub struct ReportMeta {
    pub id: i32,
    pub reported_user_id: i32,
    pub report_date: NaiveDateTime,
}

pub fn generate_bans(reports: &[ReportMeta], config: &Config) -> Vec<DbBan> {
    reports
        .iter()
        .filter_map(|r| {
            let mut rng = rand::thread_rng();

            if rng.gen_bool(config.report_ban_ratio / 100.0) {
                let ban_len = rng.gen_range(config.min_ban_length..=config.max_ban_length);

                Some(DbBan {
                    fk_user_details_id: r.reported_user_id,
                    fk_report_id: r.id,
                    start_date: r.report_date + Duration::hours(rng.gen_range(1..48)),
                    period_days: ban_len as i32,
                    is_active: true,
                })
            } else {
                None
            }
        })
        .collect()
}

pub fn generate_blocks(
    user_ids: &[i32],
    match_pairs: &[(i32, i32)],
    config: &Config,
) -> Vec<DbBlock> {
    let mut blocks = Vec::new();
    let mut rng = rand::thread_rng();

    // 1. Match Blocks
    for &(p1, p2) in match_pairs {
        if rng.gen_bool(config.match_block_ratio / 100.0) {
            let (blocker, blocked) = if rng.gen_bool(0.5) {
                (p1, p2)
            } else {
                (p2, p1)
            };

            blocks.push(DbBlock {
                fk_blocking_user_details_id: blocker,
                fk_blocked_user_details_id: blocked,
                start_date: Utc::now().naive_utc(),
                end_date: None,
                is_active: true,
            });
        }
    }

    // 2. Random Blocks
    let random_block_count = (user_ids.len() as f64 * (config.user_block_ratio / 100.0)) as usize;
    for _ in 0..random_block_count {
        let blocker = user_ids[rng.gen_range(0..user_ids.len())];
        let mut blocked = user_ids[rng.gen_range(0..user_ids.len())];
        while blocked == blocker {
            blocked = user_ids[rng.gen_range(0..user_ids.len())];
        }

        blocks.push(DbBlock {
            fk_blocking_user_details_id: blocker,
            fk_blocked_user_details_id: blocked,
            start_date: Utc::now().naive_utc(),
            end_date: None,
            is_active: true,
        });
    }

    blocks
}
