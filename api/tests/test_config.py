from app.config import Settings


def test_settings_loads_with_defaults_for_new_audio_fields():
    settings = Settings(_env_file=None)

    assert settings.google_tts_credentials_json == ""
    assert settings.r2_account_id == ""
    assert settings.r2_access_key_id == ""
    assert settings.r2_secret_access_key == ""
    assert settings.r2_bucket_name == ""
    assert settings.r2_public_url_base == ""
