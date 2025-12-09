use crate::config::Config;
use crate::models::{DbMatch, DbSwipe};
use chrono::Utc;
use rand::prelude::*;
use rayon::prelude::*;
use std::collections::{HashMap, HashSet};
use std::sync::{Arc, Mutex};

pub struct InteractionData {
    pub swipes: Vec<DbSwipe>,
    pub matches: Vec<DbMatch>,
}

/// Simulation Logic:
/// 1. Each user swipes N times on random other users.
/// 2. If User A right-swipes B, and B has already right-swiped A, a Match is formed.
pub fn generate_interactions(user_ids: &[i32], config: &Config) -> InteractionData {
    // Config parameters
    let max_swipes = config.max_user_swipes;
    let right_swipe_prob = config.right_swipe_ratio / 100.0;

    // Thread-safe storage for results
    // We use a Map to store "Received Right Swipes" to detect matches: TargetID -> Set<SenderID>
    let likes_received: Arc<Mutex<HashMap<i32, HashSet<i32>>>> =
        Arc::new(Mutex::new(HashMap::new()));

    let swipes: Vec<DbSwipe> = user_ids
        .par_iter()
        .map(|&actor_id| {
            let mut rng = rand::thread_rng();
            let num_swipes = rng.gen_range(0..=max_swipes);
            let mut local_swipes = Vec::with_capacity(num_swipes);

            // Simple strategy: pick random targets
            // Optimization: In a real graph, we'd pick by geo/score. Here, random sampling.
            for _ in 0..num_swipes {
                let target_idx = rng.gen_range(0..user_ids.len());
                let target_id = user_ids[target_idx];

                if target_id == actor_id {
                    continue;
                }

                let is_right_swipe = rng.gen_bool(right_swipe_prob);

                // Record the swipe
                local_swipes.push(DbSwipe {
                    result: is_right_swipe,
                    fk_swiping_user_details_id: actor_id,
                    fk_swiped_user_details_id: target_id,
                    swipe_time: Utc::now().naive_utc(),
                });

                // If right swipe, register interest for match checking
                if is_right_swipe {
                    let mut guard = likes_received.lock().unwrap();
                    guard.entry(target_id).or_default().insert(actor_id);
                }
            }
            local_swipes
        })
        .flatten()
        .collect();

    // MATCH GENERATION PHASE
    // Iterate through the likes map to find mutuals.
    // A Match exists if A is in likes_received[B] AND B is in likes_received[A]
    // To avoid duplicates (A-B and B-A), we only store if A < B.

    let likes_map = likes_received.lock().unwrap();
    let mut matches = Vec::new();

    for (&recipient, senders) in likes_map.iter() {
        for &sender in senders {
            // Check for mutual like
            if let Some(recipient_likes) = likes_map.get(&sender) {
                if recipient_likes.contains(&recipient) {
                    // Mutual found. Enforce order to prevent duplicates
                    if sender < recipient {
                        matches.push(DbMatch {
                            fk_person1_id: sender,
                            fk_person2_id: recipient,
                            date_formed: Utc::now().naive_utc(),
                            status: "active".to_string(),
                        });
                    }
                }
            }
        }
    }

    InteractionData { swipes, matches }
}
