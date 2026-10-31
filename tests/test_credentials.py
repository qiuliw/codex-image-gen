import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('wrapper', Path(__file__).resolve().parents[1] / 'scripts/codex_image_gen.py')
wrapper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(wrapper)


class CredentialsTest(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        for name, value in [('AUTH_PATH', self.root/'auth.json'), ('CONFIG_PATH', self.root/'config.toml')]:
            patcher = patch.object(wrapper, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        patcher = patch.dict(os.environ, {}, clear=True)
        patcher.start()
        self.addCleanup(patcher.stop)
        wrapper.CONFIG_PATH.write_text("model_provider = 'selected'\n[model_providers.other]\nexperimental_bearer_token='wrong'\n[model_providers.selected]\nexperimental_bearer_token='provider-test'\n")

    def test_missing_auth(self):
        self.assertEqual(wrapper.read_api_key(), 'provider-test')

    def test_missing_empty_null_and_whitespace_auth_key(self):
        for value in [{}, {'OPENAI_API_KEY': ''}, {'OPENAI_API_KEY': None}, {'OPENAI_API_KEY': '  '}]:
            with self.subTest(value=value):
                wrapper.AUTH_PATH.write_text(json.dumps(value))
                self.assertEqual(wrapper.read_api_key(), 'provider-test')

    def test_precedence(self):
        wrapper.AUTH_PATH.write_text('{"OPENAI_API_KEY":"auth-test"}')
        self.assertEqual(wrapper.read_api_key(), 'auth-test')
        os.environ['OPENAI_API_KEY'] = 'env-test'
        self.assertEqual(wrapper.read_api_key(), 'env-test')
        self.assertEqual(wrapper.read_api_key('cli-test'), 'cli-test')

    def test_does_not_use_other_provider(self):
        wrapper.CONFIG_PATH.write_text("model_provider='missing'\n[model_providers.other]\nexperimental_bearer_token='wrong'\n")
        with self.assertRaisesRegex(SystemExit, 'Missing OPENAI_API_KEY'):
            wrapper.read_api_key()

    def test_no_files(self):
        wrapper.CONFIG_PATH.unlink()
        with self.assertRaisesRegex(SystemExit, 'Missing OPENAI_API_KEY'):
            wrapper.read_api_key()

    def test_malformed_auth_is_error(self):
        wrapper.AUTH_PATH.write_text('{')
        with self.assertRaisesRegex(SystemExit, 'Could not parse'):
            wrapper.read_api_key()

    def test_malformed_config_does_not_expose_secret(self):
        wrapper.CONFIG_PATH.write_text('experimental_bearer_token = secret-test')
        with self.assertRaises(SystemExit) as error:
            wrapper.read_api_key()
        self.assertNotIn('secret-test', str(error.exception))


if __name__ == '__main__':
    unittest.main()
