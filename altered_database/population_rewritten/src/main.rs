mod config;
mod db;
mod generators;
mod models;

use crate::config::Config;
use crate::db::{bulk::BulkInserter, create_pool};
use anyhow::Result;
use indicatif::ProgressBar;

#[tokio::main]
async fn main() -> Result<()> {
    println!(">>> Tinder 2.0 Optimizer Starting...");

    let config = Config::load("config.yml")?;
    println!(">>> Config loaded. Target Users: {}", config.users_number);

    let pool = create_pool(&config);
    let mut client = pool.get().await?;

    // 1. Static Data
    generators::static_data::populate_static_data(&client).await?;

    let batch_size = 500;
    let total_batches = (config.users_number + batch_size - 1) / batch_size;
    let pb = ProgressBar::new(config.users_number as u64);

    // We need to collect ALL user IDs to generate interactions later
    let mut all_user_ids: Vec<i32> = Vec::with_capacity(config.users_number);

    println!(">>> Generating Users...");
    for _ in 0..total_batches {
        // A. Generate Auth (CPU)
        let users =
            tokio::task::spawn_blocking(move || generators::users::generate_user_batch(batch_size))
                .await?;

        // B. Insert Auth (IO)
        let stmt = client
            .prepare(
                "
            INSERT INTO \"user\" (username, email, password_hash, created_at)
            SELECT * FROM UNNEST($1::text[], $2::text[], $3::text[], $4::timestamp[])
            RETURNING id
        ",
            )
            .await?;

        let usernames: Vec<&str> = users.iter().map(|u| u.username.as_str()).collect();
        let emails: Vec<&str> = users.iter().map(|u| u.email.as_str()).collect();
        let hashes: Vec<&str> = users.iter().map(|u| u.password_hash.as_str()).collect();
        let dates: Vec<chrono::NaiveDateTime> = users.iter().map(|u| u.created_at).collect();

        let rows = client
            .query(&stmt, &[&usernames, &emails, &hashes, &dates])
            .await?;
        let user_ids: Vec<i32> = rows.iter().map(|r| r.get(0)).collect();

        // Save IDs for next steps
        all_user_ids.extend_from_slice(&user_ids);

        // C. Generate Details (CPU)
        let cfg_clone = config.clone();
        let uids_clone = user_ids.clone();
        let details_batch = tokio::task::spawn_blocking(move || {
            generators::users::generate_details_batch(uids_clone, &cfg_clone)
        })
        .await?;

        // D. Insert Details (IO)
        let bulk = BulkInserter::new(&client);
        bulk.insert(
            "user_details",
            &[
                "name",
                "surname",
                "fk_sex_id",
                "fk_city_id",
                "fk_subscription_id",
                "fk_search_preference_id",
                "fk_user_id",
                "created_at",
            ],
            &details_batch,
        )
        .await?;

        pb.inc(rows.len() as u64);
    }
    pb.finish_with_message("Users Done");

    // 2. Interaction Generation (Swipes & Matches)
    println!(">>> Generating Interactions (Swipes & Matches)...");

    // Cloning for thread safety in spawn_blocking
    let cfg_clone = config.clone();
    let uids_clone = all_user_ids.clone(); // Moving full ID set

    let interactions = tokio::task::spawn_blocking(move || {
        generators::interactions::generate_interactions(&uids_clone, &cfg_clone)
    })
    .await?;

    println!(">>> Inserting {} Swipes...", interactions.swipes.len());
    let bulk = BulkInserter::new(&client);

    // Insert Swipes
    // Note: Breaking into chunks might be necessary for massive datasets (postgres parameter limits),
    // but COPY handles millions of rows fine in one go.
    bulk.insert(
        "swipe",
        &[
            "result",
            "fk_swiping_user_details_id",
            "fk_swiped_user_details_id",
            "swipe_time",
        ],
        &interactions.swipes,
    )
    .await?;

    println!(">>> Inserting {} Matches...", interactions.matches.len());
    // Insert Matches
    bulk.insert(
        "match",
        &["fk_person1_id", "fk_person2_id", "date_formed", "status"],
        &interactions.matches,
    )
    .await?;

    println!(">>> Population Complete.");
    Ok(())
}
