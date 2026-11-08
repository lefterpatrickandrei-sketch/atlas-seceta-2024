"""Teste pentru crearea clientului WEkEO din .env: token din portal sau utilizator + parolă. Fără rețea."""
import pytest

import gisday_lib as gl


def test_token_is_used_directly_without_asking_the_server():
    client = gl.wekeo_client({'WEKEO_TOKEN': 'abc'})
    assert client.token == 'abc'


def test_token_wins_when_user_and_password_are_also_present():
    client = gl.wekeo_client({'WEKEO_TOKEN': 'abc', 'WEKEO_USER': 'u', 'WEKEO_PASSWORD': 'p'})
    assert client.token == 'abc'


def test_user_and_password_are_passed_to_the_client():
    client = gl.wekeo_client({'WEKEO_USER': 'u', 'WEKEO_PASSWORD': 'p'})
    assert (client.config.user, client.config.password) == ('u', 'p')


def test_missing_credentials_stop_with_a_clear_message():
    with pytest.raises(ValueError, match='WEKEO_TOKEN'):
        gl.wekeo_client({})


def test_download_is_complete_only_when_size_matches_the_catalog(tmp_path):
    product = tmp_path / 'VPP_2023.tif'
    product.write_bytes(b'x' * 10)
    assert gl.is_complete(tmp_path, 'VPP_2023', 10)
    assert not gl.is_complete(tmp_path, 'VPP_2023', 20)


def test_download_is_incomplete_when_the_file_is_missing(tmp_path):
    assert not gl.is_complete(tmp_path, 'VPP_2024', 10)
