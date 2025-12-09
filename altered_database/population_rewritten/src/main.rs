mod config;
mod db;
mod generators;
mod models;

use crate::config::Config;
use crate::db::{bulk::BulkInserter, create_pool};
use crate::models::{DbBillingAddress, DbPaymentData, DbSubscription};
use anyhow::Result;
use fake::faker::address::en::{StreetName, ZipCode};
use fake::Fake;
use indicatif::ProgressBar;
use rand::Rng;
use tokio_postgres::Client;

/// Helper to fetch all IDs from a table (used for distributing Foreign Keys)
async fn fetch_ids(client: &Client, table: &str) -> Result<Vec<i32>> {
    let rows = client
        .query(format!("SELECT id FROM {}", table).as_str(), &[])
        .await?;
    Ok(rows.iter().map(|r| r.get(0)).collect())
}

async fn truncate_database(client: &tokio_postgres::Client) -> anyhow::Result<()> {
    println!(">>> Cleaning up database...");
    // We use CASCADE to automatically wipe dependent tables (e.g., deleting 'user' deletes 'user_details')
    // RESTART IDENTITY resets the auto-increment counters to 1.
    client
        .batch_execute(
            "
        TRUNCATE TABLE 
            \"user\", 
            administrator, 
            subscription_plan, 
            city, 
            country, 
            sex, 
            interest,
            search_preference
        RESTART IDENTITY CASCADE;
    ",
        )
        .await?;
    println!(">>> Database cleaned.");
    Ok(())
}

