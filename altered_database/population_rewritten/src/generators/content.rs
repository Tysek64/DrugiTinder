use crate::config::Config;
use crate::models::*;
use chrono::{Duration, Utc};
use fake::faker::address::en::{StreetName, ZipCode};
use fake::faker::lorem::en::Sentence;
use fake::Fake;
use rand::Rng;
use rayon::prelude::*;

/// Generates Subscriptions + Billing dependencies
pub fn generate_subscription_chain(
    count: usize,
    city_ids: &[i32],
    _plan_ids: &[i32], // Unused in this placeholder function
    _config: &Config,  // Unused
) -> (
    Vec<DbBillingAddress>,
    Vec<DbPaymentData>,
    Vec<DbSubscription>,
) {
    let mut rng = rand::thread_rng();

    // Note: This function currently just serves as a generator for Main to consume,
    // but the actual Main.rs re-implements the logic to handle ID linking properly.
    // We generate dummy billing addresses here just to show we can.
    let _billing: Vec<DbBillingAddress> = (0..count)
        .map(|_| DbBillingAddress {
            street: StreetName().fake(),
            postal_code: ZipCode().fake(),
            fk_city_id: city_ids[rng.gen_range(0..city_ids.len())],
        })
        .collect();

    (vec![], vec![], vec![])
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

pub fn generate_search_pref_sex(pref_ids: &[i32], sex_ids: &[i32]) -> Vec<DbSearchPreferenceSex> {
    pref_ids
        .par_iter()
        .flat_map(|&pid| {
            let mut rng = rand::thread_rng();
            let mut rows = Vec::new();

            let num_picks = rng.gen_range(1..=2).min(sex_ids.len());
            let mut chosen_indices: Vec<usize> = (0..sex_ids.len()).collect();
            for i in 0..num_picks {
                let j = rng.gen_range(i..chosen_indices.len());
                chosen_indices.swap(i, j);

                rows.push(DbSearchPreferenceSex {
                    fk_search_preference_id: pid,
                    fk_sex_id: sex_ids[chosen_indices[i]],
                    priorty: Some(rng.gen_range(1..5)),
                });
            }
            rows
        })
        .collect()
}

pub fn generate_search_pref_interests(
    pref_ids: &[i32],
    interest_ids: &[i32],
) -> Vec<DbSearchPreferenceInterest> {
    pref_ids
        .par_iter()
        .flat_map(|&pid| {
            let mut rng = rand::thread_rng();
            let count = rng.gen_range(1..5);
            let mut rows = Vec::new();

            for _ in 0..count {
                rows.push(DbSearchPreferenceInterest {
                    fk_search_preference_id: pid,
                    fk_interest_id: interest_ids[rng.gen_range(0..interest_ids.len())],
                    level_of_interest: Some(rng.gen_range(1..10)),
                    is_positive: Some(rng.gen_bool(0.8)),
                });
            }
            rows
        })
        .collect()
}

pub fn generate_images(user_detail_ids: &[i32], _config: &Config) -> Vec<DbImage> {
    user_detail_ids
        .par_iter()
        .flat_map(|&uid| {
            let mut rng = rand::thread_rng();
            let count = rng.gen_range(1..6);
            let mut images = Vec::new();

            for i in 0..count {
                let is_current = i == 0;
                let size = rng.gen_range(50_000..5_000_000);

                images.push(DbImage {
                    file_path: format!("s3://bucket/user_{}/{}.jpg", uid, rng.gen::<u32>()),
                    uploaded_at: Utc::now().naive_utc() - Duration::days(rng.gen_range(0..365)),
                    is_current,
                    file_size_bytes: size,
                    is_verified: rng.gen_bool(0.7),
                    fk_user_details_id: uid,
                });
            }
            images
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

            for _ in 0..num_interests {
                let iid = interest_ids[rng.gen_range(0..interest_ids.len())];
                selected.push(DbUserInterest {
                    level_of_interest: rng.gen_range(1..=10),
                    is_positive: rng.gen_bool(0.9),
                    fk_user_details_id: uid,
                    fk_interest_id: iid,
                });
            }
            selected
        })
        .collect()
}
