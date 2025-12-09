use crate::config::Config;
use crate::models::*;
use chrono::{Duration, Utc};
use fake::faker::lorem::en::Sentence;
use fake::Fake;
use rand::Rng;
use rayon::prelude::*;

pub fn generate_admins(user_ids: &[i32]) -> Vec<DbAdministrator> {
    user_ids.par_iter().map(|&uid| {
        let mut rng = rand::thread_rng();
        DbAdministrator {
            fk_user_id: uid,
            hiring_date: Utc::now().naive_utc() - Duration::days(rng.gen_range(100..2000)),
            reports_handled: rng.gen_range(0..500),
        }
    }).collect()
}

pub fn generate_conversations_and_messages(
    matches: &[DbMatch],
    config: &Config,
) -> (Vec<DbConversation>, Vec<DbMessage>) {
    // 1. Filter matches that actually talk
    let active_matches: Vec<&DbMatch> = matches.iter()
        .filter(|_| rand::thread_rng().gen_bool(config.reply_ratio / 100.0)) // reusing reply_ratio as conversation_start_ratio
        .collect();

    let mut conversations = Vec::with_capacity(active_matches.len());
    let mut messages = Vec::new();

    // We can't easily parallelize *generation* into two vectors without a fold, 
    // keeping it sequential is fast enough for 10k items.
    
    // We assume matches are already inserted and have IDs? 
    // Actually, DbMatch struct in main might not have ID populated if we just bulk inserted.
    // **CRITICAL**: We need Match IDs to create Conversations.
    // *Fix*: This generator assumes the `matches` slice has valid IDs (fetched from DB).
    
    // Since our DbMatch struct doesn't have an `id` field in models.rs (it wasn't in your snippet),
    // we assume the caller passes a tuple `(MatchID, Person1ID, Person2ID)`.
    
    // Placeholder return
    (conversations, messages)
}

// Fixed version that takes ID tuples
pub fn generate_chat_flow(
    match_data: &[(i32, i32, i32)], // (id, p1, p2)
    config: &Config,
) -> (Vec<DbConversation>, Vec<DbMessage>) {
    let mut rng = rand::thread_rng();
    let mut conversations = Vec::new();
    let mut messages = Vec::new();

    for &(match_id, p1, p2) in match_data {
        if !rng.gen_bool(0.6) { continue; } // 60% of matches talk

        // Conversation
        conversations.push(DbConversation {
            fk_match_id: match_id,
            chat_theme: "General".to_string(),
            chat_reaction: 0,
            created_at: Utc::now().naive_utc(),
            updated_at: Utc::now().naive_utc(),
        });

        // We can't generate messages here easily because we need the Conversation ID 
        // which isn't generated until insert.
        // **Strategy**: We will insert Conversations in Main, get IDs, then generate Messages.
    }
    
    (conversations, messages)
}

pub fn generate_messages_for_convos(
    convo_data: &[(i32, i32, i32)], // (ConvoID, Person1, Person2)
    config: &Config
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
                fk_replying_to_message_id: None, // Simplified: no threaded replies
            });
        }
    }
    messages
}