#[tokio::main]
async fn main() -> Result<()> {
    println!(">>> Tinder 2.0 Optimizer Starting...");

    let config = Config::load("config.yml")?;
    println!(">>> Config loaded. Target Users: {}", config.users_number);

    let pool = create_pool(&config);
    let client = pool.get().await?;

    truncate_database(&client).await?;

    // =========================================================================
    // 1. STATIC DATA & CACHING
    // =========================================================================
    generators::static_data::populate_static_data(&client).await?;

    println!(">>> Caching Static IDs...");
    let city_ids = fetch_ids(&client, "city").await?;
    let plan_ids = fetch_ids(&client, "subscription_plan").await?;
    let interest_ids = fetch_ids(&client, "interest").await?;
    let sex_ids = fetch_ids(&client, "sex").await?; // Needed for User Gen AND Search Prefs

    // =========================================================================
    // 2. PRE-REQUISITES (Data that Users depend on)
    // =========================================================================
    println!(">>> Generating Pre-requisites (Preferences, Subscriptions)...");
    let bulk = BulkInserter::new(&client);

    // A. Search Preferences
    // We generate 100% of user count to ensure enough exist, though not all users need one
    let pref_rows = generators::content::generate_search_preferences(config.users_number);
    bulk.insert(
        "search_preference",
        &["search_description", "created_at", "updated_at"],
        &pref_rows,
    )
    .await?;
    let available_pref_ids = fetch_ids(&client, "search_preference").await?;

    // B. Subscriptions Chain (Billing -> Payment -> Subscription)
    // We calculate exactly how many subs we need based on the ratio
    let sub_count = (config.users_number as f64 * (config.subscription_ratio / 100.0)) as usize;

    if sub_count > 0 {
        let mut rng = rand::thread_rng();

        // B1. Billing Address
        let billing_rows: Vec<DbBillingAddress> = (0..sub_count)
            .map(|_| DbBillingAddress {
                street: StreetName().fake(),
                postal_code: ZipCode().fake(),
                fk_city_id: city_ids[rng.gen_range(0..city_ids.len())],
            })
            .collect();
        bulk.insert(
            "billing_address",
            &["street", "postal_code", "fk_city_id"],
            &billing_rows,
        )
        .await?;
        let bill_ids = fetch_ids(&client, "billing_address").await?;

        // B2. Payment Data
        let pay_rows: Vec<DbPaymentData> = bill_ids
            .iter()
            .map(|&bid| DbPaymentData {
                token: format!("tok_{}", rng.gen::<u64>()),
                fk_billing_address_id: bid,
            })
            .collect();
        bulk.insert(
            "payment_data",
            &["token", "fk_billing_address_id"],
            &pay_rows,
        )
        .await?;
        let pay_ids = fetch_ids(&client, "payment_data").await?;

        // B3. Subscriptions
        let sub_rows: Vec<DbSubscription> = pay_ids
            .iter()
            .map(|&pid| DbSubscription {
                expiration_date: chrono::Utc::now().naive_utc() + chrono::Duration::days(365),
                last_renewal: None,
                created_at: chrono::Utc::now().naive_utc(),
                uploaded_at: chrono::Utc::now().naive_utc(),
                is_active: true,
                auto_renewal: true,
                fk_subscription_plan_id: plan_ids[rng.gen_range(0..plan_ids.len())],
                fk_payment_data_id: Some(pid),
            })
            .collect();
        bulk.insert(
            "subscription",
            &[
                "expiration_date",
                "last_renewal",
                "created_at",
                "uploaded_at",
                "is_active",
                "auto_renewal",
                "fk_subscription_plan_id",
                "fk_payment_data_id",
            ],
            &sub_rows,
        )
        .await?;
    }
    let available_sub_ids = fetch_ids(&client, "subscription").await?;

    // =========================================================================
    // 3. ADMINS
    // =========================================================================
    println!(">>> Generating Admins...");
    // 3a. Generate Admin Accounts (User Table)
    let admin_users = generators::users::generate_user_batch(config.admins_number);

    let stmt = client
        .prepare(
            "
        INSERT INTO \"user\" (username, email, password_hash, created_at)
        SELECT * FROM UNNEST($1::text[], $2::text[], $3::text[], $4::timestamp[])
        RETURNING id
    ",
        )
        .await?;

    let usernames: Vec<&str> = admin_users.iter().map(|u| u.username.as_str()).collect();
    let emails: Vec<&str> = admin_users.iter().map(|u| u.email.as_str()).collect();
    let hashes: Vec<&str> = admin_users
        .iter()
        .map(|u| u.password_hash.as_str())
        .collect();
    let dates: Vec<chrono::NaiveDateTime> = admin_users.iter().map(|u| u.created_at).collect();

    let admin_rows = client
        .query(&stmt, &[&usernames, &emails, &hashes, &dates])
        .await?;
    let admin_user_ids: Vec<i32> = admin_rows.iter().map(|r| r.get(0)).collect();

    // 3b. Insert Admin Details
    let admin_details = generators::social::generate_admins(&admin_user_ids);
    bulk.insert(
        "administrator",
        &["fk_user_id", "hiring_date", "reports_handled"],
        &admin_details,
    )
    .await?;

    // =========================================================================
    // 4. REGULAR USERS (Batched Loop)
    // =========================================================================
    let batch_size = 500;
    let total_batches = (config.users_number + batch_size - 1) / batch_size;
    let pb = ProgressBar::new(config.users_number as u64);

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

        all_user_ids.extend_from_slice(&user_ids);

        // C. Generate Details (CPU)
        let cfg_clone = config.clone();
        let uids_clone = user_ids.clone();
        let sub_ids_clone = available_sub_ids.clone();
        let pref_ids_clone = available_pref_ids.clone();

        let details_batch = tokio::task::spawn_blocking(move || {
            generators::users::generate_details_batch(
                uids_clone,
                &cfg_clone,
                &sub_ids_clone,
                &pref_ids_clone,
            )
        })
        .await?;

        // D. Insert Details (IO)
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

    // Fetch all User Detail IDs (Needed for everything that follows)
    let user_detail_ids = fetch_ids(&client, "user_details").await?;

    // =========================================================================
    // 5. POST-REQUISITES (Interests)
    // =========================================================================
    println!(">>> Linking User Interests...");
    let ud_ids_clone = user_detail_ids.clone();
    let int_ids_clone = interest_ids.clone();

    let user_interests = tokio::task::spawn_blocking(move || {
        generators::content::generate_user_interests(&ud_ids_clone, &int_ids_clone)
    })
    .await?;

    bulk.insert(
        "user_interest",
        &[
            "level_of_interest",
            "is_positive",
            "fk_user_details_id",
            "fk_interest_id",
        ],
        &user_interests,
    )
    .await?;

    // =========================================================================
    // 6. INTERACTIONS (Swipes & Matches)
    // =========================================================================
    println!(">>> Generating Interactions (Swipes & Matches)...");

    let cfg_clone = config.clone();
    let ud_ids_clone = user_detail_ids.clone();

    let interactions = tokio::task::spawn_blocking(move || {
        generators::interactions::generate_interactions(&ud_ids_clone, &cfg_clone)
    })
    .await?;

    println!(">>> Inserting {} Swipes...", interactions.swipes.len());
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
    bulk.insert(
        "match",
        &["fk_person1_id", "fk_person2_id", "date_formed", "status"],
        &interactions.matches,
    )
    .await?;

    // =========================================================================
    // 7. MESSAGING
    // =========================================================================
    println!(">>> Generating Messages...");

    // We need Match IDs to link conversations
    let match_rows = client
        .query(
            "SELECT id, fk_person1_id, fk_person2_id FROM \"match\"",
            &[],
        )
        .await?;
    let match_data: Vec<(i32, i32, i32)> = match_rows
        .iter()
        .map(|r| (r.get(0), r.get(1), r.get(2)))
        .collect();

    // Store match pairs for block logic later
    let match_pairs: Vec<(i32, i32)> = match_rows.iter().map(|r| (r.get(1), r.get(2))).collect();

    if !match_data.is_empty() {
        let cfg_clone = config.clone();

        // 7a. Generate Conversations
        let (conversations, _) = generators::social::generate_chat_flow(&match_data, &cfg_clone);
        bulk.insert(
            "conversation",
            &[
                "fk_match_id",
                "chat_theme",
                "chat_reaction",
                "created_at",
                "updated_at",
            ],
            &conversations,
        )
        .await?;

        // 7b. Generate Messages
        let convo_rows = client
            .query(
                "SELECT c.id, m.fk_person1_id, m.fk_person2_id 
                 FROM conversation c 
                 JOIN \"match\" m ON c.fk_match_id = m.id",
                &[],
            )
            .await?;

        let convo_data: Vec<(i32, i32, i32)> = convo_rows
            .iter()
            .map(|r| (r.get(0), r.get(1), r.get(2)))
            .collect();

        let messages = generators::social::generate_messages_for_convos(&convo_data, &config);
        bulk.insert(
            "message",
            &[
                "send_time",
                "contents",
                "reaction",
                "fk_sender_id",
                "fk_conversation_id",
                "fk_replying_to_message_id",
            ],
            &messages,
        )
        .await?;
    }

    // =========================================================================
    // 8. MEDIA (Images)
    // =========================================================================
    println!(">>> Generating Images...");
    let images = tokio::task::spawn_blocking({
        let uids = user_detail_ids.clone();
        let cfg = config.clone();
        move || generators::content::generate_images(&uids, &cfg)
    })
    .await?;

    bulk.insert(
        "image",
        &[
            "file_path",
            "uploaded_at",
            "is_current",
            "file_size_bytes",
            "is_verified",
            "fk_user_details_id",
        ],
        &images,
    )
    .await?;

    // =========================================================================
    // 9. SEARCH PREFERENCE DETAILS
    // =========================================================================
    println!(">>> Linking Search Preferences (Sex & Interests)...");
    // We need to fetch the preference IDs we generated way back in step 2A
    let pref_ids = fetch_ids(&client, "search_preference").await?;

    // We use the sex_ids and interest_ids cached at start of main
    let sp_sex = generators::content::generate_search_pref_sex(&pref_ids, &sex_ids);
    bulk.insert(
        "search_preference_sex",
        &["fk_search_preference_id", "fk_sex_id", "priorty"],
        &sp_sex,
    )
    .await?;

    let sp_int = generators::content::generate_search_pref_interests(&pref_ids, &interest_ids);
    bulk.insert(
        "search_preference_interest",
        &[
            "fk_search_preference_id",
            "fk_interest_id",
            "level_of_interest",
            "is_positive",
        ],
        &sp_int,
    )
    .await?;

    // =========================================================================
    // 10. SOCIAL SAFETY (Reports, Bans, Blocks)
    // =========================================================================
    println!(">>> Generating Safety Data (Reports, Bans, Blocks)...");

    // A. Reports
    let admin_rows = client
        .query("SELECT fk_user_id FROM administrator", &[])
        .await?;
    let admin_ids: Vec<i32> = admin_rows.iter().map(|r| r.get(0)).collect();

    let reports = generators::social::generate_reports(&user_detail_ids, &admin_ids, &config);
    bulk.insert(
        "report",
        &[
            "reason",
            "report_date",
            "fk_reporting_user_details_id",
            "fk_reported_user_details_id",
            "fk_administrator_id",
        ],
        &reports,
    )
    .await?;

    // B. Bans
    // Must fetch reports to link bans
    let report_rows = client
        .query(
            "SELECT id, fk_reported_user_details_id, report_date FROM report",
            &[],
        )
        .await?;
    let report_meta: Vec<generators::social::ReportMeta> = report_rows
        .iter()
        .map(|r| generators::social::ReportMeta {
            id: r.get(0),
            reported_user_id: r.get(1),
            report_date: r.get(2),
        })
        .collect();

    let bans = generators::social::generate_bans(&report_meta, &config);
    bulk.insert(
        "ban",
        &[
            "fk_user_details_id",
            "fk_report_id",
            "start_date",
            "period_days",
            "is_active",
        ],
        &bans,
    )
    .await?;

    // C. Blocks
    let blocks = generators::social::generate_blocks(&user_detail_ids, &match_pairs, &config);
    bulk.insert(
        "block",
        &[
            "fk_blocking_user_details_id",
            "fk_blocked_user_details_id",
            "start_date",
            "end_date",
            "is_active",
        ],
        &blocks,
    )
    .await?;

    println!(">>> Population Complete.");
    Ok(())
}
