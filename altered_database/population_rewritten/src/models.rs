use chrono::NaiveDateTime;
use serde::{Deserialize, Serialize};

// --- CSV Mappings ---
#[derive(Debug, Deserialize)]
pub struct CountryRecord {
    pub name: String,
    pub iso_code: String,
    pub population: Option<i64>,
    pub locale: Option<String>,
}

#[derive(Debug, Deserialize)]
pub struct PlanRecord {
    pub name: String,
    pub price: f64,
    pub payment_cycle: String,
    pub benefits: String,
    pub users: i32,
}

#[derive(Debug, Deserialize)]
pub struct SexRecord {
    pub name: String,
}

#[derive(Debug, Deserialize)]
pub struct InterestRecord {
    pub name: String,
}

// --- Runtime Structs ---

#[derive(Debug, Clone, Serialize)]
pub struct DbUser {
    pub id: Option<i32>,
    pub username: String,
    pub email: String,
    pub password_hash: String,
    pub created_at: NaiveDateTime,
}

#[derive(Debug, Clone, Serialize)]
pub struct DbUserDetails {
    pub name: String,
    pub surname: String,
    pub fk_sex_id: i32,
    pub fk_city_id: Option<i32>,
    pub fk_subscription_id: Option<i32>,
    pub fk_search_preference_id: Option<i32>,
    pub fk_user_id: i32,
    pub created_at: NaiveDateTime,
}

// --- Interaction Structs (New) ---

#[derive(Debug, Serialize)]
pub struct DbSwipe {
    pub result: bool,
    pub fk_swiping_user_details_id: i32,
    pub fk_swiped_user_details_id: i32,
    pub swipe_time: NaiveDateTime,
}

#[derive(Debug, Serialize)]
pub struct DbMatch {
    pub fk_person1_id: i32,
    pub fk_person2_id: i32,
    pub date_formed: NaiveDateTime,
    pub status: String,
}
//
// ... (Keep existing structs: CountryRecord, PlanRecord, DbUser, DbUserDetails, DbSwipe, DbMatch) ...

// --- 1. Admin & Auth ---
#[derive(Debug, Serialize)]
pub struct DbAdministrator {
    pub fk_user_id: i32,
    pub hiring_date: NaiveDateTime,
    pub reports_handled: i32,
}

// --- 2. Subscriptions ---
#[derive(Debug, Serialize)]
pub struct DbBillingAddress {
    pub street: String,
    pub postal_code: String,
    pub fk_city_id: i32,
}

#[derive(Debug, Serialize)]
pub struct DbPaymentData {
    pub token: String,
    pub fk_billing_address_id: i32,
}

#[derive(Debug, Serialize)]
pub struct DbSubscription {
    pub expiration_date: NaiveDateTime,
    pub last_renewal: Option<NaiveDateTime>,
    pub created_at: NaiveDateTime,
    pub uploaded_at: NaiveDateTime,
    pub is_active: bool,
    pub auto_renewal: bool,
    pub fk_subscription_plan_id: i32,
    pub fk_payment_data_id: Option<i32>,
}

// --- 3. Preferences & Interests ---
#[derive(Debug, Serialize)]
pub struct DbSearchPreference {
    pub search_description: String,
    pub created_at: NaiveDateTime,
    pub updated_at: NaiveDateTime,
}

#[derive(Debug, Serialize)]
pub struct DbSearchPreferenceSex {
    pub fk_search_preference_id: i32,
    pub fk_sex_id: i32,
    pub priorty: i32,
}

#[derive(Debug, Serialize)]
pub struct DbSearchPreferenceInterest {
    pub fk_search_preference_id: i32,
    pub fk_interest_id: i32,
    pub level_of_interest: i32,
    pub is_positive: bool,
}

#[derive(Debug, Serialize)]
pub struct DbUserInterest {
    pub level_of_interest: i32,
    pub is_positive: bool,
    pub fk_user_details_id: i32,
    pub fk_interest_id: i32,
}

// --- 4. Messaging ---
#[derive(Debug, Serialize)]
pub struct DbConversation {
    pub fk_match_id: i32,
    pub chat_theme: String,
    pub chat_reaction: i16,
    pub created_at: NaiveDateTime,
    pub updated_at: NaiveDateTime,
}

#[derive(Debug, Serialize)]
pub struct DbMessage {
    pub send_time: NaiveDateTime,
    pub contents: String,
    pub reaction: Option<i16>,
    pub fk_sender_id: Option<i32>,
    pub fk_conversation_id: i32,
    pub fk_replying_to_message_id: Option<i32>,
}

// --- 5. Social Safety ---
#[derive(Debug, Serialize)]
pub struct DbReport {
    pub reason: String,
    pub report_date: NaiveDateTime,
    pub fk_reporting_user_details_id: i32,
    pub fk_reported_user_details_id: i32,
    pub fk_administrator_id: Option<i32>,
}

#[derive(Debug, Serialize)]
pub struct DbBan {
    pub fk_user_details_id: i32,
    pub fk_report_id: i32,
    pub start_date: NaiveDateTime,
    pub period_days: i32,
    pub is_active: bool,
}

#[derive(Debug, Serialize)]
pub struct DbBlock {
    pub fk_blocking_user_details_id: i32,
    pub fk_blocked_user_details_id: i32,
    pub start_date: NaiveDateTime,
    pub end_date: Option<NaiveDateTime>,
    pub is_active: bool,
}
