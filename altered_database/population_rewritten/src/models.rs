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
