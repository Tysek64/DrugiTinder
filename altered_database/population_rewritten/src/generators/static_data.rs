use crate::db::bulk::BulkInserter;
use anyhow::{Context, Result};
use serde::Deserialize;
use std::collections::HashMap;
use tokio_postgres::Client;

// --- CSV Record Structures ---
// These match the CSV headers provided in your context
#[derive(Debug, Deserialize)]
struct CsvCountry {
    name: String,
    iso_code: String,
    population: Option<i64>,
    #[serde(rename = "locale")]
    _locale: Option<String>, // Parsed but unused in DB schema directly
}

#[derive(Debug, Deserialize)]
struct CsvSex {
    name: String,
    // We ignore frequencyIGuess and nazoNumbers for the DB insert
}

#[derive(Debug, Deserialize)]
struct CsvPlan {
    name: String,
    price: f64,
    payment_cycle: String,
    benefits: String,
    // 'users' column is used for weighted generation logic, not DB storage
}

#[derive(Debug, Deserialize)]
struct CsvInterest {
    name: String,
}

// --- DB Row Structures (for Bulk Copy) ---
#[derive(Debug, serde::Serialize)]
struct DbSex {
    name: String,
}

#[derive(Debug, serde::Serialize)]
struct DbInterest {
    name: String,
}

#[derive(Debug, serde::Serialize)]
struct DbCity {
    name: String,
    fk_country_id: i32,
}

#[derive(Debug, serde::Serialize)]
struct DbPlan {
    name: String,
    price: f64,
    payment_cycle: String,
    benefits: String,
    is_active: bool,
}

/// Orchestrates the loading of all static catalog data
pub async fn populate_static_data(client: &Client) -> Result<()> {
    println!("--- Populating Static Data ---");

    populate_sexes(client)
        .await
        .context("Failed to populate sexes")?;
    populate_plans(client)
        .await
        .context("Failed to populate plans")?;
    populate_interests(client)
        .await
        .context("Failed to populate interests")?;

    // Country + City must be sequential: We need Country IDs to create Cities
    populate_countries_and_cities(client)
        .await
        .context("Failed to populate countries/cities")?;

    println!("--- Static Data Complete ---");
    Ok(())
}

async fn populate_sexes(client: &Client) -> Result<()> {
    // 1. Parse CSV
    let mut rdr =
        csv::Reader::from_path("sexes.csv").context("Could not find sexes.csv in run directory")?;

    let mut rows = Vec::new();
    for result in rdr.deserialize() {
        let record: CsvSex = result?;
        rows.push(DbSex { name: record.name });
    }

    // 2. Bulk Insert
    let bulk = BulkInserter::new(client);
    bulk.insert("sex", &["name"], &rows).await?;
    println!("> Inserted {} sexes", rows.len());
    Ok(())
}

async fn populate_interests(client: &Client) -> Result<()> {
    let mut rdr =
        csv::Reader::from_path("interests.csv").context("Could not find interests.csv")?;

    let mut rows = Vec::new();
    for result in rdr.deserialize() {
        let record: CsvInterest = result?;
        rows.push(DbInterest { name: record.name });
    }

    let bulk = BulkInserter::new(client);
    bulk.insert("interest", &["name"], &rows).await?;
    println!("> Inserted {} interests", rows.len());
    Ok(())
}

async fn populate_plans(client: &Client) -> Result<()> {
    let mut rdr = csv::Reader::from_path("plans.csv").context("Could not find plans.csv")?;

    let mut rows = Vec::new();
    for result in rdr.deserialize() {
        let record: CsvPlan = result?;
        rows.push(DbPlan {
            name: record.name,
            price: record.price,
            payment_cycle: record.payment_cycle,
            benefits: record.benefits,
            is_active: true, // Default to true as per schema logic
        });
    }

    let bulk = BulkInserter::new(client);
    bulk.insert(
        "subscription_plan",
        &["name", "price", "payment_cycle", "benefits", "is_active"],
        &rows,
    )
    .await?;
    println!("> Inserted {} subscription plans", rows.len());
    Ok(())
}

async fn populate_countries_and_cities(client: &Client) -> Result<()> {
    let mut rdr = csv::ReaderBuilder::new()
        .flexible(true) // <--- THIS ALLOWS MISSING OPTIONAL COLUMNS
        .trim(csv::Trim::All) // Good practice to trim whitespace
        .from_path("parsedCountries.csv")
        .context("Could not find parsedCountries.csv")?;

    // Step 1: Insert Countries individually to capture IDs (needed for FK)
    let stmt = client
        .prepare(
            "
        INSERT INTO country (name, iso_code) 
        VALUES ($1, $2) 
        ON CONFLICT (iso_code) DO NOTHING 
        RETURNING id, name
    ",
        )
        .await?;

    let mut country_map: HashMap<String, i32> = HashMap::new();
    let mut count = 0;

    for result in rdr.deserialize() {
        // We map the error to avoid crashing the whole batch on one bad line,
        // though typically we want to fail fast if data is corrupt.
        let record: CsvCountry = result.context("Failed to parse country record")?;

        let row = client
            .query_opt(&stmt, &[&record.name, &record.iso_code])
            .await?;

        if let Some(row) = row {
            let id: i32 = row.get(0);
            country_map.insert(record.name, id);
            count += 1;
        }
    }
    println!("> Inserted {} countries", count);

    // Step 2: Generate Synthetic Cities (Since cities.csv is missing)
    // Constraint: We generate 2 cities per country to ensure we have enough IDs
    // for the user generation logic (which selects random IDs).
    let mut cities = Vec::new();
    for (country_name, country_id) in country_map {
        cities.push(DbCity {
            name: format!("Capital of {}", country_name),
            fk_country_id: country_id,
        });
        cities.push(DbCity {
            name: format!("Port {}", country_name),
            fk_country_id: country_id,
        });
    }

    // Step 3: Bulk Insert Cities
    let bulk = BulkInserter::new(client);
    bulk.insert("city", &["name", "fk_country_id"], &cities)
        .await?;
    println!("> Inserted {} synthetic cities", cities.len());

    Ok(())
}
