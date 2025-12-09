use crate::config::Config;
use crate::models::{DbUser, DbUserDetails};
use bcrypt::hash;
use chrono::{Duration, Utc};
use fake::faker::internet::en::Username;
use fake::faker::name::en::{FirstName, LastName};
use fake::Fake;
use rand::Rng;

pub fn generate_user_batch(size: usize) -> Vec<DbUser> {
    use rayon::prelude::*;
    (0..size)
        .into_par_iter()
        .map(|_| {
            let mut rng = rand::thread_rng();
            let days_ago = rng.gen_range(0..1000);
            let created_at = Utc::now().naive_utc() - Duration::days(days_ago);
            let password_hash = hash("password123", 4).unwrap();

            let base_name: String = Username().fake();
            let suffix: u32 = rng.gen_range(100_000..999_999);
            let clean_base = base_name.replace(|c: char| !c.is_alphanumeric(), "");
            let unique_username = format!("{}{}", clean_base, suffix);
            let unique_email = format!("{}@example.com", unique_username);

            DbUser {
                id: None,
                username: unique_username,
                email: unique_email,
                password_hash,
                created_at,
            }
        })
        .collect()
}

pub fn generate_details_batch(
    user_ids: Vec<i32>,
    _config: &Config,
    available_sub_ids: &[i32],
    available_pref_ids: &[i32],
) -> Vec<DbUserDetails> {
    let mut results = Vec::with_capacity(user_ids.len());
    let mut rng = rand::thread_rng();

    for uid in user_ids {
        // Correctly using the arguments now
        let sub_id = if !available_sub_ids.is_empty() && rng.gen_bool(0.1) {
            Some(available_sub_ids[rng.gen_range(0..available_sub_ids.len())])
        } else {
            None
        };

        let pref_id = if !available_pref_ids.is_empty() {
            Some(available_pref_ids[rng.gen_range(0..available_pref_ids.len())])
        } else {
            None
        };

        let city_id = if rng.gen_range(0..100) < 10 {
            None
        } else {
            Some(rng.gen_range(1..=50))
        };

        results.push(DbUserDetails {
            name: FirstName().fake(),
            surname: LastName().fake(),
            fk_sex_id: rng.gen_range(1..=2),
            fk_city_id: city_id,
            fk_subscription_id: sub_id,       // Used here!
            fk_search_preference_id: pref_id, // Used here!
            fk_user_id: uid,
            created_at: Utc::now().naive_utc(),
        });
    }
    results
}
