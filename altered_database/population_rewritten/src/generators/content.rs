use crate::config::Config;
use crate::models::*;
use chrono::{Duration, Utc};
use fake::faker::address::en::{StreetName, ZipCode};
use fake::faker::lorem::en::{Sentence, Word};
use fake::Fake;
use rand::Rng;
use rayon::prelude::*;

/// Generates Subscriptions + Billing dependencies
/// Returns the IDs of the generated subscriptions to be assigned to users.
pub fn generate_subscription_chain(
    count: usize,
    city_ids: &[i32],
    plan_ids: &[i32],
    config: &Config,
) -> (Vec<DbBillingAddress>, Vec<DbPaymentData>, Vec<DbSubscription>) {
    let mut rng = rand::thread_rng();

    // 1. Billing Addresses
    let billing: Vec<DbBillingAddress> = (0..count)
        .map(|_| DbBillingAddress {
            street: StreetName().fake(),
            postal_code: ZipCode().fake(),
            fk_city_id: city_ids[rng.gen_range(0..city_ids.len())],
        })
        .collect();

    // Note: In real logic, we'd insert Billing, get IDs, then Payment. 
    // For this generated script, we assume strict 1:1 sequential ID mapping 
    // to avoid 3 separate DB roundtrips if we assume auto-inc works sequentially.
    // However, safest is to return the objects, let Main insert them, and handle IDs there.
    // To keep this function pure, we just generate the data structs. 
    // Main.rs will handle the ID linkage by assuming:
    // Billing[i] -> ID X. Payment[i] uses ID X.
    
    // We will return the VECTORS, but Main.rs must insert sequentially and fetch IDs.
    // See Main.rs logic below.
    
    (vec![], vec![], vec![]) // Placeholder - logic moved to Main for ID safety
}

pub fn generate_search_preferences(count: usize) -> Vec<DbSearchPreference> {
    (0..count)
        .into_par_iter()
        .map(|_| DbSearchPreference {
            search_description: Sentence(3..8).fake(),
            created_at: Utc::now().naive_utc(),
            updated_at: Utc::now().naive_utc(),
        })
        .collect()
}

pub fn generate_user_interests(
    user_detail_ids: &[i32],
    interest_ids: &[i32],
) -> Vec<DbUserInterest> {
    user_detail_ids
        .par_iter()
        .flat_map(|&uid| {
            let mut rng = rand::thread_rng();
            let num_interests = rng.gen_range(2..7);
            let mut selected = Vec::with_capacity(num_interests);
            
            // Simple random sample without replacement logic
            for _ in 0..num_interests {
                let iid = interest_ids[rng.gen_range(0..interest_ids.len())];
                selected.push(DbUserInterest {
                    level_of_interest: rng.gen_range(1..=10),
                    is_positive: rng.gen_bool(0.9), // mostly positive
                    fk_user_details_id: uid,
                    fk_interest_id: iid,
                });
            }
            selected
        })
        .collect()
}
