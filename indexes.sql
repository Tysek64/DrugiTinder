CREATE INDEX message_conversation_time ON message(fk_conversation_id, send_time);

CREATE INDEX match_fk_person1 ON "match" (fk_person1_id);

CREATE INDEX idx_sps_search_preference_id on search_preference_sex (fk_search_preference_id);

CREATE INDEX idx_fk_both_users on swipe (fk_swiping_user_details_id, fk_swiped_user_details_id);

CREATE INDEX idx_fk_swiped_user_id on swipe (fk_swiped_user_details_id);

CREATE INDEX idx_ui_fk_interest_id ON user_interest(fk_interest_id);

CREATE INDEX idx_ui_fk_user_details_id ON user_interest(fk_user_details_id);

CREATE INDEX idx_ui_covering ON user_interest(fk_user_details_id, fk_interest_id, level_of_interest, is_positive);

CREATE INDEX idx_message_sent_time ON message(sent_time);

CREATE INDEX idx_image_user_current ON image(fk_user_details_id, is_current);