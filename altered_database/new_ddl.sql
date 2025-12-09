-- =============================================================
-- DEMOGRAPHIC DATA
-- =============================================================
CREATE TABLE sex (
    id   INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    name VARCHAR(64) NOT NULL UNIQUE
);

CREATE TABLE country (
    id       INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    iso_code CHAR(3)     NOT NULL UNIQUE,
    name     VARCHAR(64) NOT NULL
);

CREATE TABLE city (
    id            INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    name          VARCHAR(128) NOT NULL,
    fk_country_id INT          NOT NULL,
    FOREIGN KEY (fk_country_id) REFERENCES country (id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);

-- =============================================================
-- user & ADMIN
-- =============================================================
CREATE TABLE "user" (
    id            INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    username      VARCHAR(64)  NOT NULL UNIQUE,
    email         VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at    TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    CHECK (position('@' IN email) > 1)
);

CREATE TABLE administrator (
    id              INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    fk_user_id   INTEGER NOT NULL UNIQUE,
    hiring_date     DATE NOT NULL,
    reports_handled INTEGER DEFAULT 0 CHECK (reports_handled >= 0),
    FOREIGN KEY (fk_user_id) REFERENCES "user" (id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CHECK (hiring_date <= CURRENT_DATE)
);

-- =============================================================
-- SUBSCRIPTIONS AND PAYMENTS
-- =============================================================
CREATE TABLE subscription_plan (
    id            INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    name          VARCHAR(100)   NOT NULL,
    price         DECIMAL(10, 2) NOT NULL CHECK (price > 0),
    payment_cycle VARCHAR(50)    NOT NULL CHECK (payment_cycle IN ('Yearly', 'Monthly', 'OneTime')),
    max_users     INTEGER        DEFAULT 1 CHECK (max_users > 0),
    benefits      TEXT,
    is_active     BOOLEAN DEFAULT TRUE
);

CREATE TABLE billing_address (
    id          INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    street      VARCHAR(128) NOT NULL,
    postal_code VARCHAR(10)  NOT NULL,
    fk_city_id  INTEGER      NOT NULL,
    FOREIGN KEY (fk_city_id) REFERENCES city (id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE
);

CREATE TABLE payment_data (
    id                    INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    token                 VARCHAR(255) NOT NULL,
    fk_billing_address_id INT,
    FOREIGN KEY (fk_billing_address_id) REFERENCES billing_address (id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE
);

CREATE TABLE subscription (
    id                      INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    expiration_date         DATE NOT NULL,
    created_at              TIMESTAMP DEFAULT now(),
    updated_at              TIMESTAMP DEFAULT now(),
    is_active               BOOLEAN DEFAULT TRUE,
    auto_renewal            BOOLEAN DEFAULT FALSE,
    fk_subscription_plan_id INT  NOT NULL,
    fk_payment_data_id      INT,
    fk_owner_id             INT  NOT NULL,
    FOREIGN KEY (fk_subscription_plan_id) REFERENCES subscription_plan (id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,
    FOREIGN KEY (fk_payment_data_id) REFERENCES payment_data (id)
        ON DELETE SET NULL
        ON UPDATE CASCADE,
    FOREIGN KEY (fk_owner_id) REFERENCES user (id)
        ON DELETE SET NULL
        ON UPDATE CASCADE,
    CHECK (updated_at IS NULL OR expiration_date >= updated_at)
);

-- =============================================================
-- SEARCH PREFERENCES
-- =============================================================
CREATE TABLE search_preference (
    id                 INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    search_description TEXT,
    -- HERE
    created_at         TIMESTAMP DEFAULT now(),
    updated_at        TIMESTAMP DEFAULT now()
);

CREATE TABLE search_preference_sex (
    id                      INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    fk_search_preference_id INT NOT NULL,
    fk_sex_id               INT NOT NULL,
    priority                 INT,
    FOREIGN KEY (fk_search_preference_id) REFERENCES search_preference (id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    FOREIGN KEY (fk_sex_id) REFERENCES sex (id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);

CREATE TABLE interest (
    id   INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    name VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE search_preference_interest (
    id                      INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    fk_search_preference_id INT NOT NULL,
    fk_interest_id          INT NOT NULL,
    level_of_interest       INT,
    is_positive             BOOLEAN,
    UNIQUE (fk_search_preference_id, fk_interest_id),
    FOREIGN KEY (fk_search_preference_id) REFERENCES search_preference (id)
        ON DELETE CASCADE,
    FOREIGN KEY (fk_interest_id) REFERENCES interest (id)
        ON DELETE CASCADE
);

-- =============================================================
-- USER PROFILE
-- =============================================================
CREATE TABLE user_details (
    id                      INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    name                    VARCHAR(50) NOT NULL,
    surname                 VARCHAR(50) NOT NULL,
    fk_sex_id               INT DEFAULT 1,
    fk_city_id              INT,
    fk_subscription_id      INT,
    fk_search_preference_id INT,
    fk_user_id              INT UNIQUE,
    created_at              TIMESTAMP DEFAULT now(),
    updated_at              TIMESTAMP DEFAULT now(),
    FOREIGN KEY (fk_sex_id) REFERENCES sex (id)
        ON DELETE SET DEFAULT
        ON UPDATE SET DEFAULT,
    FOREIGN KEY (fk_city_id) REFERENCES city (id)
        ON DELETE SET NULL
        ON UPDATE SET NULL,
    FOREIGN KEY (fk_subscription_id) REFERENCES subscription (id)
        ON DELETE SET NULL
        ON UPDATE SET NULL,
    FOREIGN KEY (fk_search_preference_id) REFERENCES search_preference (id)
        ON DELETE SET NULL
        ON UPDATE SET NULL,
    FOREIGN KEY (fk_user_id) REFERENCES "user" (id)
        ON DELETE SET NULL
        ON UPDATE SET NULL
);

-- DODANIE KLUCZA OBCEGO TERA BO WCZEŚNIEJ TABELA USER_DETAILS NIE ISTNIALA

ALTER TABLE subscription
ADD CONSTRAINT fk_subscription_owner
FOREIGN KEY (fk_owner_id) REFERENCES user_details (id)
ON DELETE CASCADE
ON UPDATE CASCADE;


CREATE TABLE image (
    id              INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    file_path       TEXT NOT NULL,
    uploaded_at     TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    is_current      BOOLEAN DEFAULT FALSE,
    file_size_bytes BIGINT CHECK (file_size_bytes >= 0),
    is_verified     BOOLEAN DEFAULT FALSE,
    fk_user_details_id      INT NOT NULL,
    FOREIGN KEY (fk_user_details_id) REFERENCES user_details (id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);

CREATE TABLE user_interest (
    id                INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    level_of_interest INT CHECK (level_of_interest BETWEEN 1 AND 10),
    is_positive       BOOLEAN DEFAULT TRUE,
    fk_user_details_id        INT NOT NULL,
    fk_interest_id    INT NOT NULL,
    UNIQUE (fk_user_details_id, fk_interest_id),
    FOREIGN KEY (fk_user_details_id) REFERENCES user_details (id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    FOREIGN KEY (fk_interest_id) REFERENCES interest (id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);

-- =============================================================
-- MATCHES, SWIPES, BLOCKS
-- =============================================================
CREATE TABLE swipe (
    id                 INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    result             BOOLEAN,
    fk_swiping_user_details_id INT NOT NULL,
    fk_swiped_user_details_id  INT NOT NULL,
    -- HERE
    swipe_time         TIMESTAMP DEFAULT now(),
    FOREIGN KEY (fk_swiping_user_details_id) REFERENCES user_details (id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    FOREIGN KEY (fk_swiped_user_details_id) REFERENCES user_details (id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CHECK (fk_swiping_user_details_id <> fk_swiped_user_details_id)
);
-- HERE
CREATE TABLE "match" (
    id              INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    fk_person1_id   INT NOT NULL,
    fk_person2_id   INT NOT NULL,
    date_formed     TIMESTAMP DEFAULT now(),
    date_ended      TIMESTAMP,
    fk_ender_id     INT,
    status          VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'ended')),
    FOREIGN KEY (fk_person1_id) REFERENCES user_details (id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    FOREIGN KEY (fk_person2_id) REFERENCES user_details (id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    FOREIGN KEY (fk_ender_id) REFERENCES user_details (id)
        ON DELETE SET NULL
        ON UPDATE CASCADE,
    CHECK (fk_person1_id <> fk_person2_id),
    CHECK (fk_ender_id IS NULL OR fk_ender_id IN (fk_person1_id, fk_person2_id))
);

CREATE UNIQUE INDEX ux_match_pair ON "match" (LEAST(fk_person1_id, fk_person2_id),
                                              GREATEST(fk_person1_id, fk_person2_id));

CREATE TABLE block (
    id                          INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    fk_blocking_user_details_id INT NOT NULL,
    fk_blocked_user_details_id  INT NOT NULL,
    start_date          TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    end_date            TIMESTAMP,
    is_active           BOOLEAN DEFAULT TRUE,
    UNIQUE (fk_blocking_user_details_id, fk_blocked_user_details_id),
    FOREIGN KEY (fk_blocking_user_details_id) REFERENCES user_details (id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    FOREIGN KEY (fk_blocked_user_details_id) REFERENCES user_details (id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CHECK (fk_blocking_user_details_id <> fk_blocked_user_details_id)
);

-- =============================================================
-- CONVERSATIONS & MESSAGES
-- =============================================================
CREATE TABLE conversation (
    id            INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    fk_match_id   INT UNIQUE,
    chat_theme    VARCHAR(255),
    chat_reaction SMALLINT CHECK (chat_reaction BETWEEN -1 AND 5),
    created_at    TIMESTAMP DEFAULT now(),
    updated_at    TIMESTAMP DEFAULT now(),
    FOREIGN KEY (fk_match_id) REFERENCES "match" (id)
        ON DELETE SET NULL
        ON UPDATE CASCADE
);

CREATE TABLE message (
    id                        INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    send_time                 TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    contents                  TEXT NOT NULL,
    reaction                  SMALLINT DEFAULT NULL CHECK (reaction BETWEEN 0 AND 5),
    fk_sender_id              INT,
    fk_conversation_id        INT NOT NULL,
    fk_replying_to_message_id INT,
    FOREIGN KEY (fk_conversation_id) REFERENCES conversation (id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    FOREIGN KEY (fk_sender_id) REFERENCES user_details (id)
        ON DELETE SET NULL
        ON UPDATE CASCADE,
    FOREIGN KEY (fk_replying_to_message_id) REFERENCES message (id)
        ON DELETE SET NULL
        ON UPDATE CASCADE
);

-- =============================================================
-- REPORTS AND BANS
-- =============================================================
CREATE TABLE "report" (
    id                   INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    reason               TEXT,
    report_date          TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    fk_reporting_user_details_id INT NOT NULL,
    fk_reported_user_details_id  INT NOT NULL,
    fk_administrator_id  INT,
    FOREIGN KEY (fk_reporting_user_details_id) REFERENCES user_details (id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    FOREIGN KEY (fk_reported_user_details_id) REFERENCES user_details (id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    FOREIGN KEY (fk_administrator_id) REFERENCES administrator (id)
        ON DELETE SET NULL
        ON UPDATE CASCADE,
    CHECK (fk_reporting_user_details_id <> fk_reported_user_details_id)
);

CREATE TABLE ban (
    id           INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    fk_user_details_id   INT NOT NULL,
    fk_report_id INT NOT NULL,
    start_date   TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    period_days  INT NOT NULL CHECK (period_days >= 1),
    is_active    BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (fk_report_id) REFERENCES "report" (id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    FOREIGN KEY (fk_user_details_id) REFERENCES user_details (id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);
